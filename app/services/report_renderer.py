"""Serviço de renderização de relatórios em PDF, HTML e CSV."""

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from app.config.settings import TEMPLATES_DIR
from app.services.chart_builder import build_chart, chart_to_image_bytes
from app.utils.logger import get_logger

logger = get_logger(__name__)

_FRAMEWORK_LABELS = {
    "ooda": "OODA Loop",
    "funnel": "Funil de Conversão",
    "performance": "Diagnóstico de Performance",
    "eda": "Análise Exploratória",
    "temporal": "Comparação Temporal",
}


def _build_jinja_env() -> Environment:
    """Cria ambiente Jinja2 apontando para o diretório de templates."""
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True,
    )


def _sections_to_context(
    sections: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Converte seções do framework em contexto renderizável para Jinja2.
    Gera imagens base64 de cada gráfico.
    """
    rendered_sections = []
    for key, section in sections.items():
        chart_config = section.get("chart_config", {})
        data = section.get("data", pd.DataFrame())

        img_b64 = ""
        try:
            if not data.empty:
                fig = build_chart(data, chart_config)
                img_bytes = chart_to_image_bytes(fig)
                if img_bytes:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Falha ao gerar imagem do gráfico '{key}': {e}")

        rendered_sections.append({
            "title": section.get("title", ""),
            "text": section.get("text", ""),
            "chart_img_b64": img_b64,
        })
    return rendered_sections


def render_html(
    report_name: str,
    framework_id: str,
    sections: Dict[str, Any],
    insights: List[Dict[str, Any]],
    df: pd.DataFrame,
) -> bytes:
    """
    Renderiza o relatório como HTML usando Jinja2.

    Args:
        report_name: Nome do relatório.
        framework_id: ID do framework usado.
        sections: Seções analíticas geradas.
        insights: Lista de insights automáticos.
        df: DataFrame processado.

    Returns:
        Bytes do arquivo HTML.
    """
    env = _build_jinja_env()
    template = env.get_template("report_base.html")

    context = {
        "report_name": report_name,
        "framework_name": _FRAMEWORK_LABELS.get(framework_id, framework_id),
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "sections": _sections_to_context(sections),
        "insights": insights,
    }

    html_str = template.render(**context)
    return html_str.encode("utf-8")


def render_pdf(
    report_name: str,
    framework_id: str,
    sections: Dict[str, Any],
    insights: List[Dict[str, Any]],
    df: pd.DataFrame,
) -> bytes:
    """
    Renderiza o relatório como PDF usando WeasyPrint.

    Args:
        report_name: Nome do relatório.
        framework_id: ID do framework usado.
        sections: Seções analíticas geradas.
        insights: Lista de insights automáticos.
        df: DataFrame processado.

    Returns:
        Bytes do arquivo PDF.

    Raises:
        ImportError: Se WeasyPrint não estiver instalado.
        RuntimeError: Se a geração de PDF falhar.
    """
    try:
        from weasyprint import HTML as WeasyHTML
    except ImportError:
        raise ImportError(
            "WeasyPrint não está instalado ou há dependências faltando. "
            "Instale com: pip install weasyprint"
        )

    html_bytes = render_html(report_name, framework_id, sections, insights, df)
    try:
        pdf_bytes = WeasyHTML(string=html_bytes.decode("utf-8")).write_pdf()
        return pdf_bytes
    except Exception as e:
        raise RuntimeError(f"Erro ao gerar PDF: {e}")


def render_csv(df: pd.DataFrame) -> bytes:
    """
    Exporta o DataFrame processado como CSV.

    Args:
        df: DataFrame processado.

    Returns:
        Bytes do arquivo CSV.
    """
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue()
