"""Entrypoint principal do Report Generator — Streamlit."""

import streamlit as st
from app.config.db import init_db

st.set_page_config(
    page_title="Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar banco de dados
init_db()

# Inicializar session_state global
defaults = {
    "raw_df": None,
    "processed_df": None,
    "profile": None,
    "source_name": None,
    "source_type": None,
    "framework_id": None,
    "framework_sections": None,
    "insights": None,
    "report_config": None,
    "filtered_df": None,
    "report_name": "Meu Relatório",
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Sidebar de navegação
with st.sidebar:
    st.image("https://img.icons8.com/color/96/combo-chart--v2.png", width=64)
    st.title("Report Generator")
    st.markdown("---")

    steps = [
        ("01_upload", "1. Upload de Dados"),
        ("02_processing", "2. Processamento"),
        ("03_framework", "3. Framework"),
        ("04_builder", "4. Builder"),
        ("05_preview", "5. Preview"),
        ("06_published", "6. Publicados"),
    ]

    for page_id, label in steps:
        st.page_link(f"pages/{page_id}.py", label=label)

    st.markdown("---")
    st.caption("v1.0.0 — Report Generator")

# Home / Dashboard de status
st.title("📊 Report Generator")
st.markdown(
    "Transforme planilhas em relatórios analíticos estruturados com insights automáticos."
)

st.divider()

# Cards de status do fluxo atual
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.raw_df is not None:
        df = st.session_state.raw_df
        st.success(f"✅ Dados carregados\n\n{len(df):,} linhas × {len(df.columns)} colunas")
    else:
        st.info("📂 Nenhum dado carregado")

with col2:
    if st.session_state.framework_id:
        from app.config.settings import SUPPORTED_FRAMEWORKS
        fw_name = SUPPORTED_FRAMEWORKS.get(st.session_state.framework_id, "")
        st.success(f"✅ Framework: {fw_name}")
    else:
        st.info("🧩 Framework não selecionado")

with col3:
    if st.session_state.framework_sections:
        n = len(st.session_state.framework_sections)
        st.success(f"✅ Análise gerada\n\n{n} seção(ões)")
    else:
        st.info("📈 Análise não gerada")

st.divider()

# Guia de início rápido
st.markdown("### Como usar")
st.markdown(
    """
1. **Upload** — Faça upload de um arquivo .csv ou .xlsx, ou cole o link de um Google Sheets
2. **Processamento** — Os dados são limpos e normalizados automaticamente
3. **Framework** — Escolha a lente analítica: OODA, Funil, Performance, EDA ou Temporal
4. **Builder** — Configure dimensões, métricas e filtros
5. **Preview** — Veja o relatório interativo e edite os gráficos
6. **Publicar** — Exporte em PDF, HTML ou CSV, ou publique para acesso posterior
    """
)

st.divider()
st.markdown("**Comece agora:**")
st.page_link("pages/01_upload.py", label="Fazer upload de dados →", icon="📂")
