"""Serviço de geração automática de insights analíticos."""

from typing import Dict, Any, List

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_insights(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Gera insights automáticos a partir de um DataFrame processado.

    Detecta: máximos, mínimos, concentração, outliers (IQR),
    correlações altas, e rankings de categorias por métrica.

    Args:
        df: DataFrame já limpo e tipado.

    Returns:
        Lista de dicionários de insight com type, title, description e severity.
    """
    insights: List[Dict[str, Any]] = []

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        insights.append({
            "type": "info",
            "title": "Sem métricas numéricas",
            "description": "O dataset não contém colunas numéricas. Insights quantitativos não estão disponíveis.",
            "severity": "info",
        })
        return insights

    # Máximos e mínimos por coluna numérica
    for col in num_cols[:5]:
        series = df[col].dropna()
        if series.empty:
            continue
        max_val = series.max()
        min_val = series.min()
        mean_val = series.mean()

        insights.append({
            "type": "max",
            "title": f"Pico em '{col}'",
            "description": (
                f"O valor máximo de '{col}' é {max_val:,.2f}, "
                f"{((max_val - mean_val) / max(mean_val, 0.01) * 100):.0f}% acima da média ({mean_val:,.2f})."
            ),
            "severity": "info",
        })

        insights.append({
            "type": "min",
            "title": f"Mínimo em '{col}'",
            "description": (
                f"O valor mínimo de '{col}' é {min_val:,.2f}, "
                f"{((mean_val - min_val) / max(mean_val, 0.01) * 100):.0f}% abaixo da média ({mean_val:,.2f})."
            ),
            "severity": "info",
        })

    # Concentração: categoria com >50% do total
    if cat_cols and num_cols:
        main_cat = cat_cols[0]
        main_num = num_cols[0]
        grouped = df.groupby(main_cat)[main_num].sum()
        total = grouped.sum()
        if total > 0:
            for cat_val, val in grouped.items():
                pct = val / total * 100
                if pct > 50:
                    insights.append({
                        "type": "concentration",
                        "title": f"Concentração em '{cat_val}'",
                        "description": (
                            f"'{cat_val}' representa {pct:.1f}% do total de '{main_num}' ({val:,.2f} de {total:,.2f}). "
                            "Alta concentração pode indicar dependência crítica desta categoria."
                        ),
                        "severity": "warning",
                    })

    # Rankings Top 5 por métrica
    if cat_cols and num_cols:
        main_cat = cat_cols[0]
        main_num = num_cols[0]
        top5 = df.groupby(main_cat)[main_num].sum().nlargest(5).reset_index()
        if not top5.empty:
            ranking_lines = [
                f"{i+1}º {row[main_cat]}: {row[main_num]:,.2f}"
                for i, (_, row) in enumerate(top5.iterrows())
            ]
            insights.append({
                "type": "ranking",
                "title": f"Top 5 por '{main_num}'",
                "description": "Ranking das principais categorias: " + " | ".join(ranking_lines),
                "severity": "info",
            })

    # Outliers pelo método IQR
    for col in num_cols[:4]:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        n_outliers = ((series < lower) | (series > upper)).sum()
        pct = n_outliers / len(series) * 100
        if n_outliers > 0:
            severity = "critical" if pct > 10 else "warning" if pct > 5 else "info"
            insights.append({
                "type": "outlier",
                "title": f"Outliers em '{col}'",
                "description": (
                    f"{n_outliers} valor(es) atípico(s) detectado(s) em '{col}' "
                    f"({pct:.1f}% dos registros). "
                    f"Limites IQR: [{lower:,.2f}, {upper:,.2f}]."
                ),
                "severity": severity,
            })

    # Correlações altas (>0.8)
    if len(num_cols) >= 2:
        try:
            corr_matrix = df[num_cols].corr()
            for i in range(len(num_cols)):
                for j in range(i + 1, len(num_cols)):
                    c = corr_matrix.iloc[i, j]
                    if abs(c) >= 0.8:
                        direction = "positiva" if c > 0 else "negativa"
                        insights.append({
                            "type": "correlation",
                            "title": f"Alta correlação: '{num_cols[i]}' e '{num_cols[j]}'",
                            "description": (
                                f"Correlação {direction} de {c:.2f} entre '{num_cols[i]}' e '{num_cols[j]}'. "
                                "Variações em uma métrica tendem a "
                                f"{'acompanhar' if c > 0 else 'inverter'} a outra."
                            ),
                            "severity": "info",
                        })
        except Exception as e:
            logger.warning(f"Erro ao calcular correlações: {e}")

    # Variações percentuais temporais
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    if date_cols and num_cols:
        date_col = date_cols[0]
        main_num = num_cols[0]
        try:
            df_time = df[[date_col, main_num]].dropna().copy()
            df_time["periodo"] = df_time[date_col].dt.to_period("M").astype(str)
            monthly = df_time.groupby("periodo")[main_num].sum().reset_index().sort_values("periodo")
            if len(monthly) >= 2:
                last = monthly.iloc[-1][main_num]
                prev = monthly.iloc[-2][main_num]
                change = ((last - prev) / prev * 100) if prev > 0 else 0
                severity = "critical" if abs(change) > 30 else "warning" if abs(change) > 15 else "info"
                insights.append({
                    "type": "temporal",
                    "title": f"Variação recente em '{main_num}'",
                    "description": (
                        f"Comparando os dois últimos períodos: "
                        f"{'+'if change >= 0 else ''}{change:.1f}% "
                        f"({prev:,.2f} → {last:,.2f})."
                    ),
                    "severity": severity,
                })
        except Exception as e:
            logger.warning(f"Erro na análise temporal de insights: {e}")

    logger.info(f"{len(insights)} insight(s) gerado(s).")
    return insights
