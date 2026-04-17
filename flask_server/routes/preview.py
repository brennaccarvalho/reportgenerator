"""
Rotas de preview (/preview) e publicação (/publish).

Fluxo do preview:
  1. Carrega dataset do disco
  2. Filtra colunas selecionadas no builder
  3. Executa run_framework() → dict de seções {chave: {title, text, data, chart_config}}
  4. Para cada seção, build_chart() gera figura Plotly
  5. pio.to_html() converte a figura em HTML embutível
  6. generate_insights() gera lista de insights automáticos
  7. Renderiza template preview.html

Fluxo do publish:
  1. Repete geração do relatório
  2. Cria registro Report no PostgreSQL
  3. Gera HTML estático e salva em data/published_reports/<id>.html
  4. Redireciona para /reports/<id>
"""
import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app,
)
import pandas as pd
import plotly.io as pio

from app.services.framework_selector import run_framework
from app.services.chart_builder import build_chart
from app.services.insight_generator import generate_insights
from flask_server.models import db, Dataset, Report

preview_bp = Blueprint("preview", __name__)

FRAMEWORK_NAMES = {
    "ooda": "OODA Loop",
    "funnel": "Análise de Funil",
    "performance": "Diagnóstico de Performance",
    "eda": "EDA — Exploratória",
    "temporal": "Análise Temporal",
}


def _load_df(dataset: Dataset, selected_cols: list) -> pd.DataFrame:
    """Carrega o DataFrame e aplica filtro de colunas se necessário."""
    df = pd.read_csv(dataset.storage_path)
    if selected_cols:
        valid = [c for c in selected_cols if c in df.columns]
        if valid:
            df = df[valid]
    return df


def _sections_to_html(sections: dict) -> list:
    """
    Converte o dict de seções do framework em lista de dicts com chart HTML.

    Para cada seção:
      - build_chart(data, chart_config) → figura Plotly
      - pio.to_html() → string HTML com o gráfico interativo
    """
    result = []
    first = True
    for key, section in sections.items():
        try:
            fig = build_chart(section["data"], section["chart_config"])
            chart_html = pio.to_html(
                fig,
                # CDN do Plotly só é incluído no primeiro gráfico da página
                include_plotlyjs="cdn" if first else False,
                full_html=False,
                config={"responsive": True, "displayModeBar": False},
            )
            first = False
        except Exception:
            chart_html = (
                "<p class='text-muted fst-italic'>Gráfico não disponível para esta seção.</p>"
            )

        result.append({
            "key": key,
            "title": section.get("title", key),
            "text": section.get("text", ""),
            "chart_html": chart_html,
        })
    return result


# ── Preview ───────────────────────────────────────────────────────

@preview_bp.route("/preview", methods=["GET"])
def preview_page():
    """Gera e exibe o preview interativo do relatório."""
    dataset_id = session.get("dataset_id")
    framework_id = session.get("framework_id")
    report_name = session.get("report_name", "Relatório sem título")
    selected_cols = session.get("selected_cols", [])

    if not dataset_id or not framework_id:
        flash("Sessão expirada. Comece um novo relatório.", "warning")
        return redirect(url_for("main.upload_page"))

    dataset = Dataset.query.get_or_404(dataset_id)

    try:
        df = _load_df(dataset, selected_cols)
    except Exception as e:
        flash(f"Erro ao carregar dataset: {e}", "error")
        return redirect(url_for("main.upload_page"))

    try:
        sections = run_framework(framework_id, df)
        sections_html = _sections_to_html(sections)
        insights = generate_insights(df)
    except Exception as e:
        flash(f"Erro ao gerar relatório: {e}", "error")
        return redirect(
            url_for("builder.builder_page", dataset_id=dataset_id)
        )

    dataset_info = {
        "id": dataset.id,
        "name": dataset.name,
        "n_rows": dataset.n_rows,
        "n_cols": dataset.n_cols,
        "framework": framework_id,
    }

    return render_template(
        "preview.html",
        current_step="preview",
        current_step_num=5,
        dataset_info=dataset_info,
        sections=sections_html,
        insights=insights,
        report_name=report_name,
        framework_name=FRAMEWORK_NAMES.get(framework_id, framework_id),
        dataset=dataset,
    )


# ── Publish ───────────────────────────────────────────────────────

