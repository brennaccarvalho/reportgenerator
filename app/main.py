"""Entrypoint principal do Report Generator — Streamlit."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.db import init_db
from app.components.sidebar import render_sidebar

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

render_sidebar()

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

# Próximo passo sugerido
if st.session_state.raw_df is None:
    st.markdown("**Comece agora — faça o upload dos seus dados:**")
    st.page_link("pages/01_upload.py", label="Fazer upload de dados →", icon="📂")
elif st.session_state.processed_df is None:
    st.markdown("**Próximo passo:**")
    st.page_link("pages/02_processing.py", label="Processar dados →", icon="⚙️")
elif st.session_state.framework_id is None:
    st.markdown("**Próximo passo:**")
    st.page_link("pages/03_framework.py", label="Escolher framework →", icon="🧩")
elif st.session_state.framework_sections is None:
    st.markdown("**Próximo passo:**")
    st.page_link("pages/04_builder.py", label="Configurar relatório →", icon="🛠️")
else:
    st.markdown("**Relatório pronto — veja o resultado:**")
    st.page_link("pages/05_preview.py", label="Ver preview →", icon="👁️")

st.divider()

st.markdown("### Como usar")
st.markdown(
    """
1. **Upload** — Faça upload de um arquivo .csv ou .xlsx, ou cole o link de um Google Sheets
2. **Processamento** — Os dados são limpos e normalizados automaticamente
3. **Framework** — Escolha a lente analítica: OODA, Funil, Performance, EDA ou Temporal
4. **Builder** — Configure dimensões, métricas e filtros
5. **Preview** — Veja o relatório interativo e exporte em PDF, HTML ou CSV
6. **Publicados** — Acesse relatórios salvos anteriormente
    """
)
