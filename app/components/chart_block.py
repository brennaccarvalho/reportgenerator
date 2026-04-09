"""Componente de bloco de gráfico editável para o Streamlit."""

from typing import Any, Dict, Tuple

import pandas as pd
import streamlit as st

from app.services.chart_builder import build_chart


def render_chart_block(
    section_key: str,
    section: Dict[str, Any],
) -> Tuple[Dict[str, Any], str]:
    """
    Renderiza um bloco de gráfico interativo com controles de edição.

    Permite ao usuário trocar tipo de gráfico, editar título,
    ordenar resultados e limitar o número de itens exibidos.

    Args:
        section_key: Chave única da seção (usada para state).
        section: Dicionário da seção com title, text, data e chart_config.

    Returns:
        Tupla (chart_config atualizado, título da seção).
    """
    chart_config = section.get("chart_config", {}).copy()
    data: pd.DataFrame = section.get("data", pd.DataFrame())
    title = section.get("title", "")
    text = section.get("text", "")

    st.markdown(f"### {title}")

    with st.expander("Configurar gráfico", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            chart_type = st.selectbox(
                "Tipo de gráfico",
                options=["bar", "line", "pie", "scatter", "table"],
                index=["bar", "line", "pie", "scatter", "table"].index(
                    chart_config.get("chart_type", "bar")
                ),
                key=f"chart_type_{section_key}",
            )
            chart_config["chart_type"] = chart_type

            new_title = st.text_input(
                "Título do gráfico",
                value=chart_config.get("title", ""),
                key=f"title_{section_key}",
            )
            chart_config["title"] = new_title

        with col2:
            sort_order = st.selectbox(
                "Ordenar por valor",
                options=["(sem ordenação)", "desc", "asc"],
                index=0,
                key=f"sort_{section_key}",
                format_func=lambda x: {
                    "(sem ordenação)": "Sem ordenação",
                    "desc": "Maior → Menor",
                    "asc": "Menor → Maior",
                }.get(x, x),
            )
            chart_config["sort_order"] = None if sort_order == "(sem ordenação)" else sort_order

            top_n = st.number_input(
                "Limitar resultados (top N)",
                min_value=0,
                max_value=200,
                value=0,
                step=5,
                key=f"topn_{section_key}",
                help="0 = sem limite",
            )
            chart_config["top_n"] = int(top_n) if top_n > 0 else None

    # Renderizar gráfico
    if not data.empty:
        try:
            fig = build_chart(data, chart_config)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao renderizar gráfico: {e}")
    else:
        st.info("Sem dados para exibir nesta seção.")

    # Texto analítico
    if text:
        st.markdown(
            f'<div style="background:#f0f4ff;border-left:4px solid #4f46e5;'
            f'padding:12px 16px;border-radius:4px;margin-top:8px;'
            f'font-size:0.95rem;color:#1f2937;">{text}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    return chart_config, title
