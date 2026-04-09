"""Framework Funil de Conversão: Topo → Meio → Fundo → Conversão → Gargalos."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks.base_framework import BaseFramework


class FunnelFramework(BaseFramework):
    """
    Framework de Funil de Conversão.

    Analisa volume, taxas de conversão e identifica gargalos
    com base nas métricas numéricas disponíveis.
    """

    def analyze(self) -> Dict[str, Any]:
        """Executa análise de funil e retorna seções estruturadas."""
        result = {}
        num_cols = self._get_numeric_cols()
        cat_cols = self._get_categorical_cols()

        if not self._has_enough_data():
            return {
                "topo": self._build_section(
                    "Topo — Dados insuficientes",
                    "Dataset muito pequeno para análise de funil.",
                    self.df, "table", "", "", "Dados",
                )
            }

        # TOPO: Volume de entrada
        if num_cols:
            main_num = num_cols[0]
            total_volume = self.df[main_num].sum()
            mean_vol = self.df[main_num].mean()

            topo_text = (
                f"Topo do funil: volume total de {total_volume:,.2f} em '{main_num}', "
                f"com média de {mean_vol:,.2f} por registro. "
                f"O dataset registra {len(self.df):,} entradas no período analisado."
            )

            if cat_cols:
                main_cat = cat_cols[0]
                grouped = self.df.groupby(main_cat)[main_num].sum().reset_index()
                result["topo"] = self._build_section(
                    "Topo — Volume de Entrada",
                    topo_text,
                    grouped,
                    "bar", main_cat, main_num,
                    f"Volume por {main_cat}",
                    "sum",
                )
            else:
                result["topo"] = self._build_section(
                    "Topo — Volume de Entrada",
                    topo_text,
                    self.df[[main_num]].head(50),
                    "bar", self.df.index.name or "index", main_num,
                    "Volume Total",
                    "sum",
                )
        else:
            result["topo"] = self._build_section(
                "Topo — Volume de Entrada",
                "Sem colunas numéricas para análise de volume.",
                self.df, "table", "", "", "Dados",
            )

        # MEIO: Análise intermediária (segunda métrica se disponível)
        if len(num_cols) >= 2:
            m1, m2 = num_cols[0], num_cols[1]
            total_m1 = self.df[m1].sum()
            total_m2 = self.df[m2].sum()
            ratio = (total_m2 / total_m1 * 100) if total_m1 > 0 else 0

            meio_text = (
                f"Meio do funil: de {total_m1:,.2f} em '{m1}', "
                f"foram gerados {total_m2:,.2f} em '{m2}' — "
                f"taxa de {ratio:.1f}%. "
            )
            if ratio < 30:
                meio_text += "Taxa abaixo de 30% indica perda significativa nesta etapa."
            elif ratio < 60:
                meio_text += "Taxa moderada — há espaço para otimização nesta etapa."
            else:
                meio_text += "Taxa saudável — etapa intermediária bem convertida."

            if cat_cols:
                main_cat = cat_cols[0]
                meio_data = self.df.groupby(main_cat)[[m1, m2]].sum().reset_index()
                result["meio"] = self._build_section(
                    "Meio — Conversão Intermediária",
                    meio_text,
                    meio_data,
                    "bar", main_cat, m2,
                    f"{m2} por {main_cat}",
                    "sum",
                )
            else:
                result["meio"] = self._build_section(
                    "Meio — Conversão Intermediária",
                    meio_text,
                    self.df[[m1, m2]].head(50),
                    "scatter", m1, m2,
                    f"{m1} vs {m2}",
                )
        else:
            result["meio"] = self._build_section(
                "Meio — Conversão Intermediária",
                "Apenas uma métrica disponível. Para análise de funil completo, forneça ao menos 2 métricas numéricas.",
                self.df, "table", "", "", "Dados",
            )

        # FUNDO: Resultado final (última métrica ou combinação)
        if len(num_cols) >= 2:
            last_num = num_cols[-1]
            first_num = num_cols[0]
            total_last = self.df[last_num].sum()
            total_first = self.df[first_num].sum()
            final_conv = (total_last / total_first * 100) if total_first > 0 else 0

            fundo_text = (
                f"Fundo do funil: '{last_num}' totaliza {total_last:,.2f}. "
                f"Conversão global de '{first_num}' para '{last_num}': {final_conv:.1f}%. "
            )
            if final_conv < 10:
                fundo_text += "Conversão final crítica — revisar todas as etapas do funil."
            elif final_conv < 25:
                fundo_text += "Conversão final abaixo do esperado para a maioria dos segmentos."
            else:
                fundo_text += "Conversão final dentro de parâmetros aceitáveis."

            if cat_cols:
                main_cat = cat_cols[0]
                fundo_data = (
                    self.df.groupby(main_cat)[last_num]
                    .sum()
                    .reset_index()
                    .sort_values(last_num, ascending=False)
                )
                result["fundo"] = self._build_section(
                    "Fundo — Resultado Final",
                    fundo_text,
                    fundo_data,
                    "pie", main_cat, last_num,
                    f"Distribuição de {last_num}",
                    "sum",
                )
            else:
                result["fundo"] = self._build_section(
                    "Fundo — Resultado Final",
                    fundo_text,
                    self.df[[last_num]].head(50),
                    "bar", self.df.index.name or "index", last_num,
                    f"Resultado: {last_num}",
                )
        else:
            result["fundo"] = result.get("topo", self._build_section(
                "Fundo — Resultado Final",
                "Métricas insuficientes para análise de fundo de funil.",
                self.df, "table", "", "", "Dados",
            ))

        # GARGALOS: Onde há maior perda
        if num_cols and cat_cols:
            main_num = num_cols[0]
            main_cat = cat_cols[0]
            grouped = self.df.groupby(main_cat)[main_num].sum().reset_index()
            total = grouped[main_num].sum()
            grouped["pct"] = grouped[main_num] / total * 100
            grouped = grouped.sort_values(main_num, ascending=True)

            bottom3 = grouped.head(3)
            gargalo_text = (
                "Gargalos identificados: as 3 categorias com menor volume são "
                + ", ".join(
                    f"'{r[main_cat]}' ({r['pct']:.1f}%)"
                    for _, r in bottom3.iterrows()
                )
                + ". Estas representam as maiores oportunidades de melhoria no funil."
            )

            result["gargalos"] = self._build_section(
                "Gargalos — Pontos de Perda",
                gargalo_text,
                grouped,
                "bar", main_cat, main_num,
                "Categorias por Volume (Crescente)",
                "sum",
            )
        else:
            result["gargalos"] = self._build_section(
                "Gargalos — Pontos de Perda",
                "Dados insuficientes para identificação de gargalos.",
                self.df, "table", "", "", "Dados",
            )

        return result
