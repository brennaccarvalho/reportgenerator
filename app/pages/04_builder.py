"""Página 4 — Builder: configuração do relatório."""

import streamlit as st
import pandas as pd

from app.models.report_model import ReportConfig
from app.services.framework_selector import run_framework
from app.services.insight_generator import generate_insights

st.set_page_config(page_title="Builder — Report Generator", layout="wide")

st.title("4. Configurar o Relatório")

# Validações de estado
if st.session_state.get("processed_df") is None:
    st.warning("Dados não processados.")
    st.page_link("pages/02_processing.py", label="← Voltar para Processamento")
    st.stop()

if not st.session_state.get("framework_id"):
    st.warning("Framework não selecionado.")
    st.page_link("pages/03_framework.py", label="← Selecionar Framework")
    st.stop()

df: pd.DataFrame = st.session_state.processed_df
framework_id: str = st.session_state.framework_id

num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
all_cols = df.columns.tolist()

st.markdown(f"**Framework:** {framework_id.upper()} | **Dataset:** {len(df):,} linhas × {len(df.columns)} colunas")

st.divider()

# Nome do relatório
report_name = st.text_input(
    "Nome do relatório",
    value=st.session_state.get("report_name", f"Relatório {framework_id.upper()}"),
    key="report_name_input",
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Dimensões (colunas categóricas)")
    selected_dims = st.multiselect(
        "Selecione as dimensões para análise",
        options=cat_cols,
        default=cat_cols[:2] if cat_cols else [],
        key="builder_dims",
    )

with col2:
    st.markdown("#### Métricas (colunas numéricas)")
    selected_metrics = st.multiselect(
        "Selecione as métricas para análise",
        options=num_cols,
        default=num_cols[:3] if num_cols else [],
        key="builder_metrics",
    )

# Filtros
st.markdown("#### Filtros (opcional)")
filter_col = st.selectbox(
    "Filtrar por coluna",
    options=["(sem filtro)"] + all_cols,
    key="filter_col",
)

filters = {}
if filter_col != "(sem filtro)":
    unique_vals = df[filter_col].dropna().unique().tolist()
    selected_vals = st.multiselect(
        f"Valores de '{filter_col}' a incluir",
        options=unique_vals,
        default=unique_vals,
        key="filter_vals",
    )
    if selected_vals:
        filters[filter_col] = selected_vals

# Agrupamento
groupby = st.selectbox(
    "Agrupar por (dimensão principal)",
    options=["(automático)"] + cat_cols,
    key="groupby_col",
)
groupby_val = None if groupby == "(automático)" else groupby

# Aplicar filtros ao dataframe
filtered_df = df.copy()
for col, vals in filters.items():
    filtered_df = filtered_df[filtered_df[col].isin(vals)]

st.markdown(f"_Dataset após filtros: **{len(filtered_df):,} linhas**_")

st.divider()

if st.button("Gerar análise", type="primary", use_container_width=True):
    if filtered_df.empty:
        st.error("Os filtros aplicados resultaram em dataset vazio. Ajuste os filtros.")
        st.stop()

    with st.spinner("Executando análise e gerando insights..."):
        try:
            sections = run_framework(framework_id, filtered_df)
            insights = generate_insights(filtered_df)

            config = ReportConfig(
                name=report_name,
                framework_id=framework_id,
                dimensions=selected_dims,
                metrics=selected_metrics,
                filters=filters,
                groupby=groupby_val,
            )

            st.session_state.framework_sections = sections
            st.session_state.insights = insights
            st.session_state.report_config = config
            st.session_state.filtered_df = filtered_df
            st.session_state.report_name = report_name

            st.success(f"Análise gerada: {len(sections)} seção(ões) | {len(insights)} insight(s).")

        except Exception as e:
            st.error(f"Erro ao gerar análise: {e}")
            st.stop()

if st.session_state.get("framework_sections"):
    st.page_link("pages/05_preview.py", label="Próximo: Preview do Relatório →", icon="👁️")
