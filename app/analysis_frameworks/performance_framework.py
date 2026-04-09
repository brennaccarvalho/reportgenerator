"""Framework Diagnóstico de Performance: Volume → Eficiência → Qualidade."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks.base_framework import BaseFramework


class PerformanceFramework(BaseFramework):
    """
    Framework de Diagnóstico de Performance.

    Analisa volume produzido, eficiência operacional e qualidade
    dos resultados com base nas métricas disponíveis.
    """

    def analyze(self) -> Dict[str, Any]:
        """Executa diagnóstico de performance e retorna seções estruturadas."""
        result = {}
        num_cols = self._get_numeric_cols()
        cat_cols = self._get_categorical_cols()

        if not self._has_enough_data():
            return {
                "volume": self._build_section(
                    "Volume — Dados insuficientes",
                    "Dataset muito pequeno para diagnóstico.",
                    self.df, "table", "", "", "Dados",
                )
            }

        # VOLUME: Quanto foi produzido
        if num_cols:
            main_num = num_cols[0]
            total = self.df[main_num].sum()
            mean_val = self.df[main_num].mean()
            max_val = self.df[main_num].max()
            min_val = self.df[main_num].min()

            volume_text = (
                f"Volume total de '{main_num}': {total:,.2f}. "
                f"Média por registro: {mean_val:,.2f}. "
                f"Pico: {max_val:,.2f} | Mínimo: {min_val:,.2f}. "
                f"Amplitude de {((max_val - min_val)/max(mean_val, 0.01)*100):.0f}% em relação à média."
            )

            if cat_cols:
                main_cat = cat_cols[0]
                vol_data = self.df.groupby(main_cat)[main_num].sum().reset_index().sort_values(main_num, ascending=False)
                result["volume"] = self._build_section(
                    "Volume — Produção Total",
                    volume_text,
                    vol_data,
                    "bar", main_cat, main_num,
                    f"Volume de {main_num} por {main_cat}",
                    "sum",
                )
            else:
                result["volume"] = self._build_section(
                    "Volume — Produção Total",
                    volume_text,
                    self.df[[main_num]].describe().reset_index(),
                    "table", "", "", f"Estatísticas de {main_num}",
                )
        else:
            result["volume"] = self._build_section(
                "Volume — Produção Total",
                "Sem colunas numéricas para análise de volume.",
                self.df, "table", "", "", "Dados",
            )

        # EFICIÊNCIA: Relação entre recursos e resultado
        if len(num_cols) >= 2:
            input_col = num_cols[0]
            output_col = num_cols[1]
            total_input = self.df[input_col].sum()
            total_output = self.df[output_col].sum()
            efficiency = (total_output / total_input) if total_input > 0 else 0

            efic_text = (
                f"Eficiência: para cada unidade de '{input_col}', "
                f"são geradas {efficiency:.4f} unidades de '{output_col}'. "
                f"Total investido: {total_input:,.2f} | Retorno: {total_output:,.2f}."
            )

            if cat_cols:
                main_cat = cat_cols[0]
                efic_df = self.df.groupby(main_cat)[[input_col, output_col]].sum().reset_index()
                efic_df["eficiencia"] = efic_df[output_col] / efic_df[input_col].replace(0, float("nan"))
                efic_df = efic_df.sort_values("eficiencia", ascending=False)

                efic_text += (
                    f" Maior eficiência: '{efic_df.iloc[0][main_cat]}' "
                    f"({efic_df.iloc[0]['eficiencia']:.4f}). "
                    f"Menor eficiência: '{efic_df.iloc[-1][main_cat]}' "
                    f"({efic_df.iloc[-1]['eficiencia']:.4f})."
                )

                result["eficiencia"] = self._build_section(
                    "Eficiência — Relação Insumo/Resultado",
                    efic_text,
                    efic_df,
                    "bar", main_cat, "eficiencia",
                    f"Eficiência por {main_cat}",
                    "mean",
                )
            else:
                result["eficiencia"] = self._build_section(
                    "Eficiência — Relação Insumo/Resultado",
                    efic_text,
                    self.df[[input_col, output_col]].head(50),
                    "scatter", input_col, output_col,
                    f"{input_col} vs {output_col}",
                )
        else:
            result["eficiencia"] = self._build_section(
                "Eficiência — Relação Insumo/Resultado",
                "Apenas uma métrica disponível. Para análise de eficiência, forneça ao menos 2 colunas numéricas.",
                self.df, "table", "", "", "Dados",
            )

        # QUALIDADE: Consistência e concentração
        if num_cols:
            main_num = num_cols[0]
            cv = (self.df[main_num].std() / self.df[main_num].mean() * 100) if self.df[main_num].mean() != 0 else 0
            null_pct = (self.df[main_num].isna().sum() / len(self.df) * 100)

            qual_text = (
                f"Qualidade dos dados de '{main_num}': "
                f"coeficiente de variação de {cv:.1f}% "
                f"({'alta variabilidade' if cv > 50 else 'variabilidade moderada' if cv > 20 else 'dados consistentes'}). "
                f"Completude: {100 - null_pct:.1f}% dos registros preenchidos."
            )

            if cat_cols:
                main_cat = cat_cols[0]
                qual_data = self.df.groupby(main_cat)[main_num].agg(["mean", "std", "count"]).reset_index()
                qual_data.columns = [main_cat, "media", "desvio_padrao", "contagem"]
                qual_data["cv"] = (qual_data["desvio_padrao"] / qual_data["media"].replace(0, float("nan")) * 100).round(1)

                result["qualidade"] = self._build_section(
                    "Qualidade — Consistência dos Resultados",
                    qual_text,
                    qual_data,
                    "bar", main_cat, "cv",
                    f"Coeficiente de Variação por {main_cat} (%)",
                    "mean",
                )
            else:
                result["qualidade"] = self._build_section(
                    "Qualidade — Consistência dos Resultados",
                    qual_text,
                    self.df[[main_num]].describe().reset_index(),
                    "table", "", "", "Estatísticas",
                )
        else:
            result["qualidade"] = self._build_section(
                "Qualidade — Consistência dos Resultados",
                "Sem colunas numéricas para análise de qualidade.",
                self.df, "table", "", "", "Dados",
            )

        return result
