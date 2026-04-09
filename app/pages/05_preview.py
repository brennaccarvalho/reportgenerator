"""Página 5 — Preview interativo do relatório."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.chart_block import render_chart_block
from app.components.insight_card import render_insights_panel
from app.components.sidebar import render_sidebar
from app.components.step_header import render_step_header
from app.services.report_renderer import render_pdf, render_html, render_csv
from app.services.publisher import publish_report

st.set_page_config(page_title="Preview — Report Generator", layout="wide")

render_sidebar()
render_step_header(5)

st.title("5. Preview do Relatório")

# Validações
if not st.session_state.get("framework_sections"):
    st.warning("Nenhuma análise gerada. Volte para o Builder.")
    st.page_link("pages/04_builder.py", label="← Voltar para Builder")
    st.stop()

sections: dict = st.session_state.framework_sections
insights: list = st.session_state.get("insights", [])
config = st.session_state.get("report_config")
df: pd.DataFrame = st.session_state.get("filtered_df", st.session_state.get("processed_df"))

report_name = config.name if config else "Relatório"
framework_id = config.framework_id if config else ""

st.markdown(f"**{report_name}** | Framework: `{framework_id.upper()}`")
st.divider()

# Renderizar seções
updated_configs = {}
for section_key, section in sections.items():
    updated_config, section_title = render_chart_block(section_key, section)
    updated_configs[section_key] = updated_config

# Painel de insights
st.markdown("## Insights Automáticos")
render_insights_panel(insights)

st.divider()

# --- Exportação ---
st.markdown("## Exportar Relatório")

# Pré-gerar HTML e CSV na primeira visita (rápidos) e armazenar em session_state
if st.session_state.get("_export_html") is None:
    try:
        st.session_state._export_html = render_html(
            report_name=report_name,
            framework_id=framework_id,
            sections=sections,
            insights=insights,
            df=df,
        )
    except Exception:
        st.session_state._export_html = False  # Flag de erro

if st.session_state.get("_export_csv") is None:
    try:
        st.session_state._export_csv = render_csv(df)
    except Exception:
        st.session_state._export_csv = False

col1, col2, col3 = st.columns(3)

with col1:
    # PDF: gerado sob demanda e persistido
    if st.session_state.get("_export_pdf") is None:
        if st.button("Gerar PDF", use_container_width=True):
            with st.spinner("Gerando PDF..."):
                try:
                    st.session_state._export_pdf = render_pdf(
                        report_name=report_name,
                        framework_id=framework_id,
                        sections=sections,
                        insights=insights,
                        df=df,
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
    else:
        st.download_button(
            label="⬇ Download PDF",
            data=st.session_state._export_pdf,
            file_name=f"{report_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

with col2:
    html_data = st.session_state.get("_export_html")
    if html_data and html_data is not False:
        st.download_button(
            label="⬇ Download HTML",
            data=html_data,
            file_name=f"{report_name.replace(' ', '_')}.html",
            mime="text/html",
            use_container_width=True,
        )
    elif html_data is False:
        st.error("Erro ao gerar HTML.")

with col3:
    csv_data = st.session_state.get("_export_csv")
    if csv_data and csv_data is not False:
        st.download_button(
            label="⬇ Download CSV",
            data=csv_data,
            file_name=f"{report_name.replace(' ', '_')}_dados.csv",
            mime="text/csv",
            use_container_width=True,
        )
    elif csv_data is False:
        st.error("Erro ao gerar CSV.")

st.divider()

# --- Publicar ---
st.markdown("## Publicar Relatório")
st.markdown("Salve o relatório para acessá-lo depois na galeria de relatórios publicados.")

if st.session_state.get("last_published_id"):
    st.success(f"Relatório publicado! ID: `{st.session_state.last_published_id}`")
    col_pub, col_nav = st.columns(2)
    with col_pub:
        if st.button("Publicar novamente", use_container_width=True):
            st.session_state.pop("last_published_id", None)
            st.rerun()
    with col_nav:
        st.page_link("pages/06_published.py", label="Ver relatórios publicados →", icon="📚")
else:
    if st.button("Publicar relatório", type="primary", use_container_width=True):
        with st.spinner("Publicando..."):
            try:
                source_type = st.session_state.get("source_type", "upload")
                source_name = st.session_state.get("source_name", "")

                report_id = publish_report(
                    name=report_name,
                    framework_id=framework_id,
                    sections=sections,
                    insights=insights,
                    df=df,
                    source=source_type,
                    source_name=source_name,
                )
                st.session_state.last_published_id = report_id
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao publicar: {e}")
