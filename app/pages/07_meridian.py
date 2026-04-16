"""Página 7 — Media Mix Model (Meridian)."""

import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.sidebar import render_sidebar
from app.components.step_header import render_step_header
from app.config.settings import PUBLISHED_REPORTS_DIR

try:
    from app.analysis_frameworks.meridian_framework import (
        MERIDIAN_AVAILABLE,
        MeridianFramework,
    )
except ImportError:
    MERIDIAN_AVAILABLE = False
    MeridianFramework = None  # type: ignore[assignment,misc]

from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Media Mix Model — Report Generator", layout="wide")

render_sidebar()
render_step_header(6)  # posição extra após etapa 6 (Publicados)


def _safe_index(lst: list, value: Any, default: int = 0) -> int:
    """Retorna o índice de *value* em *lst* ou *default* se não encontrado."""
    try:
        return lst.index(value)
    except (ValueError, TypeError):
        return default


def _render_tab1_mapeamento(fw: Any) -> None:
    """Aba 1 — Mapeamento de Colunas."""
    if st.session_state.get("processed_df") is None:
        st.warning("Nenhum dataset carregado. Vá para a etapa de Upload.")
        if st.button("Ir para Upload"):
            st.switch_page("pages/01_upload.py")
        return

    df: pd.DataFrame = st.session_state.processed_df

    # Auto-detecção
    st.subheader("Detecção Automática de Colunas")
    detected = fw.detect_columns(df)

    if not detected.get("has_minimum_columns"):
        st.warning(detected.get("message", "Não foi possível detectar colunas adequadas."))
    else:
        st.success(detected.get("message", "Colunas detectadas com sucesso."))

    st.divider()

    with st.expander("Ver dados carregados", expanded=False):
        st.dataframe(df.head(10), use_container_width=True)

    # Mapeamento manual
    all_cols: List[str] = ["(nenhuma)"] + list(df.columns)
    num_cols: List[str] = list(df.select_dtypes(include="number").columns)

    st.subheader("Confirme ou ajuste o mapeamento")

    col1, col2 = st.columns(2)

    with col1:
        kpi_default = detected.get("kpi", {}).get("column")
        kpi_col = st.selectbox(
            "Coluna KPI (resultado a modelar)",
            options=num_cols,
            index=_safe_index(num_cols, kpi_default),
            help="Ex: vendas, receita, conversões",
        )

        date_default = detected.get("date_col", {}).get("column")
        date_col = st.selectbox(
            "Coluna de Data (opcional)",
            options=all_cols,
            index=_safe_index(all_cols, date_default),
            help="Coluna com datas semanais ou mensais",
        )

    with col2:
        spend_defaults: List[str] = detected.get("media_spend", {}).get("columns", [])
        spend_cols: List[str] = st.multiselect(
            "Colunas de Investimento (spend por canal)",
            options=num_cols,
            default=[c for c in spend_defaults if c in df.columns],
            help="Ex: gasto_tv, custo_digital, invest_radio",
        )

        impression_defaults: List[str] = detected.get("media_impressions", {}).get("columns", [])
        impression_cols: List[str] = st.multiselect(
            "Colunas de Impressões (opcional)",
            options=num_cols,
            default=[c for c in impression_defaults if c in df.columns],
            help="Ex: impressoes_tv, alcance_digital",
        )

    # Variáveis de controle — numéricas não usadas
    used_cols = set(
        [kpi_col]
        + spend_cols
        + impression_cols
        + ([date_col] if date_col != "(nenhuma)" else [])
    )
    available_controls = [c for c in num_cols if c not in used_cols]
    control_cols: List[str] = st.multiselect(
        "Variáveis de Controle (opcional)",
        options=available_controls,
        default=[],
        help="Variáveis externas que afetam o KPI (ex: sazonalidade, promoções)",
    )

    column_mapping: Dict[str, Any] = {
        "kpi": kpi_col,
        "media_spend": spend_cols,
        "media_impressions": impression_cols,
        "date_col": date_col if date_col != "(nenhuma)" else None,
        "controls": control_cols,
    }
    st.session_state["mmm_column_mapping"] = column_mapping

    st.divider()

    if st.button("Validar dados", type="primary"):
        if not spend_cols:
            st.error("Selecione pelo menos uma coluna de investimento.")
        else:
            validation = fw.validate_data(df, column_mapping)
            for err in validation.get("errors", []):
                st.error(err)
            for warn in validation.get("warnings", []):
                st.warning(warn)
            if validation.get("valid"):
                st.success("Dados válidos! Prossiga para a aba de Configuração.")
                st.session_state["mmm_data_valid"] = True
            else:
                st.session_state["mmm_data_valid"] = False


