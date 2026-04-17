"""
Rota /framework/<dataset_id> — seleção do framework analítico.

Os 5 frameworks disponíveis:
  ooda        → Observe-Oriente-Decida-Aja (diagnóstico rápido)
  funnel      → Análise de funil de conversão
  performance → Diagnóstico de volume, eficiência e qualidade
  eda         → Análise exploratória (distribuições, correlações, outliers)
  temporal    → Séries temporais (tendência, crescimento, sazonalidade)
"""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session,
)
import pandas as pd

from flask_server.models import Dataset

framework_bp = Blueprint("framework", __name__)

# Catálogo dos frameworks com metadados de exibição
FRAMEWORKS = {
    "ooda": {
        "id": "ooda",
        "name": "OODA Loop",
        "icon": "bi-arrow-repeat",
        "description": (
            "Observe → Oriente → Decida → Aja. "
            "Framework de tomada de decisão rápida adaptado do contexto militar."
        ),
        "best_for": "Diagnósticos rápidos, tomada de decisão sob pressão",
        "color": "#7c3aed",
    },
    "funnel": {
        "id": "funnel",
        "name": "Análise de Funil",
        "icon": "bi-filter",
        "description": (
            "Topo → Meio → Fundo → Conversão. "
            "Mapeia taxas de conversão entre etapas do processo."
        ),
        "best_for": "Vendas, marketing, jornada do cliente",
        "color": "#0891b2",
    },
    "performance": {
        "id": "performance",
        "name": "Diagnóstico de Performance",
        "icon": "bi-speedometer2",
        "description": (
            "Volume → Eficiência → Qualidade. "
            "Analisa a performance operacional de forma estruturada."
        ),
        "best_for": "Operações, produção, KPIs de negócio",
        "color": "#059669",
    },
    "eda": {
        "id": "eda",
        "name": "EDA — Exploratória",
        "icon": "bi-search",
        "description": (
            "Distribuições → Correlações → Outliers. "
            "Análise exploratória completa dos dados."
        ),
        "best_for": "Exploração inicial, descoberta de padrões",
        "color": "#d97706",
    },
    "temporal": {
        "id": "temporal",
        "name": "Análise Temporal",
        "icon": "bi-graph-up",
        "description": (
            "Tendência → Crescimento → Sazonalidade. "
            "Analisa séries temporais e variações ao longo do tempo."
        ),
        "best_for": "Dados com coluna de data, tendências, sazonalidade",
        "color": "#dc2626",
    },
}


@framework_bp.route("/framework/<dataset_id>", methods=["GET"])
def framework_page(dataset_id):
    """Exibe os cards de seleção de framework."""
    dataset = Dataset.query.get_or_404(dataset_id)

    # Detecta se há coluna de data para destacar framework temporal
    has_date_col = False
    try:
        df = pd.read_csv(dataset.storage_path, nrows=5)
        date_keywords = ("data", "date", "periodo", "mes", "ano", "dt_")
        has_date_col = any(
            any(kw in col.lower() for kw in date_keywords)
            for col in df.columns
        )
    except Exception:
        pass

    dataset_info = {
        "id": dataset.id,
        "name": dataset.name,
        "n_rows": dataset.n_rows,
        "n_cols": dataset.n_cols,
        "framework": session.get("framework_id"),
    }

    return render_template(
        "framework.html",
        current_step="framework",
        current_step_num=3,
        dataset_info=dataset_info,
        dataset=dataset,
        frameworks=FRAMEWORKS,
        has_date_col=has_date_col,
        selected_framework=session.get("framework_id"),
    )


@framework_bp.route("/framework/<dataset_id>", methods=["POST"])
def select_framework(dataset_id):
    """Salva o framework escolhido na sessão e avança para o builder."""
    Dataset.query.get_or_404(dataset_id)
    framework_id = request.form.get("framework_id")

    if framework_id not in FRAMEWORKS:
        flash("Framework inválido. Selecione uma das opções.", "error")
        return redirect(
            url_for("framework.framework_page", dataset_id=dataset_id)
        )

    session["framework_id"] = framework_id
    return redirect(url_for("builder.builder_page", dataset_id=dataset_id))
