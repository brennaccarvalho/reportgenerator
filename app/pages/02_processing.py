"""Página 2 — Processamento e saneamento dos dados."""

import streamlit as st

from app.services.data_cleaner import clean_dataframe
from app.services.data_profiler import profile_dataframe
from app.components.data_summary import render_data_summary

st.set_page_config(page_title="Processamento — Report Generator", layout="wide")

st.title("2. Processamento dos Dados")

if st.session_state.get("raw_df") is None:
    st.warning("Nenhum dado carregado. Volte para a etapa de Upload.")
    st.page_link("pages/01_upload.py", label="← Voltar para Upload")
    st.stop()

raw_df = st.session_state.raw_df

# Processar se ainda não foi feito
if st.session_state.get("processed_df") is None:
    with st.spinner("Processando e limpando os dados..."):
        try:
            processed_df, transformations_log = clean_dataframe(raw_df)
            profile = profile_dataframe(processed_df, transformations_log)
            st.session_state.processed_df = processed_df
            st.session_state.profile = profile
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
            st.stop()

processed_df = st.session_state.processed_df
profile = st.session_state.profile

# Botão para reprocessar
if st.button("Reprocessar dados"):
    processed_df, transformations_log = clean_dataframe(raw_df)
    profile = profile_dataframe(processed_df, transformations_log)
    st.session_state.processed_df = processed_df
    st.session_state.profile = profile
    st.rerun()

st.markdown("### Resumo do Dataset Processado")
render_data_summary(profile)

# Toggle raw vs processed
st.divider()
st.markdown("### Comparativo: Original vs. Processado")
show_raw = st.toggle("Exibir dados originais (brutos)", value=False)

if show_raw:
    st.markdown("**Dados originais:**")
    st.dataframe(raw_df.head(20), use_container_width=True)
else:
    st.markdown("**Dados processados:**")
    st.dataframe(processed_df.head(20), use_container_width=True)

st.divider()
st.page_link("pages/03_framework.py", label="Próximo: Escolher Framework →", icon="🧩")
