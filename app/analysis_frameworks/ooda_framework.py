"""Framework OODA Loop: Observe → Orient → Decide → Act."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks.base_framework import BaseFramework


class OodaFramework(BaseFramework):
    """
    Framework OODA Loop aplicado a dados tabulares.

    Fases:
    - Observe: Visão geral dos dados e distribuições principais.
    - Orient: Contexto comparativo e benchmarks internos.
    - Decide: Identificação de pontos de ação.
    - Act: Recomendações baseadas nos dados.
    """

    def analyze(self) -> Dict[str, Any]:
        """Executa análise OODA Loop e retorna seções estruturadas."""
        result = {}
        num_cols = self._get_numeric_cols()
        cat_cols = self._get_categorical_cols()

        if not self._has_enough_data():
            return {
                "observe": self._build_section(
                    "Observe — Dados insuficientes",
                    "O dataset contém menos de 5 linhas. Não é possível gerar análise confiável.",
                    self.df,
                    "table", "", "", "Dados brutos",
                )
            }

        # OBSERVE: Visão geral dos dados
        observe_data = self.df.describe(include="all").T.reset_index()
        observe_data.columns = [str(c) for c in observe_data.columns]

        if num_cols and cat_cols:
            main_num = num_cols[0]
            main_cat = cat_cols[0]
            total = self.df[main_num].sum()
            observe_text = (
                f"O dataset contém {len(self.df):,} registros com {len(self.df.columns)} dimensões. "
                f"A métrica principal '{main_num}' totaliza {total:,.2f}, "
                f"distribuída em {self.df[main_cat].nunique()} categorias de '{main_cat}'. "
                f"Esses são os fatos observáveis sem interpretação."
            )
            obs_chart_type, obs_x, obs_y = "bar", main_cat, main_num
        else:
            observe_text = (
                f"O dataset contém {len(self.df):,} registros com {len(self.df.columns)} dimensões. "
                "Não foram detectadas colunas numéricas e categóricas para análise combinada."
            )
            obs_chart_type, obs_x, obs_y = "table", "", ""

        result["observe"] = self._build_section(
            "Observe — Panorama Geral",
            observe_text,
            self.df.head(50),
            obs_chart_type, obs_x, obs_y,
            "Distribuição Geral dos Dados",
            "sum",
        )

        # ORIENT: Contexto e comparação
        if num_cols and cat_cols:
            main_num = num_cols[0]
            main_cat = cat_cols[0]
            grouped = (
                self.df.groupby(main_cat)[main_num]
                .sum()
                .reset_index()
                .sort_values(main_num, ascending=False)
            )
            top = grouped.iloc[0]
            bottom = grouped.iloc[-1]
            total = grouped[main_num].sum()
            top_pct = (top[main_num] / total * 100) if total > 0 else 0

            orient_text = (
                f"Orientando o contexto: '{top[main_cat]}' lidera com "
                f"{top[main_num]:,.2f} ({top_pct:.1f}% do total), "
                f"enquanto '{bottom[main_cat]}' tem o menor volume com {bottom[main_num]:,.2f}. "
                f"Essa disparidade de {(top[main_num] / max(bottom[main_num], 0.01)):.1f}x "
                f"indica concentração relevante que deve orientar decisões."
            )

            result["orient"] = self._build_section(
                "Orient — Contexto Comparativo",
                orient_text,
                grouped,
                "bar", main_cat, main_num,
                f"Ranking por {main_num}",
                "sum",
            )
        else:
            result["orient"] = self._build_section(
                "Orient — Contexto Comparativo",
                "Dados insuficientes para comparação contextual (requer colunas numéricas e categóricas).",
                self.df,
                "table", "", "", "Dados",
            )

        # DECIDE: Identificação de pontos críticos
        if len(num_cols) >= 2:
            m1, m2 = num_cols[0], num_cols[1]
            corr = self.df[[m1, m2]].corr().iloc[0, 1]
            decide_text = (
                f"Ponto de decisão: a correlação entre '{m1}' e '{m2}' é {corr:.2f}. "
            )
            if abs(corr) > 0.7:
                decide_text += (
                    f"Correlação {'positiva' if corr > 0 else 'negativa'} forte — "
                    f"variações em '{m1}' tendem a {'aumentar' if corr > 0 else 'reduzir'} '{m2}'."
                )
            elif abs(corr) > 0.4:
                decide_text += "Correlação moderada — relação parcial entre as métricas."
            else:
                decide_text += "Correlação fraca — métricas se comportam de forma independente."

            scatter_data = self.df[[m1, m2]].dropna()
            result["decide"] = self._build_section(
                "Decide — Pontos de Decisão",
                decide_text,
                scatter_data,
                "scatter", m1, m2,
                f"Relação entre {m1} e {m2}",
                "sum",
            )
        elif num_cols:
            main_num = num_cols[0]
            mean_val = self.df[main_num].mean()
            std_val = self.df[main_num].std()
            decide_text = (
                f"'{main_num}': média de {mean_val:,.2f} com desvio padrão de {std_val:,.2f}. "
                f"Valores acima de {(mean_val + std_val):,.2f} representam performance acima da média."
            )
            result["decide"] = self._build_section(
                "Decide — Pontos de Decisão",
                decide_text,
                self.df[[main_num]].dropna(),
                "bar", self.df.index.name or "index", main_num,
                f"Distribuição de {main_num}",
            )
        else:
            result["decide"] = self._build_section(
                "Decide — Pontos de Decisão",
                "Sem colunas numéricas para análise de decisão.",
                self.df, "table", "", "", "Dados",
            )

        # ACT: Recomendações baseadas nos dados
        act_lines = []
        if num_cols and cat_cols:
            main_num = num_cols[0]
            main_cat = cat_cols[0]
            grouped = self.df.groupby(main_cat)[main_num].sum().reset_index()
            total = grouped[main_num].sum()
            top3 = grouped.nlargest(3, main_num)
            act_lines.append(
                f"Priorize recursos nas top 3 categorias de '{main_cat}': "
                + ", ".join(
                    f"'{r[main_cat]}' ({r[main_num]/total*100:.1f}%)"
                    for _, r in top3.iterrows()
                )
                + f" — responsáveis por {top3[main_num].sum()/total*100:.1f}% do total."
            )
            bottom1 = grouped.nsmallest(1, main_num).iloc[0]
            act_lines.append(
                f"Investigue '{bottom1[main_cat]}' — menor volume ({bottom1[main_num]:,.2f}). "
                "Avaliar se deve ser descontinuado ou receber intervenção."
            )

        act_text = " ".join(act_lines) if act_lines else (
            "Com os dados disponíveis, recomenda-se aprofundar a coleta de métricas "
            "numéricas para gerar recomendações acionáveis."
        )

        act_data = top3 if (num_cols and cat_cols) else self.df.head(10)
        result["act"] = self._build_section(
            "Act — Recomendações Acionáveis",
            act_text,
            act_data,
            "bar",
            main_cat if (num_cols and cat_cols) else "",
            main_num if num_cols else "",
            "Top Prioridades para Ação",
            "sum",
        )

        return result
