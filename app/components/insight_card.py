"""Componente de card de insight para o Streamlit."""

from typing import Any, Dict, List

import streamlit as st


_SEVERITY_STYLE = {
    "info": ("ℹ️", "#e0f2fe", "#0369a1"),
    "warning": ("⚠️", "#fef9c3", "#92400e"),
    "critical": ("🚨", "#fee2e2", "#991b1b"),
}


def render_insight_card(insight: Dict[str, Any]) -> None:
    """
    Renderiza um card de insight individual.

    Args:
        insight: Dicionário com type, title, description e severity.
    """
    severity = insight.get("severity", "info")
    icon, bg_color, text_color = _SEVERITY_STYLE.get(severity, _SEVERITY_STYLE["info"])
    title = insight.get("title", "")
    description = insight.get("description", "")

    st.markdown(
        f"""
        <div style="
            background:{bg_color};
            border-radius:8px;
            padding:12px 16px;
            margin-bottom:10px;
            color:{text_color};
        ">
            <strong>{icon} {title}</strong><br>
            <span style="font-size:0.9rem;">{description}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insights_panel(insights: List[Dict[str, Any]]) -> None:
    """
    Renderiza um painel completo de insights agrupados por severidade.

    Args:
        insights: Lista de insights gerados.
    """
    if not insights:
        st.info("Nenhum insight detectado para este dataset.")
        return

    criticals = [i for i in insights if i.get("severity") == "critical"]
    warnings = [i for i in insights if i.get("severity") == "warning"]
    infos = [i for i in insights if i.get("severity") == "info"]

    if criticals:
        st.markdown("#### Alertas Críticos")
        for ins in criticals:
            render_insight_card(ins)

    if warnings:
        st.markdown("#### Atenção")
        for ins in warnings:
            render_insight_card(ins)

    if infos:
        st.markdown("#### Informações")
        for ins in infos:
            render_insight_card(ins)
