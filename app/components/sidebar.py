"""Sidebar compartilhado com navegação e status de progresso."""

import streamlit as st

_STEPS = [
    ("pages/01_upload.py", "Upload de Dados", "raw_df"),
    ("pages/02_processing.py", "Processamento", "processed_df"),
    ("pages/03_framework.py", "Framework", "framework_id"),
    ("pages/04_builder.py", "Builder", "framework_sections"),
    ("pages/05_preview.py", "Preview", None),
    ("pages/06_published.py", "Publicados", None),
]


def render_sidebar() -> None:
    """Renderiza sidebar consistente em todas as páginas."""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/combo-chart--v2.png", width=56)
        st.title("Report Generator")
        st.markdown("---")

        st.markdown("**Etapas**")
        for page_path, label, check_key in _STEPS:
            done = check_key is not None and st.session_state.get(check_key) is not None
            icon = "✅" if done else "○"
            st.page_link(page_path, label=f"{icon} {label}")

        st.markdown("---")

        # Resumo do estado atual
        raw_df = st.session_state.get("raw_df")
        if raw_df is not None:
            source = st.session_state.get("source_name", "Dados carregados")
            # Trunca source_name longo
            display_source = source if len(source) <= 30 else source[:27] + "..."
            st.caption(f"📂 {display_source}")
            st.caption(f"{len(raw_df):,} linhas × {len(raw_df.columns)} colunas")

        fw_id = st.session_state.get("framework_id")
        if fw_id:
            from app.config.settings import SUPPORTED_FRAMEWORKS
            fw_name = SUPPORTED_FRAMEWORKS.get(fw_id, fw_id.upper())
            st.caption(f"🧩 {fw_name}")

        sections = st.session_state.get("framework_sections")
        if sections:
            insights = st.session_state.get("insights", [])
            st.caption(f"📈 {len(sections)} seção(ões) | {len(insights)} insight(s)")

        st.markdown("---")
        st.caption("v1.1.0 — Report Generator")
