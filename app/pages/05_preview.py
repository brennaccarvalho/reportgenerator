"""Página 5 — Preview interativo do relatório."""

import streamlit as st
import pandas as pd

from app.components.chart_block import render_chart_block
from app.components.insight_card import render_insights_panel
from app.services.report_renderer import render_pdf, render_html, render_csv
from app.services.publisher import publish_report

st.set_page_config(page_title="Preview — Report Generator", layout="wide")

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

# Exportação
st.markdown("## Exportar Relatório")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Exportar PDF", use_container_width=True):
        with st.spinner("Gerando PDF..."):
            try:
                pdf_bytes = render_pdf(
                    report_name=report_name,
                    framework_id=framework_id,
                    sections=sections,
                    insights=insights,
                    df=df,
                )
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"{report_name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key="dl_pdf",
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

with col2:
    if st.button("Exportar HTML", use_container_width=True):
        with st.spinner("Gerando HTML..."):
            try:
                html_bytes = render_html(
                    report_name=report_name,
                    framework_id=framework_id,
                    sections=sections,
                    insights=insights,
                    df=df,
                )
                st.download_button(
                    label="Download HTML",
                    data=html_bytes,
                    file_name=f"{report_name.replace(' ', '_')}.html",
                    mime="text/html",
                    key="dl_html",
                )
            except Exception as e:
                st.error(f"Erro ao gerar HTML: {e}")

with col3:
    if st.button("Exportar CSV", use_container_width=True):
        try:
            csv_bytes = render_csv(df)
            st.download_button(
                label="Download CSV",
                data=csv_bytes,
                file_name=f"{report_name.replace(' ', '_')}_dados.csv",
                mime="text/csv",
                key="dl_csv",
            )
        except Exception as e:
            st.error(f"Erro ao gerar CSV: {e}")

st.divider()

# Publicar
st.markdown("## Publicar Relatório")
st.markdown("Salve o relatório para acessá-lo depois na galeria de relatórios publicados.")

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
            st.success(f"Relatório publicado com sucesso! ID: `{report_id}`")
            st.page_link("pages/06_published.py", label="Ver relatórios publicados →", icon="📚")
        except Exception as e:
            st.error(f"Erro ao publicar: {e}")