def _render_tab2_configuracao(fw: Any) -> None:
    """Aba 2 — Configuração do Modelo."""
    if not st.session_state.get("mmm_data_valid"):
        st.info("Valide os dados na aba anterior antes de configurar o modelo.")
        return

    st.subheader("Parâmetros do Modelo")

    if st.session_state.get("mmm_model"):
        if st.button("Usar modelo já treinado (em cache)"):
            st.success("Usando modelo treinado anteriormente.")

    st.info(
        "**Sobre os parâmetros:**\n"
        "- **ROI Prior (média)**: valor esperado de retorno por real investido. "
        "0.2 = espera-se R$0,20 de retorno por R$1 investido.\n"
        "- **ROI Prior (desvio)**: incerteza no prior. Valores maiores = distribuição mais ampla.\n"
        "- **Cadeias MCMC**: número de amostras independentes. Mais cadeias = mais confiável, mais lento.\n"
        "- **Adaptação/Burnin/Keep**: fases do algoritmo MCMC. Valores maiores = mais preciso, mais lento."
    )

    st.warning(
        "O treino pode levar de 10 a 60 minutos dependendo do hardware. "
        "Use GPU para melhores resultados."
    )

    col1, col2 = st.columns(2)
    with col1:
        roi_mu = st.slider(
            "ROI Prior — Média (μ)",
            min_value=-1.0,
            max_value=2.0,
            value=float(os.getenv("MERIDIAN_ROI_MU", "0.2")),
            step=0.1,
            help="Média da distribuição LogNormal do ROI prior",
        )
        n_chains = st.number_input(
            "Número de Cadeias MCMC",
            min_value=1,
            max_value=16,
            value=int(os.getenv("MERIDIAN_N_CHAINS", "4")),
        )
        n_burnin = st.number_input(
            "Burnin",
            min_value=100,
            max_value=5000,
            value=int(os.getenv("MERIDIAN_N_BURNIN", "500")),
        )

    with col2:
        roi_sigma = st.slider(
            "ROI Prior — Desvio (σ)",
            min_value=0.1,
            max_value=2.0,
            value=float(os.getenv("MERIDIAN_ROI_SIGMA", "0.9")),
            step=0.1,
            help="Desvio padrão da distribuição LogNormal do ROI prior",
        )
        n_adapt = st.number_input(
            "Adaptação",
            min_value=100,
            max_value=5000,
            value=int(os.getenv("MERIDIAN_N_ADAPT", "1000")),
        )
        n_keep = st.number_input(
            "Amostras a Manter (keep)",
            min_value=100,
            max_value=5000,
            value=int(os.getenv("MERIDIAN_N_KEEP", "500")),
        )

    model_config: Dict[str, float] = {"roi_mu": roi_mu, "roi_sigma": roi_sigma}

    if st.button("Iniciar Treino", type="primary"):
        df: pd.DataFrame = st.session_state.processed_df
        column_mapping = st.session_state.get("mmm_column_mapping", {})

        with st.spinner("Construindo dados de entrada..."):
            try:
                input_data = fw.build_input_data(df, column_mapping)
                st.success("Dados de entrada construídos.")
            except Exception as exc:
                st.error(f"Erro ao construir dados: {exc}")
                st.stop()

        with st.spinner("Configurando modelo..."):
            try:
                mmm = fw.configure_model(input_data, model_config)
                st.success("Modelo configurado.")
            except Exception as exc:
                st.error(f"Erro ao configurar modelo: {exc}")
                st.stop()

        with st.spinner("Treinando modelo (isso pode demorar vários minutos)..."):
            try:
                mmm, metadata = fw.train(
                    mmm,
                    n_chains=n_chains,
                    n_adapt=n_adapt,
                    n_burnin=n_burnin,
                    n_keep=n_keep,
                )
                st.session_state["mmm_model"] = mmm
                st.session_state["mmm_metadata"] = metadata
                st.session_state["mmm_fw"] = fw
                st.success(
                    f"Treino concluído em {metadata['tempo_segundos']:.0f} segundos!"
                )
            except Exception as exc:
                st.error(f"Erro durante o treino: {exc}")
                st.stop()


