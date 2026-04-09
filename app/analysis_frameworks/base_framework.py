"""Framework base abstrato para todos os frameworks analíticos."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd


class BaseFramework(ABC):
    """
    Classe base para todos os frameworks de análise.

    Cada subclasse implementa `analyze()` que retorna um dicionário
    de seções estruturadas para renderização.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Inicializa o framework com o DataFrame processado.

        Args:
            df: DataFrame já limpo e tipado.
        """
        self.df = df.copy()

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Executa a análise e retorna seções estruturadas.

        Returns:
            Dicionário onde cada chave é uma etapa do framework.
            Cada valor é um dict com 'title', 'text', 'data' e 'chart_config'.
        """
        pass

    def _get_numeric_cols(self) -> List[str]:
        """Retorna lista de colunas numéricas."""
        return self.df.select_dtypes(include="number").columns.tolist()

    def _get_categorical_cols(self) -> List[str]:
        """Retorna lista de colunas categóricas/texto."""
        return self.df.select_dtypes(include=["object", "category"]).columns.tolist()

    def _get_date_cols(self) -> List[str]:
        """Retorna lista de colunas de data."""
        return self.df.select_dtypes(include=["datetime64"]).columns.tolist()

    def _has_enough_data(self, min_rows: int = 5) -> bool:
        """Verifica se há dados suficientes para análise."""
        return len(self.df) >= min_rows

    def _build_section(
        self,
        title: str,
        text: str,
        data: pd.DataFrame,
        chart_type: str,
        x: str,
        y: str,
        chart_title: str,
        aggregation: str = "sum",
    ) -> Dict[str, Any]:
        """
        Constrói uma seção de análise padronizada.

        Args:
            title: Título da seção.
            text: Texto analítico interpretativo.
            data: DataFrame com os dados da seção.
            chart_type: Tipo de gráfico (bar, line, pie, scatter, table).
            x: Coluna do eixo X.
            y: Coluna do eixo Y.
            chart_title: Título do gráfico.
            aggregation: Tipo de agregação.

        Returns:
            Dicionário de seção padronizado.
        """
        return {
            "title": title,
            "text": text,
            "data": data,
            "chart_config": {
                "chart_type": chart_type,
                "x": x,
                "y": y,
                "title": chart_title,
                "aggregation": aggregation,
            },
        }
