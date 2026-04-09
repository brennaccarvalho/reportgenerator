"""Framework EDA — Análise Exploratória: Distribuições → Correlações → Outliers."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks.base_framework import BaseFramework


class EdaFramework(BaseFramework):
    """
    Framework de Análise Exploratória de Dados (EDA).

    Explora distribuições, correlações entre variáveis e outliers
    de forma automática com base nos tipos de colunas disponíveis.
    """

    def analyze(self) -> Dict[str, Any]:
        """Executa EDA e retorna seções estruturadas."""
        result = {}
        num_cols = self._get_numeric_cols()
        cat_cols = self._get_categorical_cols()

        if not self._has_enough_data():
            return {
                "distribuicoes": self._build_section(
                    "Distribuições — Dados insuficientes",
                    "Dataset com menos de 5 registros — EDA não aplicável.",
                    self.df, "table", "", "", "Dados",
                )
            }

        # DISTRIBUIÇÕES: Estatísticas descritivas
        if num_cols:
            desc = self.df[num_cols].describe().T.reset_index()
            desc.columns = ["coluna"] + list(desc.columns[1:])

            dist_lines = []
            for col in num_cols[:3]:
                mean_v = self.df[col].mean()
                median_v = self.df[col].median()
                skew_v = self.df[col].skew()
                dist_lines.append(
                    f"'{col}': média={mean_v:,.2f}, mediana={median_v:,.2f}, "
                    f"assimetria={'positiva' if skew_v > 0.5 else 'negativa' if skew_v < -0.5 else 'simétrica'} ({skew_v:.2f})"
                )

            dist_text = "Distribuições das métricas numéricas: " + "; ".join(dist_lines) + "."

            main_num = num_cols[0]
            if cat_cols:
                main_cat = cat_cols[0]
                dist_data = self.df.groupby(main_cat)[main_num].mean().reset_index()
                result["distribuicoes"] = self._build_section(
                    "Distribuições — Estatísticas Descritivas",
                    dist_text,
                    dist_data,
                    "bar", main_cat, main_num,
                    f"Média de {main_num} por {main_cat}",
                    "mean",
                )
            else:
                result["distribuicoes"] = self._build_section(
                    "Distribuições — Estatísticas Descritivas",
                    dist_text,
                    desc,
                    "table", "", "", "Resumo Estatístico",
                )
        else:
            result["distribuicoes"] = self._build_section(
                "Distribuições — Estatísticas Descritivas",
                "Sem colunas numéricas para análise de distribuição.",
                self.df, "table", "", "", "Dados",
            )

        # CORRELAÇÕES
        if len(num_cols) >= 2:
            corr_matrix = self.df[num_cols].corr()
            high_corr = []
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    c = corr_matrix.iloc[i, j]
                    if abs(c) > 0.5:
                        high_corr.append((num_cols[i], num_cols[j], c))

            if high_corr:
                corr_lines = [
                    f"'{a}' e '{b}': {c:.2f} ({'positiva' if c > 0 else 'negativa'})"
                    for a, b, c in sorted(high_corr, key=lambda x: abs(x[2]), reverse=True)[:5]
                ]
                corr_text = (
                    f"Correlações relevantes (|r| > 0.5) encontradas: "
                    + "; ".join(corr_lines) + "."
                )
            else:
                corr_text = (
                    "Nenhuma correlação forte (|r| > 0.5) encontrada entre as métricas. "
                    "As variáveis se comportam de forma relativamente independente."
                )

            if len(num_cols) >= 2:
                top_pair = high_corr[0] if high_corr else (num_cols[0], num_cols[1], 0)
                scatter_data = self.df[[top_pair[0], top_pair[1]]].dropna()
                result["correlacoes"] = self._build_section(
                    "Correlações — Relações entre Variáveis",
                    corr_text,
                    scatter_data,
                    "scatter", top_pair[0], top_pair[1],
                    f"Correlação: {top_pair[0]} vs {top_pair[1]}",
                )
        else:
            result["correlacoes"] = self._build_section(
                "Correlações — Relações entre Variáveis",
                "São necessárias ao menos 2 colunas numéricas para análise de correlação.",
                self.df, "table", "", "", "Dados",
            )

        # OUTLIERS: Método IQR
        if num_cols:
            outlier_summary = []
            all_outlier_data = {}
            for col in num_cols[:4]:
                q1 = self.df[col].quantile(0.25)
                q3 = self.df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]
                n_out = len(outliers)
                pct_out = n_out / len(self.df) * 100
                if n_out > 0:
                    outlier_summary.append(
                        f"'{col}': {n_out} outlier(s) ({pct_out:.1f}%) — "
                        f"limites [{lower:,.2f}, {upper:,.2f}]"
                    )
                all_outlier_data[col] = n_out

            if outlier_summary:
                out_text = "Outliers detectados (método IQR): " + "; ".join(outlier_summary) + "."
            else:
                out_text = "Nenhum outlier significativo detectado pelo método IQR nas métricas analisadas."

            out_df = pd.DataFrame(
                [(k, v) for k, v in all_outlier_data.items()],
                columns=["coluna", "n_outliers"],
            )

            result["outliers"] = self._build_section(
                "Outliers — Valores Atípicos",
                out_text,
                out_df,
                "bar", "coluna", "n_outliers",
                "Quantidade de Outliers por Métrica",
                "sum",
            )
        else:
            result["outliers"] = self._build_section(
                "Outliers — Valores Atípicos",
                "Sem colunas numéricas para análise de outliers.",
                self.df, "table", "", "", "Dados",
            )

        return result
