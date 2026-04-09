"""Framework Comparação Temporal: Tendência → Crescimento → Sazonalidade."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks.base_framework import BaseFramework


class TemporalFramework(BaseFramework):
    """
    Framework de Comparação Temporal.

    Analisa tendências, taxas de crescimento e padrões de sazonalidade
    com base em colunas de data e métricas numéricas.
    """

    def analyze(self) -> Dict[str, Any]:
        """Executa análise temporal e retorna seções estruturadas."""
        result = {}
        num_cols = self._get_numeric_cols()
        date_cols = self._get_date_cols()

        if not self._has_enough_data():
            return {
                "tendencia": self._build_section(
                    "Tendência — Dados insuficientes",
                    "Dataset com menos de 5 registros — análise temporal não aplicável.",
                    self.df, "table", "", "", "Dados",
                )
            }

        if not date_cols:
            return {
                "tendencia": self._build_section(
                    "Tendência — Sem coluna de data",
                    "Nenhuma coluna de data detectada. Para análise temporal, o dataset precisa conter uma coluna no formato de data (ex: YYYY-MM-DD, DD/MM/YYYY).",
                    self.df, "table", "", "", "Dados",
                )
            }

        date_col = date_cols[0]

        if not num_cols:
            return {
                "tendencia": self._build_section(
                    "Tendência — Sem métricas",
                    "Sem colunas numéricas para análise temporal.",
                    self.df, "table", "", "", "Dados",
                )
            }

        main_num = num_cols[0]

        # Criar série temporal agrupada por mês
        df_time = self.df[[date_col, main_num]].dropna().copy()
        df_time["periodo"] = df_time[date_col].dt.to_period("M").astype(str)
        monthly = df_time.groupby("periodo")[main_num].sum().reset_index()
        monthly = monthly.sort_values("periodo")

        if len(monthly) < 2:
            return {
                "tendencia": self._build_section(
                    "Tendência — Período insuficiente",
                    "Apenas 1 período detectado. Análise temporal requer ao menos 2 períodos.",
                    monthly, "table", "", "", "Dados mensais",
                )
            }

        # TENDÊNCIA
        first_val = monthly[main_num].iloc[0]
        last_val = monthly[main_num].iloc[-1]
        overall_growth = ((last_val - first_val) / first_val * 100) if first_val > 0 else 0
        n_periods = len(monthly)

        tend_text = (
            f"Tendência de '{main_num}' em {n_periods} períodos: "
            f"saiu de {first_val:,.2f} (período inicial) para {last_val:,.2f} (período mais recente). "
            f"Variação total: {'+'if overall_growth >= 0 else ''}{overall_growth:.1f}%. "
        )
        if overall_growth > 10:
            tend_text += "Tendência de crescimento clara no período analisado."
        elif overall_growth < -10:
            tend_text += "Tendência de queda clara no período analisado."
        else:
            tend_text += "Tendência estável — sem variação expressiva no período."

        result["tendencia"] = self._build_section(
            "Tendência — Evolução Temporal",
            tend_text,
            monthly,
            "line", "periodo", main_num,
            f"Evolução de {main_num} ao longo do tempo",
            "sum",
        )

        # CRESCIMENTO: Variação mês a mês
        monthly["crescimento_pct"] = monthly[main_num].pct_change() * 100
        growth_df = monthly.dropna(subset=["crescimento_pct"])

        best_period = growth_df.loc[growth_df["crescimento_pct"].idxmax()]
        worst_period = growth_df.loc[growth_df["crescimento_pct"].idxmin()]
        avg_growth = growth_df["crescimento_pct"].mean()

        growth_text = (
            f"Crescimento médio mensal: {'+'if avg_growth >= 0 else ''}{avg_growth:.1f}%. "
            f"Melhor período: {best_period['periodo']} (+{best_period['crescimento_pct']:.1f}%). "
            f"Pior período: {worst_period['periodo']} ({worst_period['crescimento_pct']:.1f}%). "
        )
        if avg_growth > 5:
            growth_text += "Crescimento consistente e acima de 5% ao mês — expansão expressiva."
        elif avg_growth > 0:
            growth_text += "Crescimento positivo moderado no período."
        else:
            growth_text += "Crescimento médio negativo — período de retração."

        result["crescimento"] = self._build_section(
            "Crescimento — Variação Período a Período",
            growth_text,
            growth_df,
            "bar", "periodo", "crescimento_pct",
            "Crescimento % Mês a Mês",
            "mean",
        )

        # SAZONALIDADE: Padrão por mês do ano (se dados suficientes)
        df_time["mes"] = df_time[date_col].dt.month
        seasonal = df_time.groupby("mes")[main_num].mean().reset_index()
        seasonal.columns = ["mes", "media"]
        mes_names = {
            1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
            5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
            9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
        }
        seasonal["mes_nome"] = seasonal["mes"].map(mes_names)

        if len(seasonal) >= 3:
            peak_month = seasonal.loc[seasonal["media"].idxmax()]
            low_month = seasonal.loc[seasonal["media"].idxmin()]
            amplitude = ((peak_month["media"] - low_month["media"]) / max(low_month["media"], 0.01) * 100)

            sazon_text = (
                f"Sazonalidade: pico em {peak_month['mes_nome']} "
                f"(média {peak_month['media']:,.2f}) e vale em "
                f"{low_month['mes_nome']} (média {low_month['media']:,.2f}). "
                f"Amplitude sazonal de {amplitude:.0f}%. "
            )
            if amplitude > 50:
                sazon_text += "Sazonalidade forte — planejamento por período é essencial."
            elif amplitude > 20:
                sazon_text += "Sazonalidade moderada — considerar ajustes por período."
            else:
                sazon_text += "Padrão relativamente estável ao longo dos meses."
        else:
            sazon_text = (
                f"Dataset cobre apenas {len(seasonal)} mês(es). "
                "Para análise de sazonalidade confiável, são necessários dados de ao menos 12 meses."
            )

        result["sazonalidade"] = self._build_section(
            "Sazonalidade — Padrão por Período",
            sazon_text,
            seasonal,
            "line", "mes_nome", "media",
            f"Média de {main_num} por Mês",
            "mean",
        )

        return result
