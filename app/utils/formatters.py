"""Funções utilitárias de formatação."""

import re
import unicodedata
from typing import Any


def normalize_column_name(name: str) -> str:
    """Normaliza nome de coluna: lowercase, sem espaços, sem acentos, sem caracteres especiais."""
    name = str(name).strip()
    # Remove acentos
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    # Lowercase
    name = name.lower()
    # Substitui espaços e hífens por underscore
    name = re.sub(r"[\s\-]+", "_", name)
    # Remove caracteres não alfanuméricos (exceto underscore)
    name = re.sub(r"[^\w]", "", name)
    # Remove underscores duplicados
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def format_number(value: Any, decimals: int = 2) -> str:
    """Formata número com separadores brasileiros."""
    try:
        return f"{float(value):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float) -> str:
    """Formata valor como porcentagem."""
    return f"{value:.1f}%"


def clean_numeric_string(value: str) -> str:
    """Remove símbolos monetários e converte para número."""
    if not isinstance(value, str):
        return str(value)
    value = value.strip()
    value = re.sub(r"[R$\s]", "", value)
    value = value.replace(".", "").replace(",", ".")
    return value
