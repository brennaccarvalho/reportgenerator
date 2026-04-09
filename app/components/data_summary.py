"""Componente de resumo de dados para o Streamlit."""

from typing import Any, Dict

import pandas as pd
import streamlit as st


def render_data_summary(profile: Dict[str, Any]) -> None:
    """
    Renderiza o painel de resumo do dataset com métricas e alertas.

    Args:
        profile: Dicionário de perfil gerado por data_profiler.profile_dataframe().
    """
    n_rows = profile.get("n_rows", 0)
    n_cols = profile.get("n_cols", 0)
    issues = profile.get("issues", [])
    transformations = profile.get("transformations_log", [])
    columns = profile.get("columns", [])

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Linhas", f"{n_rows:,}")
    with col2:
        st.metric("Colunas", f"{n_cols}")
    with col3:
        total_nulls = sum(c["null_count"] for c in columns)
        st.metric("Valores Nulos", f"{total_nulls:,}")
    with col4:
        st.metric("Alertas", f"{len(issues)}", delta=None)

    st.divider()

    # Tipos de colunas
    if columns:
        st.markdown("#### Colunas e Tipos Detectados")
        col_data = [
            {
                "Coluna": c["name"],
                "Tipo": c["inferred_type"],
                "Nulos": f"{c['null_count']} ({c['null_pct']:.1f}%)",
                "Únicos": c["unique_count"],
                "Exemplos": ", ".join(str(v) for v in c["sample_values"][:3]),
            }
            for c in columns
        ]
        st.dataframe(pd.DataFrame(col_data), use_container_width=True)

    # Alertas de qualidade
    if issues:
        st.markdown("#### Alertas de Qualidade")
        for issue in issues:
            st.warning(issue)
    else:
        st.success("Nenhum problema de qualidade detectado nos dados.")

    # Log de transformações
    if transformations:
        with st.expander("Ver transformações aplicadas"):
            for t in transformations:
                st.markdown(f"- {t}")
