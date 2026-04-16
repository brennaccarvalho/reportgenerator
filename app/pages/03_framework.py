"""Página 3 — Escolha do framework analítico."""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import SUPPORTED_FRAMEWORKS
from app.components.sidebar import render_sidebar
from app.components.step_header import render_step_header

st.set_page_config(page_title="Framework — Report Generator", layout="wide")

render_sidebar()
render_step_header(3)

st.title("3. Escolha o Framework Analítico")
st.markdown(
    "O framework define a lente estratégica pela qual seus dados serão interpretados."
)

if st.session_state.get("processed_df") is None:
    st.warning("Dados não processados. Volte para a etapa anterior.")
    st.page_link("pages/02_processing.py", label="← Voltar para Processamento")
    st.stop()

FRAMEWORK_DESCRIPTIONS = {
    "ooda": {
        "name": "OODA Loop",
        "icon": "🔄",
        "dimensions": "Observe → Orient → Decide → Act",
        "description": (
            "Analisa dados em 4 fases militares adaptadas ao negócio: "
            "observe o panorama geral, oriente o contexto comparativo, "
            "decida com base em correlações e aja com recomendações priorizadas."
        ),
        "ideal_for": "Análise estratégica geral, tomada de decisão executiva",
    },
    "funnel": {
        "name": "Funil de Conversão",
        "icon": "📊",
        "dimensions": "Topo → Meio → Fundo → Conversão → Gargalos",
        "description": (
            "Mapeia o fluxo de volume através de etapas sequenciais, "
            "identificando taxas de conversão e gargalos em cada fase."
        ),
        "ideal_for": "Marketing, vendas, e-commerce, jornadas de usuário",
    },
    "performance": {
        "name": "Diagnóstico de Performance",
        "icon": "⚡",
        "dimensions": "Volume → Eficiência → Qualidade",
        "description": (
            "Avalia quanto foi produzido (volume), com que eficiência "
            "(relação insumo/resultado) e com que consistência (qualidade)."
        ),
        "ideal_for": "Operações, equipes de vendas, produção, KPIs operacionais",
    },
    "eda": {
        "name": "Análise Exploratória",
        "icon": "🔬",
        "dimensions": "Distribuições → Correlações → Outliers",
        "description": (
            "Explora o dataset de forma abrangente: distribuições estatísticas, "
            "relações entre variáveis e identificação de valores atípicos."
        ),
        "ideal_for": "Primeiro contato com dados novos, análise científica, data science",
    },
    "temporal": {
        "name": "Comparação Temporal",
        "icon": "📈",
        "dimensions": "Tendência → Crescimento → Sazonalidade",
        "description": (
            "Analisa a evolução ao longo do tempo, calculando crescimento "
            "período a período e identificando padrões sazonais."
        ),
        "ideal_for": "Séries temporais, dados financeiros, métricas com data",
    },
    "meridian": {
        "name": "Media Mix Model (Meridian)",
        "icon": "📡",
        "dimensions": "Investimento → ROI → Otimização de Budget",
        "description": (
            "Quantifica o impacto real de cada canal de marketing nas vendas usando inferência Bayesiana (MCMC). "
            "Ideal para analisar ROI por canal e otimizar distribuição de verba."
        ),
        "ideal_for": "Análise de mix de mídia, atribuição de vendas a canais de marketing, otimização de budget.",
        "note": "⚠️ Requer TensorFlow e GPU (recomendado). Tempo de treino: 10-60 min.",
    },
}


# Frameworks with a custom next-page destination (others go to 04_builder.py)
_NEXT_PAGE: dict[str, tuple[str, str, str]] = {
    "meridian": ("pages/07_meridian.py", "Iniciar análise MMM →", "📡"),
}


def _suggest_framework(profile: dict) -> str | None:
    """Sugere framework baseado no perfil dos dados."""
    if not profile:
        return None
    types = [c["inferred_type"] for c in profile.get("columns", [])]
    if "data" in types:
        return "temporal"
    cats = types.count("categórico")
    nums = types.count("numérico")
    if cats >= 2 and nums >= 1:
        return "funnel"
    if nums >= 3:
        return "performance"
    return "eda"


profile = st.session_state.get("profile")
suggested = _suggest_framework(profile)

if suggested:
    suggested_name = FRAMEWORK_DESCRIPTIONS[suggested]["name"]
    st.info(
        f"💡 **Recomendado para seus dados:** {FRAMEWORK_DESCRIPTIONS[suggested]['icon']} {suggested_name} "
        f"— baseado no perfil das colunas detectadas.",
        icon=None,
    )

st.markdown("")

# Grid de cards de framework
selected_fw = st.session_state.get("framework_id")

cols = st.columns(2)
options = list(FRAMEWORK_DESCRIPTIONS.keys())

for i, fw_id in enumerate(options):
    fw = FRAMEWORK_DESCRIPTIONS[fw_id]
    col = cols[i % 2]
    with col:
        is_selected = selected_fw == fw_id
        is_suggested = fw_id == suggested and not is_selected
        border_color = "#4f46e5" if is_selected else ("#f59e0b" if is_suggested else "#e5e7eb")
        bg_color = "#eef2ff" if is_selected else ("#fffbeb" if is_suggested else "#ffffff")

        note_html = (
            f'<p style="color:#92400e;font-size:0.82rem;margin:6px 0 0 0;background:#fef3c7;padding:4px 8px;border-radius:6px;">{fw["note"]}</p>'
            if fw.get("note") else ""
        )
        st.markdown(
            f"""
            <div style="
                border: 2px solid {border_color};
                background: {bg_color};
                border-radius: 10px;
                padding: 16px 20px;
                margin-bottom: 12px;
            ">
                <h3 style="margin:0;color:#1f2937;">{fw['icon']} {fw['name']}
                    {'<span style="font-size:0.7rem;background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:12px;margin-left:8px;vertical-align:middle;">⭐ Recomendado</span>' if is_suggested else ''}
                    {'<span style="font-size:0.7rem;background:#ede9fe;color:#4f46e5;padding:2px 8px;border-radius:12px;margin-left:8px;vertical-align:middle;">✓ Selecionado</span>' if is_selected else ''}
                </h3>
                <p style="color:#6366f1;font-size:0.85rem;margin:4px 0 8px 0;">
                    {fw['dimensions']}
                </p>
                <p style="color:#374151;font-size:0.92rem;margin:0 0 8px 0;">
                    {fw['description']}
                </p>
                <p style="color:#6b7280;font-size:0.82rem;margin:0;">
                    <strong>Ideal para:</strong> {fw['ideal_for']}
                </p>
                {note_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            f"{'✓ Selecionado' if is_selected else 'Selecionar'} — {fw['name']}",
            key=f"fw_btn_{fw_id}",
            type="primary" if is_selected else "secondary",
            use_container_width=True,
        ):
            st.session_state.framework_id = fw_id
            st.session_state.pop("framework_sections", None)
            st.session_state.pop("insights", None)
            st.rerun()

st.divider()

if st.session_state.get("framework_id"):
    fw_name = FRAMEWORK_DESCRIPTIONS[st.session_state.framework_id]["name"]
    col_status, col_nav = st.columns([2, 1])
    with col_status:
        st.success(f"Framework selecionado: **{fw_name}**")
    with col_nav:
        next_page = _NEXT_PAGE.get(st.session_state.framework_id, ("pages/04_builder.py", "Próximo: Configurar Relatório →", "🛠️"))
        st.page_link(next_page[0], label=next_page[1], icon=next_page[2])
else:
    st.info("Selecione um framework para continuar.")