def _render_tab3_diagnosticos(fw: Any) -> None:
    """Aba 3 — Diagnósticos."""
    if not st.session_state.get("mmm_model"):
        st.info("Treine o modelo na aba anterior.")
        return

    mmm = st.session_state["mmm_model"]
    fw_active = st.session_state.get("mmm_fw", fw)

    st.subheader("Diagnóstico de Convergência")

    with st.spinner("Executando diagnóstico..."):
        health = fw_active.run_health_check(mmm)

    rhat_max: float = health.get("rhat_max", 0)

    if rhat_max < 1.05:
        cor, status_msg = "🟢", "Convergência adequada"
    elif rhat_max < 1.15:
        cor, status_msg = "🟡", "Convergência marginal — considere mais iterações"
    else:
        cor, status_msg = "🔴", "Convergência insuficiente — aumente n_burnin e n_keep"

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            f"{cor} R-hat Máximo",
            f"{rhat_max:.4f}",
            help="R-hat < 1.05 indica boa convergência",
        )
    with col2:
        st.metric("Status", status_msg)

    st.info(health.get("rhat_summary", ""))

    if health.get("warnings"):
        st.subheader("Avisos do Modelo")
        for warn in health["warnings"]:
            st.warning(warn)

    if st.button("Gerar Resultados →", type="primary"):
        with st.spinner("Extraindo resultados..."):
            results = fw_active.generate_results(mmm)
            st.session_state["mmm_results"] = results
        st.success("Resultados gerados! Acesse a aba 4.")


