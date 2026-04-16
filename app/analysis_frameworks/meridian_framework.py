"""Framework de Media Mix Modeling usando Google Meridian."""

# Stdlib
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Third-party
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Import opcional do Meridian (requer TF e GPU)
try:
    from meridian.model import model as meridian_model
    from meridian.model import spec
    from meridian.model import prior_distribution
    from meridian.analysis import analyzer as meridian_analyzer
    from meridian.analysis import optimizer as meridian_optimizer
    from meridian.analysis import summarizer as meridian_summarizer
    from meridian.analysis.review import reviewer as meridian_reviewer
    from meridian.data import data_frame_input_data_builder
    import tensorflow_probability as tfp
    MERIDIAN_AVAILABLE = True
except ImportError:
    MERIDIAN_AVAILABLE = False

# Local
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Paleta de cores do projeto
_COR_PRIMARIA = "#4f46e5"
_COR_SUCESSO = "#10b981"
_COR_AVISO = "#f59e0b"


class MeridianFramework:
    """Framework de Media Mix Modeling usando Google Meridian."""

    # Palavras-chave para detecção de colunas
    _KPI_KEYWORDS = [
        "sales", "revenue", "conversions", "vendas", "receita", "kpi",
        "resultado", "venda", "conversion",
    ]
    _SPEND_KEYWORDS = [
        "spend", "cost", "invest", "gasto", "custo", "budget",
        "investimento", "orcamento",
    ]
    _IMPRESSION_KEYWORDS = [
        "impression", "impressao", "impressão", "view", "reach", "click",
        "alcance", "visualizacao", "visualização", "clique",
    ]
    _DATE_KEYWORDS = [
        "date", "data", "week", "period", "semana", "mes", "mês", "ano",
        "periodo", "período", "dt_", "_dt", "data_",
    ]

    # ------------------------------------------------------------------
    # Detecção automática de colunas
    # ------------------------------------------------------------------

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detecta automaticamente colunas relevantes para MMM no DataFrame.

        Args:
            df: DataFrame com os dados brutos.

        Returns:
            Dicionário com colunas detectadas e confiança de cada categoria.
        """
        num_cols = df.select_dtypes(include="number").columns.tolist()
        all_cols = df.columns.tolist()

        assigned: set = set()

        def _match(col: str, keywords: List[str]) -> float:
            col_lower = col.lower()
            for kw in keywords:
                if col_lower == kw:
                    return 1.0
            for kw in keywords:
                if kw in col_lower:
                    return 0.7
            return 0.0

        # KPI: primeira coluna numérica que bate nas keywords
        kpi_col: Optional[str] = None
        kpi_conf = 0.0
        for col in num_cols:
            conf = _match(col, self._KPI_KEYWORDS)
            if conf > 0:
                kpi_col = col
                kpi_conf = conf
                assigned.add(col)
                break

        # Data: primeira coluna (qualquer tipo) que bate nas keywords
        date_col: Optional[str] = None
        date_conf = 0.0
        for col in all_cols:
            conf = _match(col, self._DATE_KEYWORDS)
            if conf > 0:
                date_col = col
                date_conf = conf
                assigned.add(col)
                break

        # Spend: todas colunas numéricas não usadas que batem em spend
        spend_cols: List[str] = []
        spend_conf = 0.0
        for col in num_cols:
            if col in assigned:
                continue
            conf = _match(col, self._SPEND_KEYWORDS)
            if conf > 0:
                spend_cols.append(col)
                spend_conf = max(spend_conf, conf)
                assigned.add(col)

        # Impressions: todas colunas numéricas não usadas que batem em impressions
        imp_cols: List[str] = []
        imp_conf = 0.0
        for col in num_cols:
            if col in assigned:
                continue
            conf = _match(col, self._IMPRESSION_KEYWORDS)
            if conf > 0:
                imp_cols.append(col)
                imp_conf = max(imp_conf, conf)
                assigned.add(col)

        # Controls: colunas numéricas restantes
        control_cols = [c for c in num_cols if c not in assigned]

        has_minimum = kpi_col is not None and len(spend_cols) > 0

        if has_minimum:
            msg = (
                f"Colunas detectadas: KPI='{kpi_col}', "
                f"{len(spend_cols)} canal(is) de investimento, "
                f"{len(imp_cols)} coluna(s) de impressões, "
                f"{len(control_cols)} variável(is) de controle."
            )
        else:
            partes = []
            if kpi_col is None:
                partes.append("KPI não detectado")
            if not spend_cols:
                partes.append("nenhum canal de investimento detectado")
            msg = (
                "Mapeamento incompleto: " + "; ".join(partes) + ". "
                "Mapeie as colunas manualmente antes de treinar o modelo."
            )

        return {
            "kpi": {"column": kpi_col, "confidence": kpi_conf},
            "media_spend": {"columns": spend_cols, "confidence": spend_conf},
            "media_impressions": {"columns": imp_cols, "confidence": imp_conf},
            "date_col": {"column": date_col, "confidence": date_conf},
            "controls": {"columns": control_cols, "confidence": 1.0},
            "message": msg,
            "has_minimum_columns": has_minimum,
        }

    # ------------------------------------------------------------------
    # Validação de dados
    # ------------------------------------------------------------------

    def validate_data(
        self, df: pd.DataFrame, column_mapping: Dict
    ) -> Dict[str, Any]:
        """
        Valida o DataFrame e o mapeamento de colunas para uso no MMM.

        Args:
            df: DataFrame com os dados.
            column_mapping: Dicionário com keys kpi, media_spend, media_impressions,
                date_col e controls.

        Returns:
            Dicionário com listas de erros, avisos e flag de validade.
        """
        errors: List[str] = []
        warnings_list: List[str] = []

        n_rows = len(df)

        # Linhas insuficientes
        if n_rows < 52:
            errors.append(
                f"Dados insuficientes: {n_rows} linhas. "
                "Mínimo recomendado: 52 semanas."
            )
        elif n_rows < 104:
            warnings_list.append(
                "Recomendamos pelo menos 104 semanas (2 anos) para resultados robustos."
            )

        # Canais de mídia insuficientes
        spend_cols = column_mapping.get("media_spend") or []
        if isinstance(spend_cols, str):
            spend_cols = [spend_cols]
        if len(spend_cols) < 3:
            warnings_list.append(
                f"Poucos canais de mídia ({len(spend_cols)}). "
                "Recomendamos pelo menos 3."
            )

        def _as_list(val) -> List[str]:
            """Normaliza um valor de mapeamento para lista de strings."""
            if not val:
                return []
            return [val] if isinstance(val, str) else list(val)

        all_mapped = (
            _as_list(column_mapping.get("kpi"))
            + spend_cols
            + _as_list(column_mapping.get("media_impressions"))
            + _as_list(column_mapping.get("date_col"))
            + _as_list(column_mapping.get("controls"))
        )

        for col in all_mapped:
            if not col:
                continue
            if col not in df.columns:
                errors.append(f"Coluna '{col}' não encontrada no dataset.")
                continue
            null_pct = df[col].isna().mean()
            if null_pct > 0.20:
                errors.append(
                    f"Coluna '{col}' tem {null_pct:.0%} de valores nulos (máximo: 20%)."
                )

        # KPI sem negativos
        kpi_col = column_mapping.get("kpi")
        if kpi_col and kpi_col in df.columns:
            if (df[kpi_col] < 0).any():
                errors.append(
                    f"KPI '{kpi_col}' contém valores negativos. "
                    "MMM requer KPI não-negativo."
                )

        # Spend sem negativos
        for col in spend_cols:
            if col in df.columns and (df[col] < 0).any():
                errors.append(
                    f"Canal '{col}' contém valores negativos de investimento."
                )

        return {
            "errors": errors,
            "warnings": warnings_list,
            "valid": len(errors) == 0,
        }

    # ------------------------------------------------------------------
    # Construção de dados de entrada
    # ------------------------------------------------------------------

    def build_input_data(
        self,
        df: pd.DataFrame,
        column_mapping: Dict,
        kpi_type: str = "non_revenue",
    ) -> Any:
        """
        Constrói o objeto InputData do Meridian a partir do DataFrame.

        Args:
            df: DataFrame com os dados.
            column_mapping: Mapeamento de colunas.
            kpi_type: Tipo de KPI ('non_revenue' ou 'revenue').

        Returns:
            Objeto InputData do Meridian.

        Raises:
            ImportError: Se o Meridian não estiver instalado.
            ValueError: Se houver erro na construção dos dados.
        """
        if not MERIDIAN_AVAILABLE:
            raise ImportError(
                "O pacote Google Meridian não está instalado. "
                "Instale com: pip install google-meridian"
            )

        impressions = column_mapping.get("media_impressions")
        controls = column_mapping.get("controls")

        try:
            builder = data_frame_input_data_builder.DataFrameInputDataBuilder(
                kpi=df[column_mapping["kpi"]],
                kpi_type=kpi_type,
                media_spend=df[column_mapping["media_spend"]],
                media=df[impressions] if impressions else None,
                controls=df[controls] if controls else None,
                revenue_per_kpi=None,
            )
            return builder.build()
        except Exception as exc:
            raise ValueError(
                f"Erro ao construir dados de entrada: {exc}. "
                "Verifique o mapeamento de colunas."
            ) from exc

    # ------------------------------------------------------------------
    # Configuração do modelo
    # ------------------------------------------------------------------

    def configure_model(self, input_data: Any, config: Dict) -> Any:
        """
        Configura e retorna uma instância do modelo Meridian.

        Args:
            input_data: Objeto InputData do Meridian.
            config: Dicionário com roi_mu e roi_sigma.

        Returns:
            Instância do modelo Meridian.
        """
        roi_prior = prior_distribution.PriorDistribution(
            roi=tfp.distributions.LogNormal(
                loc=config.get("roi_mu", 0.2),
                scale=config.get("roi_sigma", 0.9),
            )
        )
        model_spec = spec.ModelSpec(prior=roi_prior, enable_aks=True)
        mmm = meridian_model.Meridian(input_data=input_data, model_spec=model_spec)
        return mmm

    # ------------------------------------------------------------------
    # Treinamento
    # ------------------------------------------------------------------

    def train(
        self,
        mmm: Any,
        n_chains: int = 4,
        n_adapt: int = 1000,
        n_burnin: int = 500,
        n_keep: int = 500,
    ) -> Tuple[Any, Dict]:
        """
        Executa amostragem prior e posterior no modelo Meridian.

        Args:
            mmm: Instância do modelo Meridian.
            n_chains: Número de cadeias MCMC.
            n_adapt: Passos de adaptação.
            n_burnin: Passos de burnin.
            n_keep: Amostras a manter.

        Returns:
            Tupla (mmm, metadados do treinamento).
        """
        start = datetime.now()

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning, module="tensorflow")
            warnings.filterwarnings("ignore", category=UserWarning, module="arviz")
            warnings.filterwarnings("ignore", message=".*divergence.*")
            warnings.filterwarnings("ignore", message=".*convergence.*")

            mmm.sample_prior(500)
            mmm.sample_posterior(
                n_chains=n_chains,
                n_adapt=n_adapt,
                n_burnin=n_burnin,
                n_keep=n_keep,
            )

        elapsed = (datetime.now() - start).total_seconds()
        logger.info("Treinamento concluído em %.1f segundos.", elapsed)

        metadata = {
            "tempo_segundos": elapsed,
            "n_chains": n_chains,
            "n_adapt": n_adapt,
            "n_burnin": n_burnin,
            "n_keep": n_keep,
            "timestamp": datetime.now().isoformat(),
        }
        return mmm, metadata

    # ------------------------------------------------------------------
    # Diagnóstico de convergência
    # ------------------------------------------------------------------

    def run_health_check(self, mmm: Any) -> Dict[str, Any]:
        """
        Executa verificação de saúde do modelo (diagnóstico de convergência).

        Args:
            mmm: Modelo treinado.

        Returns:
            Dicionário com métricas de convergência e avisos.
        """
        reviewer = meridian_reviewer.ModelReviewer(mmm)
        review_result = reviewer.run()

        # Extrai R-hat values
        rhat_values: List[float] = []
        health_warnings: List[str] = []

        try:
            if hasattr(review_result, "rhat"):
                rhat_raw = review_result.rhat
                if hasattr(rhat_raw, "values"):
                    rhat_values = [float(v) for v in rhat_raw.values.flatten() if not np.isnan(v)]
                elif isinstance(rhat_raw, (list, np.ndarray)):
                    rhat_values = [float(v) for v in np.array(rhat_raw).flatten() if not np.isnan(v)]

            if hasattr(review_result, "warnings") and review_result.warnings:
                health_warnings = [str(w) for w in review_result.warnings]
        except Exception as exc:
            logger.warning("Erro ao extrair métricas de convergência: %s", exc)

        rhat_max = max(rhat_values) if rhat_values else float("nan")
        convergiu = rhat_max < 1.05 if rhat_values else False

        return {
            "convergiu": convergiu,
            "rhat_max": float(rhat_max),
            "rhat_summary": (
                f"R-hat máximo: {rhat_max:.4f} "
                f"({'Convergência adequada' if convergiu else 'Verificar convergência'})"
            ),
            "warnings": health_warnings,
        }

    # ------------------------------------------------------------------
    # Extração de resultados
    # ------------------------------------------------------------------

    def generate_results(
        self,
        mmm: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extrai ROI, contribuição por canal e ajuste do modelo.

        Args:
            mmm: Modelo treinado.
            start_date: Data inicial do período de análise (opcional).
            end_date: Data final do período de análise (opcional).

        Returns:
            Dicionário com métricas de resultados.
        """
        roi_by_channel: Dict[str, Dict] = {}
        contribution_by_channel: Dict[str, float] = {}
        baseline_contribution: Optional[float] = None
        total_decomp: Dict = {}
        model_fit_r2: Optional[float] = None

        try:
            summarizer = meridian_summarizer.Summarizer(mmm)
            analyzer = meridian_analyzer.Analyzer(mmm)

            # ROI por canal
            roi_summary = summarizer.roi_summary()
            if hasattr(roi_summary, "mean"):
                for canal, mean_val in roi_summary.mean.items():
                    lower = roi_summary.ci_lo.get(canal, mean_val)
                    upper = roi_summary.ci_hi.get(canal, mean_val)
                    roi_by_channel[str(canal)] = {
                        "mean": float(mean_val),
                        "lower": float(lower),
                        "upper": float(upper),
                    }

            # Contribuição percentual
            decomp = analyzer.revenue_decomposition(
                start_date=start_date, end_date=end_date
            )
            total_decomp = decomp
            total_val = sum(float(v) for v in decomp.values()) if decomp else 1.0

            for canal, val in decomp.items():
                fval = float(val)
                if str(canal).lower() in ("baseline", "intercept", "base"):
                    baseline_contribution = fval / total_val * 100 if total_val else 0.0
                else:
                    contribution_by_channel[str(canal)] = fval / total_val * 100 if total_val else 0.0

            # R² do modelo
            try:
                model_fit_r2 = float(summarizer.model_fit().r_squared)
            except Exception:
                pass

        except Exception as exc:
            logger.warning("Erro ao extrair resultados do modelo: %s", exc)

        return {
            "roi_by_channel": roi_by_channel,
            "contribution_by_channel": contribution_by_channel,
            "baseline_contribution": baseline_contribution,
            "total_revenue_decomposition": total_decomp,
            "model_fit_r2": model_fit_r2,
        }

    # ------------------------------------------------------------------
    # Otimização de budget
    # ------------------------------------------------------------------

    def run_optimization(
        self, mmm: Any, total_budget: float, constraints: Dict
    ) -> Dict[str, Any]:
        """
        Otimiza alocação de budget entre canais usando o Meridian.

        Args:
            mmm: Modelo treinado.
            total_budget: Budget total disponível.
            constraints: Dicionário {canal: {"min": float, "max": float}}.

        Returns:
            Dicionário com budget otimizado, atual, lift esperado e delta.
        """
        optimizer = meridian_optimizer.BudgetOptimizer(mmm)

        min_bounds = {canal: v.get("min", 0.0) for canal, v in constraints.items()}
        max_bounds = {canal: v.get("max", total_budget) for canal, v in constraints.items()}

        opt_result = optimizer.optimize(
            budget=total_budget,
            min_spend=min_bounds,
            max_spend=max_bounds,
        )

        optimized: Dict[str, float] = {}
        current: Dict[str, float] = {}

        if hasattr(opt_result, "optimized_spend"):
            for canal, val in opt_result.optimized_spend.items():
                optimized[str(canal)] = float(val)
        if hasattr(opt_result, "current_spend"):
            for canal, val in opt_result.current_spend.items():
                current[str(canal)] = float(val)

        expected_lift = float(getattr(opt_result, "expected_kpi_lift", 0.0))

        budget_delta = {
            canal: optimized.get(canal, 0.0) - current.get(canal, 0.0)
            for canal in set(list(optimized.keys()) + list(current.keys()))
        }

        return {
            "optimized_budget": optimized,
            "current_budget": current,
            "expected_kpi_lift": expected_lift,
            "budget_delta": budget_delta,
        }

    # ------------------------------------------------------------------
    # Gráficos
    # ------------------------------------------------------------------

    def generate_charts(
        self,
        results: Dict,
        optimization_results: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Gera gráficos Plotly para ROI, contribuição e otimização.

        Args:
            results: Saída de generate_results().
            optimization_results: Saída de run_optimization() (opcional).

        Returns:
            Dicionário com figuras Plotly.
        """
        roi_chart = self._make_roi_chart(results.get("roi_by_channel", {}))
        contribution_chart = self._make_contribution_chart(
            results.get("contribution_by_channel", {}),
            results.get("baseline_contribution"),
        )
        optimization_chart = (
            self._make_optimization_chart(optimization_results)
            if optimization_results
            else None
        )
        response_curves = self._make_response_curves_placeholder()

        return {
            "roi_chart": roi_chart,
            "contribution_chart": contribution_chart,
            "optimization_chart": optimization_chart,
            "response_curves": response_curves,
        }

    def _make_roi_chart(self, roi_by_channel: Dict) -> go.Figure:
        """Gráfico de barras horizontais com intervalo de credibilidade para ROI."""
        if not roi_by_channel:
            fig = go.Figure()
            fig.add_annotation(
                text="Dados de ROI não disponíveis",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(title="ROI por Canal de Mídia")
            return fig

        canais = list(roi_by_channel.keys())
        means = [roi_by_channel[c]["mean"] for c in canais]
        lowers = [roi_by_channel[c]["lower"] for c in canais]
        uppers = [roi_by_channel[c]["upper"] for c in canais]
        error_minus = [m - l for m, l in zip(means, lowers)]
        error_plus = [u - m for m, u in zip(means, uppers)]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=canais,
                x=means,
                orientation="h",
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=error_plus,
                    arrayminus=error_minus,
                    color=_COR_AVISO,
                ),
                marker_color=_COR_PRIMARIA,
                name="ROI médio",
            )
        )
        fig.update_layout(
            title="ROI por Canal de Mídia (IC 90%)",
            xaxis_title="Retorno sobre Investimento (ROI)",
            yaxis_title="Canal",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter, sans-serif"),
        )
        return fig

    def _make_contribution_chart(
        self,
        contribution_by_channel: Dict,
        baseline: Optional[float],
    ) -> go.Figure:
        """Donut chart com contribuição percentual por canal e baseline."""
        labels: List[str] = []
        values: List[float] = []

        if baseline is not None:
            labels.append("Baseline")
            values.append(baseline)

        for canal, pct in contribution_by_channel.items():
            labels.append(canal)
            values.append(pct)

        if not values:
            fig = go.Figure()
            fig.add_annotation(
                text="Dados de contribuição não disponíveis",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(title="Contribuição por Canal")
            return fig

        # Baseline recebe cor de destaque; canais de mídia recebem cor primária
        colors = (
            [_COR_AVISO] + [_COR_PRIMARIA] * (len(labels) - 1)
            if baseline is not None
            else [_COR_PRIMARIA] * len(labels)
        )

        fig = go.Figure(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors,
            )
        )
        fig.update_layout(
            title="Contribuição Percentual por Canal",
            font=dict(family="Inter, sans-serif"),
        )
        return fig

    def _make_optimization_chart(self, optimization_results: Dict) -> go.Figure:
        """Grouped bar chart comparando budget atual vs otimizado."""
        current = optimization_results.get("current_budget", {})
        optimized = optimization_results.get("optimized_budget", {})
        canais = sorted(set(list(current.keys()) + list(optimized.keys())))

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="Budget Atual",
                x=canais,
                y=[current.get(c, 0.0) for c in canais],
                marker_color=_COR_PRIMARIA,
            )
        )
        fig.add_trace(
            go.Bar(
                name="Budget Otimizado",
                x=canais,
                y=[optimized.get(c, 0.0) for c in canais],
                marker_color=_COR_SUCESSO,
            )
        )
        fig.update_layout(
            barmode="group",
            title="Comparativo: Budget Atual vs Otimizado",
            xaxis_title="Canal",
            yaxis_title="Investimento (R$)",
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter, sans-serif"),
        )
        return fig

    def _make_response_curves_placeholder(self) -> go.Figure:
        """Placeholder para curvas de resposta."""
        fig = go.Figure()
        fig.add_annotation(
            text=(
                "Curvas de resposta serão geradas após treinamento completo do modelo. "
                "Execute o treinamento com pelo menos 500 amostras posterior."
            ),
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#6b7280"),
            align="center",
        )
        fig.update_layout(
            title="Curvas de Resposta por Canal",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor="#f9fafb",
            paper_bgcolor="#f9fafb",
            font=dict(family="Inter, sans-serif"),
        )
        return fig

    # ------------------------------------------------------------------
    # Relatório HTML
    # ------------------------------------------------------------------

    def generate_html_report(
        self,
        results: Dict,
        charts: Dict,
        optimization_results: Optional[Dict],
        metadata: Dict,
    ) -> str:
        """
        Gera relatório HTML completo e autocontido do MMM.

        Args:
            results: Saída de generate_results().
            charts: Saída de generate_charts().
            optimization_results: Saída de run_optimization() (opcional).
            metadata: Metadados do treinamento (timestamp, etc.).

        Returns:
            String HTML completa.
        """

        def _fig_to_html(fig: Optional[go.Figure]) -> str:
            if fig is None:
                return "<p><em>Não disponível.</em></p>"
            return fig.to_html(include_plotlyjs="cdn", full_html=False)

        roi_html = _fig_to_html(charts.get("roi_chart"))
        contribution_html = _fig_to_html(charts.get("contribution_chart"))
        optimization_html = _fig_to_html(charts.get("optimization_chart"))
        response_html = _fig_to_html(charts.get("response_curves"))

        # Sumário executivo — tabela ROI
        roi_rows = "".join(
            f"<tr>"
            f"<td>{canal}</td>"
            f"<td>{dados['mean']:.2f}</td>"
            f"<td>{dados['lower']:.2f} \u2013 {dados['upper']:.2f}</td>"
            f"</tr>\n"
            for canal, dados in results.get("roi_by_channel", {}).items()
        )

        r2_val = results.get("model_fit_r2")
        r2_text = f"{r2_val:.4f}" if r2_val is not None else "N/D"
        timestamp = metadata.get("timestamp", datetime.now().isoformat())
        n_keep = metadata.get("n_keep", "N/D")
        n_chains = metadata.get("n_chains", "N/D")
        tempo = metadata.get("tempo_segundos")
        tempo_text = f"{tempo:.1f}s" if tempo is not None else "N/D"

        opt_section = ""
        if optimization_results:
            lift = optimization_results.get("expected_kpi_lift", 0.0)
            opt_section = f"""
            <section class="section">
                <h2>Otimização de Budget</h2>
                <p>Lift esperado no KPI com alocação otimizada:
                   <strong>{lift:.1%}</strong></p>
                {optimization_html}
            </section>
            """

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Relatório Media Mix Modeling</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
        rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', sans-serif;
      background: #f3f4f6;
      color: #111827;
      line-height: 1.6;
    }}
    header {{
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: #fff;
      padding: 2.5rem 2rem 2rem;
    }}
    header h1 {{ font-size: 2rem; font-weight: 700; }}
    header p  {{ opacity: 0.85; margin-top: 0.4rem; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 2rem 1rem; }}
    .section {{
      background: #fff;
      border-radius: 12px;
      padding: 1.75rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }}
    .section h2 {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #4f46e5;
      margin-bottom: 1rem;
      border-bottom: 2px solid #e0e7ff;
      padding-bottom: 0.5rem;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }}
    .meta-card {{
      background: #f0f4ff;
      border-radius: 8px;
      padding: 0.75rem 1rem;
    }}
    .meta-card .label {{ font-size: 0.75rem; color: #6b7280; text-transform: uppercase; }}
    .meta-card .value {{ font-size: 1.1rem; font-weight: 600; color: #4f46e5; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 0.75rem;
    }}
    th {{
      background: #4f46e5;
      color: #fff;
      padding: 0.6rem 0.9rem;
      text-align: left;
      font-size: 0.85rem;
    }}
    td {{
      padding: 0.55rem 0.9rem;
      border-bottom: 1px solid #e5e7eb;
      font-size: 0.9rem;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f9fafb; }}
    footer {{
      text-align: center;
      padding: 1.5rem;
      color: #9ca3af;
      font-size: 0.8rem;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Relatório Media Mix Modeling</h1>
    <p>Análise gerada pelo Report Generator &mdash; Google Meridian</p>
  </header>

  <div class="container">

    <!-- Sumário executivo -->
    <section class="section">
      <h2>Sumário Executivo</h2>
      <div class="meta-grid">
        <div class="meta-card">
          <div class="label">Data de geração</div>
          <div class="value">{timestamp[:10]}</div>
        </div>
        <div class="meta-card">
          <div class="label">Amostras posteriores</div>
          <div class="value">{n_keep}</div>
        </div>
        <div class="meta-card">
          <div class="label">Cadeias MCMC</div>
          <div class="value">{n_chains}</div>
        </div>
        <div class="meta-card">
          <div class="label">Tempo de treinamento</div>
          <div class="value">{tempo_text}</div>
        </div>
        <div class="meta-card">
          <div class="label">R² do modelo</div>
          <div class="value">{r2_text}</div>
        </div>
      </div>
    </section>

    <!-- ROI por canal -->
    <section class="section">
      <h2>ROI por Canal de Mídia</h2>
      {"<table><thead><tr><th>Canal</th><th>ROI Médio</th><th>IC 90%</th></tr></thead><tbody>" + roi_rows + "</tbody></table>" if roi_rows else "<p><em>ROI não disponível.</em></p>"}
    </section>

    <!-- Gráfico ROI -->
    <section class="section">
      <h2>Visualização do ROI</h2>
      {roi_html}
    </section>

    <!-- Contribuição -->
    <section class="section">
      <h2>Contribuição por Canal</h2>
      {contribution_html}
    </section>

    <!-- Curvas de resposta -->
    <section class="section">
      <h2>Curvas de Resposta</h2>
      {response_html}
    </section>

    {opt_section}

    <footer>
      Relatório gerado automaticamente pelo Report Generator &bull;
      Powered by Google Meridian &bull; {timestamp[:10]}
    </footer>
  </div>
</body>
</html>"""

        return html