@preview_bp.route("/publish", methods=["POST"])
def publish_report():
    """Salva o relatório no PostgreSQL e gera HTML estático."""
    dataset_id = session.get("dataset_id")
    framework_id = session.get("framework_id")
    selected_cols = session.get("selected_cols", [])
    report_name = (
        request.form.get("report_name", "").strip()
        or session.get("report_name", "Relatório")
    )

    if not dataset_id or not framework_id:
        flash("Sessão expirada. Comece novamente.", "warning")
        return redirect(url_for("main.upload_page"))

    dataset = Dataset.query.get_or_404(dataset_id)

    try:
        df = _load_df(dataset, selected_cols)
        sections = run_framework(framework_id, df)
        sections_html = _sections_to_html(sections)
        insights = generate_insights(df)
    except Exception as e:
        flash(f"Erro ao gerar relatório: {e}", "error")
        return redirect(url_for("preview.preview_page"))

    # Cria registro no PostgreSQL
    report = Report(
        name=report_name,
        framework=framework_id,
        dataset_id=dataset_id,
        source=dataset.source,
        source_name=dataset.source_name,
        n_rows=dataset.n_rows,
        n_cols=dataset.n_cols,
    )
    db.session.add(report)
    db.session.flush()  # gera o ID

    # Gera e salva HTML estático
    html_path = os.path.join(
        current_app.config["PUBLISHED_REPORTS_DIR"], f"{report.id}.html"
    )
    html_content = _build_static_html(
        report_name, framework_id, sections_html, insights, dataset, report.created_at
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    report.path = html_path
    db.session.commit()

    flash(f"Relatório '{report_name}' publicado com sucesso!", "success")
    return redirect(url_for("reports.report_detail", report_id=report.id))


def _build_static_html(name, framework_id, sections, insights, dataset, created_at):
    """Monta o HTML estático completo do relatório para armazenar em disco."""
    fw_name = FRAMEWORK_NAMES.get(framework_id, framework_id)
    severity_colors = {
        "info": "#3b82f6",
        "warning": "#f59e0b",
        "critical": "#ef4444",
    }
    dt_str = (
        created_at.strftime("%d/%m/%Y %H:%M") if created_at else "—"
    )

    sections_html = "".join(
        f"""
        <div class="section">
            <h2>{s['title']}</h2>
            <p class="section-text">{s['text']}</p>
            <div class="chart-wrap">{s['chart_html']}</div>
        </div>"""
        for s in sections
    )

    insights_html = "".join(
        f"""
        <div class="insight" style="border-left:4px solid {severity_colors.get(i.get('severity','info'),'#3b82f6')};">
            <strong>{i.get('title','')}</strong>
            <p>{i.get('description','')}</p>
        </div>"""
        for i in insights
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name}</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    body{{font-family:Inter,sans-serif;max-width:1100px;margin:0 auto;padding:2rem;background:#f9fafb;color:#1f2937}}
    .header{{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:white;padding:2rem;border-radius:1rem;margin-bottom:2rem}}
    .header h1{{margin:0 0 .5rem;font-size:1.75rem}}
    .meta{{opacity:.85;font-size:.875rem}}
    .section{{background:white;border-radius:.75rem;padding:1.5rem;margin-bottom:1.5rem;border:1px solid #e5e7eb}}
    .section h2{{color:#4f46e5;border-bottom:2px solid #e5e7eb;padding-bottom:.5rem;margin-top:0}}
    .section-text{{color:#4b5563;line-height:1.6}}
    .chart-wrap{{margin-top:1rem}}
    .insights{{background:white;border-radius:.75rem;padding:1.5rem;border:1px solid #e5e7eb}}
    .insights h2{{color:#4f46e5;margin-top:0}}
    .insight{{padding:.75rem 1rem;margin-bottom:.75rem;background:#f9fafb;border-radius:0 .5rem .5rem 0}}
    .insight strong{{display:block;margin-bottom:.25rem}}
    .insight p{{margin:0;color:#4b5563;font-size:.9rem}}
    .footer{{text-align:center;color:#9ca3af;font-size:.8rem;margin-top:2rem}}
  </style>
</head>
<body>
  <div class="header">
    <h1>{name}</h1>
    <div class="meta">
      Framework: {fw_name} &bull;
      Dataset: {dataset.source_name} ({dataset.n_rows} linhas, {dataset.n_cols} colunas) &bull;
      Gerado em: {dt_str}
    </div>
  </div>
  {sections_html}
  <div class="insights">
    <h2>Insights Automáticos</h2>
    {insights_html if insights_html else '<p style="color:#9ca3af">Nenhum insight gerado.</p>'}
  </div>
  <div class="footer">
    Gerado por Report Generator &bull; {dt_str}
  </div>
</body>
</html>"""
