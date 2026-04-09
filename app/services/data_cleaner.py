"""Serviço de limpeza e saneamento de dados."""

import re
from typing import Tuple

import pandas as pd

from app.utils.formatters import normalize_column_name, clean_numeric_string
from app.utils.logger import get_logger

logger = get_logger(__name__)

DATE_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d/%m/%y",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
]


def _try_parse_date(series: pd.Series) -> Tuple[pd.Series, bool]:
    """Tenta converter uma série para datetime usando formatos comuns."""
    for fmt in DATE_FORMATS:
        try:
            converted = pd.to_datetime(series, format=fmt, errors="raise")
            return converted, True
        except Exception:
            continue
    try:
        converted = pd.to_datetime(series, errors="raise")
        return converted, True
    except Exception:
        return series, False


def _try_parse_numeric(series: pd.Series) -> Tuple[pd.Series, bool]:
    """Tenta converter uma série de strings para numérico."""
    cleaned = series.astype(str).apply(clean_numeric_string)
    converted = pd.to_numeric(cleaned, errors="coerce")
    success_rate = converted.notna().sum() / max(len(series), 1)
    if success_rate >= 0.8:
        return converted, True
    return series, False


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """
    Realiza limpeza e saneamento completo de um DataFrame.

    Operações:
    - Normaliza nomes de colunas
    - Remove duplicatas
    - Infere e converte tipos de dados
    - Converte strings numéricas (R$, %, vírgula como decimal)
    - Converte datas em formatos comuns

    Args:
        df: DataFrame bruto.

    Returns:
        Tupla (DataFrame limpo, lista de transformações aplicadas).
    """
    transformations_log = []
    result = df.copy()

    # Normalizar nomes de colunas
    original_cols = result.columns.tolist()
    new_cols = [normalize_column_name(c) for c in original_cols]
    result.columns = new_cols
    renamed = [
        f"'{o}' → '{n}'" for o, n in zip(original_cols, new_cols) if o != n
    ]
    if renamed:
        transformations_log.append(
            f"Colunas renomeadas: {', '.join(renamed)}"
        )

    # Remover linhas completamente vazias
    before = len(result)
    result.dropna(how="all", inplace=True)
    removed_empty = before - len(result)
    if removed_empty:
        transformations_log.append(
            f"{removed_empty} linha(s) completamente vazias removidas."
        )

    # Remover duplicatas
    before = len(result)
    result.drop_duplicates(inplace=True)
    removed_dupes = before - len(result)
    if removed_dupes:
        transformations_log.append(
            f"{removed_dupes} linha(s) duplicada(s) removidas."
        )

    # Processar cada coluna
    for col in result.columns:
        series = result[col]

        # Pular colunas já numéricas ou de data
        if pd.api.types.is_numeric_dtype(series):
            continue
        if pd.api.types.is_datetime64_any_dtype(series):
            continue

        # Tentar converter para data
        non_null = series.dropna()
        if len(non_null) == 0:
            continue

        converted_date, is_date = _try_parse_date(non_null)
        if is_date:
            result[col] = pd.to_datetime(result[col], errors="coerce")
            transformations_log.append(
                f"Coluna '{col}' convertida para data."
            )
            continue

        # Tentar converter para numérico
        converted_num, is_num = _try_parse_numeric(series)
        if is_num:
            result[col] = converted_num
            transformations_log.append(
                f"Coluna '{col}' convertida para numérico."
            )
            continue

    if not transformations_log:
        transformations_log.append("Nenhuma transformação necessária — dados já estão limpos.")

    logger.info(f"Limpeza concluída: {len(transformations_log)} transformação(ões) aplicada(s).")
    return result, transformations_log
