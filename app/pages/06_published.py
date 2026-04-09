"""Página 6 — Relatórios publicados."""

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.db import init_db, get_connection
from app.config.settings import PUBLISHED_REPORTS_DIR, SUPPORTED_FRAMEWORKS
from app.components.sidebar import render_sidebar
from app.components.step_header import render_step_header

st.set_page_config(page_title="Publicados — Report Generator", layout="wide")

render_sidebar()
render_step_header(6)

st.title("6. Relatórios Publicados")

init_db()


def load_reports() -> pd.DataFrame:
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM reports ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([dict(r) for r in rows])
    except Exception as e:
        st.error(f"Erro ao carregar relatórios: {e}")
        return pd.DataFrame()


def delete_report(report_id: str, path: str) -> None:
    try:
        conn = get_connection()
        conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()
        conn.close()
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        st.error(f"Erro ao deletar relatório: {e}")


reports_df = load_reports()

if reports_df.empty:
    st.info("Nenhum relatório publicado ainda.")
    st.page_link("pages/01_upload.py", label="← Criar um relatório", icon="📊")
    st.stop()

# Filtros em expander para não poluir a tela
with st.expander("Filtros", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        fw_options = ["Todos"] + list(SUPPORTED_FRAMEWORKS.values())
        fw_filter = st.selectbox("Filtrar por Framework", options=fw_options)
    with col2:
        date_filter = st.date_input(
            "A partir de",
            value=None,
            help="Filtrar relatórios criados a partir desta data",
        )

filtered = reports_df.copy()

if fw_filter != "Todos":
    fw_id = [k for k, v in SUPPORTED_FRAMEWORKS.items() if v == fw_filter]
    if fw_id:
        filtered = filtered[filtered["framework"] == fw_id[0]]

if date_filter:
    filtered["created_at"] = pd.to_datetime(filtered["created_at"])
    filtered = filtered[filtered["created_at"].dt.date >= date_filter]

st.markdown(f"**{len(filtered)} relatório(s) encontrado(s)**")
st.divider()

for _, row in filtered.iterrows():
    report_id = row["id"]
    name = row["name"]
    framework = SUPPORTED_FRAMEWORKS.get(row["framework"], row["framework"])
    created = row["created_at"]
    source = row.get("source_name", "")
    path = row["path"]
    n_rows = row.get("n_rows", "—")
    n_cols = row.get("n_cols", "—")

    with st.container():
        c1, c2, c3 = st.columns([4, 2, 1])

        with c1:
            st.markdown(f"**{name}**")
            st.caption(
                f"Framework: `{framework}` · {created} · "
                f"{n_rows} linhas × {n_cols} colunas · Fonte: {source}"
            )

        with c2:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    st.download_button(
                        label="⬇ Download HTML",
                        data=f.read(),
                        file_name=f"{name.replace(' ', '_')}.html",
                        mime="text/html",
                        key=f"dl_{report_id}",
                        use_container_width=True,
                    )
            else:
                st.caption("Arquivo não encontrado")

        with c3:
            if st.button("Deletar", key=f"del_{report_id}", type="secondary", use_container_width=True):
                delete_report(report_id, path)
                st.rerun()

        st.divider()
