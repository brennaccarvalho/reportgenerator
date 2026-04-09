"""Serviço de perfilamento e análise de qualidade dos dados."""

from typing import Dict, Any, List

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _infer_type(series: pd.Series) -> str:
    """Infere o tipo semântico de uma coluna."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "data"
    if pd.api.types.is_bool_dtype(series):
        return "booleano"
    if pd.api.types.is_numeric_dtype(series):
        return "numérico"
    nunique = series.nunique()
    n = len(series.dropna())
    if n > 0 and (nunique / n) < 0.2 and nunique <= 30:
        return "categórico"
    return "texto"


def profile_dataframe(df: pd.DataFrame, transformations_log: List[str] = None) -> Dict[str, Any]:
    """
    Gera o perfil completo de um DataFrame.

    Args:
        df: DataFrame a ser perfilado.
        transformations_log: Log de transformações já aplicadas.

    Returns:
        Dicionário com perfil completo incluindo issues e log.
    """
    if transformations_log is None:
        transformations_log = []

    issues: List[str] = []
    columns_profile = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = round((null_count / max(len(series), 1)) * 100, 2)
        unique_count = int(series.nunique())
        inferred_type = _infer_type(series)

        sample_values = series.dropna().unique().tolist()[:5]
        sample_values = [str(v) for v in sample_values]

        columns_profile.append({
            "name": col,
            "inferred_type": inferred_type,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "sample_values": sample_values,
        })

        # Issues por coluna
        if null_pct > 80:
            issues.append(
                f"Coluna '{col}' tem {null_pct:.0f}% de valores nulos — considere remover."
            )
        elif null_pct > 30:
            issues.append(
                f"Coluna '{col}' tem {null_pct:.0f}% de valores nulos."
            )

        if inferred_type == "numérico" and series.nunique() <= 1:
            issues.append(
                f"Coluna '{col}' tem variância zero (todos os valores são iguais)."
            )

    # Issues globais
    total_dupes = int(df.duplicated().sum())
    if total_dupes > 0:
        issues.append(f"{total_dupes} linha(s) duplicada(s) detectada(s) nos dados processados.")

    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": columns_profile,
        "issues": issues,
        "transformations_log": transformations_log,
    }