def _render_tab4_resultados(fw: Any) -> None:
    """Aba 4 — Resultados & Otimização."""
    if not st.session_state.get("mmm_results"):
        st.info("Execute o diagnóstico e gere os resultados na aba anterior.")
        return

    results: Dict[str, Any] = st.session_state["mmm_results"]
    fw_active = st.session_state.get("mmm_fw", fw)
    mmm = st.session_state.get("mmm_model")
    metadata: Dict[str, Any] = st.session_state.get("mmm_metadata", {})

    # --- ROI por canal ---
    st.subheader("ROI por Canal de Mídia")
    roi_data: Dict[str, Any] = results.get("roi_by_channel", {})

    if roi_data:
        cols = st.columns(min(len(roi_data), 4))
        for i, (canal, roi_info) in enumerate(roi_data.items()):
            with cols[i % 4]:
                mean_val = roi_info.get("mean", 0)
                st.metric(
                    label=canal,
                    value=f"R$ {mean_val:.2f}",
                    delta=(
                        f"IC 90%: [{roi_info.get('lower', 0):.2f}, "
                        f"{roi_info.get('upper', 0):.2f}]"
                    ),
                )

    # --- Gráficos ---
    charts = fw_active.generate_charts(results)

    st.subheader("ROI por Canal — Intervalo de Credibilidade 90%")
    if charts.get("roi_chart"):
        st.plotly_chart(charts["roi_chart"], use_container_width=True)

    st.subheader("Contribuição para o KPI")
    if charts.get("contribution_chart"):
        st.plotly_chart(charts["contribution_chart"], use_container_width=True)

    # --- Otimização de Budget ---
    st.divider()
    st.subheader("Otimização de Budget")

    default_budget = float(sum(v.get("mean", 0) for v in roi_data.values()) * 1000)
    total_budget = st.number_input(
        "Budget total disponível (R$)",
        min_value=0.0,
        value=default_budget,
        step=1000.0,
        help="Valor total que deseja distribuir entre os canais",
    )

    st.write("**Restrições por canal (opcional):**")
    constraints: Dict[str, Dict[str, float]] = {}
    if roi_data:
        constraint_cols = st.columns(min(len(roi_data), 3))
        for i, canal in enumerate(roi_data.keys()):
            with constraint_cols[i % 3]:
                st.write(f"**{canal}**")
                min_val = st.number_input(
                    f"Mínimo — {canal}", min_value=0.0, value=0.0, key=f"min_{canal}"
                )
                max_val = st.number_input(
                    f"Máximo — {canal}",
                    min_value=0.0,
                    value=total_budget,
                    key=f"max_{canal}",
                )
                constraints[canal] = {"min": min_val, "max": max_val}

    if st.button("Otimizar Budget", type="primary") and mmm:
        with st.spinner("Rodando otimização..."):
            try:
                opt_results = fw_active.run_optimization(mmm, total_budget, constraints)
                st.session_state["mmm_optimization"] = opt_results

                st.success(
                    f"Otimização concluída! Lift esperado: "
                    f"{opt_results.get('expected_kpi_lift', 0):.1%}"
                )

                opt_df = pd.DataFrame(
                    {
                        "Canal": list(opt_results["current_budget"].keys()),
                        "Budget Atual": list(opt_results["current_budget"].values()),
                        "Budget Otimizado": list(opt_results["optimized_budget"].values()),
                        "Delta": list(opt_results["budget_delta"].values()),
                    }
                )
                st.dataframe(opt_df, use_container_width=True)

                opt_charts = fw_active.generate_charts(results, opt_results)
                if opt_charts.get("optimization_chart"):
                    st.plotly_chart(opt_charts["optimization_chart"], use_container_width=True)

            except Exception as exc:
                st.error(f"Erro na otimização: {exc}")

    # --- Exportação ---
    st.divider()
    st.subheader("Exportar Relatório")

    if st.button("Gerar Relatório HTML"):
        with st.spinner("Gerando relatório..."):
            opt_results = st.session_state.get("mmm_optimization")
            html_content: str = fw_active.generate_html_report(
                results, charts, opt_results, metadata
            )

            report_id = str(uuid.uuid4())
            report_path = Path(PUBLISHED_REPORTS_DIR) / f"{report_id}.html"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(html_content, encoding="utf-8")

            st.success(f"Relatório salvo em: `{report_path}`")
            st.download_button(
                "Baixar HTML",
                data=html_content.encode("utf-8"),
                file_name=f"mmm_report_{report_id[:8]}.html",
                mime="text/html",
            )


def render() -> None:
    """Ponto de entrada da página Meridian."""
    st.title("Media Mix Model (Meridian)")

    if not MERIDIAN_AVAILABLE:
        st.error(
            "**Meridian não está instalado.**\n\n"
            "Execute: `pip install google-meridian[schema] tensorflow tensorflow-probability`"
        )
        return

    fw = MeridianFramework()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "1️⃣ Mapeamento de Colunas",
            "2️⃣ Configuração do Modelo",
            "3️⃣ Diagnósticos",
            "4️⃣ Resultados & Otimização",
        ]
    )

    with tab1:
        _render_tab1_mapeamento(fw)

    with tab2:
        _render_tab2_configuracao(fw)

    with tab3:
        _render_tab3_diagnosticos(fw)

    with tab4:
        _render_tab4_resultados(fw)


render()
