"""Serviço de construção de gráficos com Plotly Express."""

from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.utils.logger import get_logger

logger = get_logger(__name__)

COLOR_PALETTE = px.colors.qualitative.Set2


def _aggregate(df: pd.DataFrame, x: str, y: str, aggregation: str) -> pd.DataFrame:
    """Agrega o DataFrame por x usando o método especificado."""
    if not x or not y or x not in df.columns or y not in df.columns:
        return df
    agg_map = {
        "sum": "sum",
        "mean": "mean",
        "count": "count",
        "max": "max",
        "min": "min",
    }
    agg_func = agg_map.get(aggregation, "sum")
    try:
        grouped = df.groupby(x)[y].agg(agg_func).reset_index()
        return grouped
    except Exception as e:
        logger.warning(f"Falha ao agregar dados: {e}")
        return df


def _apply_sort_and_limit(
    df: pd.DataFrame,
    y: str,
    sort_order: Optional[str],
    top_n: Optional[int],
) -> pd.DataFrame:
    """Aplica ordenação e limite de resultados ao DataFrame."""
    if sort_order and y and y in df.columns:
        ascending = sort_order == "asc"
        df = df.sort_values(y, ascending=ascending)
    if top_n and top_n > 0:
        df = df.head(top_n)
    return df


def build_chart(
    df: pd.DataFrame,
    chart_config: Dict[str, Any],
) -> go.Figure:
    """
    Constrói um gráfico Plotly a partir de uma configuração.

    Args:
        df: DataFrame com os dados.
        chart_config: Dicionário com chart_type, x, y, title, aggregation,
                      sort_order e top_n.

    Returns:
        Figura Plotly pronta para renderização.
    """
    chart_type = chart_config.get("chart_type", "bar")
    x = chart_config.get("x", "")
    y = chart_config.get("y", "")
    title = chart_config.get("title", "")
    aggregation = chart_config.get("aggregation", "sum")
    sort_order = chart_config.get("sort_order")
    top_n = chart_config.get("top_n")

    # Validar colunas existentes
    valid_x = x and x in df.columns
    valid_y = y and y in df.columns

    if chart_type == "table" or not valid_x or not valid_y:
        return _build_table(df, title)

    # Agregar dados
    plot_df = _aggregate(df, x, y, aggregation)
    plot_df = _apply_sort_and_limit(plot_df, y, sort_order, top_n)

    try:
        if chart_type == "bar":
            fig = px.bar(
                plot_df, x=x, y=y, title=title,
                color_discrete_sequence=COLOR_PALETTE,
            )
        elif chart_type == "line":
            fig = px.line(
                plot_df, x=x, y=y, title=title,
                markers=True,
                color_discrete_sequence=COLOR_PALETTE,
            )
        elif chart_type == "pie":
            fig = px.pie(
                plot_df, names=x, values=y, title=title,
                color_discrete_sequence=COLOR_PALETTE,
            )
        elif chart_type == "scatter":
            fig = px.scatter(
                plot_df, x=x, y=y, title=title,
                color_discrete_sequence=COLOR_PALETTE,
                trendline="ols" if len(plot_df) >= 3 else None,
            )
        else:
            return _build_table(df, title)

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=13),
            title=dict(font=dict(size=16, color="#1f2937")),
            margin=dict(l=40, r=40, t=60, b=40),
        )
        return fig

    except Exception as e:
        logger.warning(f"Erro ao construir gráfico '{chart_type}': {e}. Usando tabela.")
        return _build_table(df, title)


def _build_table(df: pd.DataFrame, title: str) -> go.Figure:
    """Constrói uma tabela Plotly como fallback."""
    display_df = df.head(50)
    header_values = list(display_df.columns)
    cell_values = [display_df[col].astype(str).tolist() for col in display_df.columns]

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=header_values,
                    fill_color="#4f46e5",
                    font=dict(color="white", size=12),
                    align="left",
                ),
                cells=dict(
                    values=cell_values,
                    fill_color=[["#f9fafb", "#ffffff"] * (len(display_df) // 2 + 1)],
                    align="left",
                    font=dict(size=11),
                ),
            )
        ]
    )
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def chart_to_image_bytes(fig: go.Figure) -> bytes:
    """
    Converte uma figura Plotly em PNG para uso em PDF.

    Args:
        fig: Figura Plotly.

    Returns:
        Bytes da imagem PNG.
    """
    try:
        return fig.to_image(format="png", width=900, height=450)
    except Exception as e:
        logger.warning(f"Erro ao converter gráfico para imagem: {e}")
        return b""
