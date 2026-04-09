"""Componente de cabeçalho com progresso de etapas."""

import streamlit as st

_LABELS = ["Upload", "Processamento", "Framework", "Builder", "Preview", "Publicados"]
_CHECKS = ["raw_df", "processed_df", "framework_id", "framework_sections", None, None]


def render_step_header(current_step: int) -> None:
    """
    Renderiza indicador de progresso no topo da página.

    Args:
        current_step: Etapa atual (1 a 6, baseado em 1).
    """
    cols = st.columns(len(_LABELS))
    for i, (label, check_key) in enumerate(zip(_LABELS, _CHECKS)):
        step_num = i + 1
        done = check_key is not None and st.session_state.get(check_key) is not None
        is_current = step_num == current_step

        if done and not is_current:
            color, icon, weight = "#059669", "✅", "400"
        elif is_current:
            color, icon, weight = "#4f46e5", "●", "700"
        else:
            color, icon, weight = "#9ca3af", "○", "400"

        with cols[i]:
            st.markdown(
                f'<div style="text-align:center;color:{color};font-size:0.72rem;'
                f'font-weight:{weight};line-height:1.5;">'
                f'{icon}<br>{label}</div>',
                unsafe_allow_html=True,
            )

    progress = max(0.0, min(1.0, (current_step - 1) / (len(_LABELS) - 1)))
    st.progress(progress)
    st.markdown("")
