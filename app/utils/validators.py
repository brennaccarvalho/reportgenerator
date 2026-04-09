"""Funções de validação de entradas."""

import re
from typing import Optional


def validate_google_sheets_url(url: str) -> Optional[str]:
    """
    Extrai o spreadsheet_id de uma URL do Google Sheets.
    Retorna o ID ou None se inválido.
    """
    patterns = [
        r"/spreadsheets/d/([a-zA-Z0-9-_]+)",
        r"spreadsheets/d/([a-zA-Z0-9-_]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_file_size(file_size_bytes: int, max_mb: int) -> bool:
    """Valida se o arquivo está dentro do tamanho máximo permitido."""
    max_bytes = max_mb * 1024 * 1024
    return file_size_bytes <= max_bytes


def validate_dataframe_not_empty(df) -> bool:
    """Valida que o DataFrame não está vazio."""
    return df is not None and not df.empty and len(df.columns) > 0
