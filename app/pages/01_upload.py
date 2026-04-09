"""Página 1 — Upload de dados (arquivo ou Google Sheets)."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.file_loader import load_file
from app.services.google_sheets_loader import list_sheets, load_sheet
from app.utils.validators import validate_google_sheets_url
from app.components.sidebar import render_sidebar
from app.components.step_header import render_step_header

st.set_page_config(page_title="Upload — Report Generator", layout="wide")

render_sidebar()
render_step_header(1)

st.title("1. Carregar Dados")
st.markdown(
    "Faça upload de uma planilha ou informe o link de um Google Sheets para começar."
)

# Inicializar estado
for key in ["raw_df", "source_name", "source_type"]:
    if key not in st.session_state:
        st.session_state[key] = None

tab_file, tab_sheets = st.tabs(["Arquivo (.csv / .xlsx)", "Google Sheets"])

# --- TAB: Upload de arquivo ---
with tab_file:
    uploaded = st.file_uploader(
        "Selecione o arquivo",
        type=["csv", "xlsx", "xls"],
        help="Tamanho máximo: 50MB",
    )

    if uploaded:
        try:
            file_bytes = uploaded.read()
            df, msg = load_file(file_bytes, uploaded.name)

            st.success(msg)
            st.markdown("**Preview das primeiras 5 linhas:**")
            st.dataframe(df.head(), use_container_width=True)

            if st.button("Usar este arquivo e continuar →", type="primary", key="btn_use_file", use_container_width=True):
                st.session_state.raw_df = df
                st.session_state.source_name = uploaded.name
                st.session_state.source_type = "upload"
                for key in ["processed_df", "profile", "framework_id", "framework_sections", "insights", "report_config"]:
                    st.session_state.pop(key, None)
                st.switch_page("pages/02_processing.py")

        except ValueError as e:
            st.error(f"Erro: {e}")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")

# --- TAB: Google Sheets ---
with tab_sheets:
    url = st.text_input(
        "URL da planilha Google Sheets",
        placeholder="https://docs.google.com/spreadsheets/d/...",
    )

    if url:
        if not validate_google_sheets_url(url):
            st.error("URL inválida. Copie diretamente do navegador.")
        else:
            if st.button("Listar abas", key="btn_list_sheets"):
                with st.spinner("Conectando ao Google Sheets..."):
                    try:
                        sheet_names = list_sheets(url)
                        st.session_state["_gs_sheets"] = sheet_names
                        st.session_state["_gs_url"] = url
                    except ValueError as e:
                        st.error(f"Erro: {e}")

    if st.session_state.get("_gs_sheets"):
        selected_sheet = st.selectbox(
            "Selecione a aba",
            options=st.session_state["_gs_sheets"],
            key="gs_sheet_select",
        )
        if st.button("Carregar aba e continuar →", type="primary", key="btn_load_sheet", use_container_width=True):
            with st.spinner("Carregando dados..."):
                try:
                    gs_url = st.session_state.get("_gs_url", url)
                    df, msg = load_sheet(gs_url, selected_sheet)
                    st.success(msg)

                    st.session_state.raw_df = df
                    st.session_state.source_name = f"{gs_url} / {selected_sheet}"
                    st.session_state.source_type = "google_sheets"
                    for key in ["processed_df", "profile", "framework_id", "framework_sections", "insights", "report_config"]:
                        st.session_state.pop(key, None)
                    st.switch_page("pages/02_processing.py")
                except ValueError as e:
                    st.error(f"Erro: {e}")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")

# Status atual
st.divider()
if st.session_state.raw_df is not None:
    df = st.session_state.raw_df
    st.success(
        f"Dados ativos: **{st.session_state.source_name}** "
        f"— {len(df):,} linhas × {len(df.columns)} colunas"
    )
    st.page_link("pages/02_processing.py", label="Próximo: Processamento →", icon="⚙️")
