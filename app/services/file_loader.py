"""Serviço de carregamento de arquivos CSV e XLSX."""

import io
from typing import Optional, Tuple

import chardet
import pandas as pd

from app.config.settings import MAX_UPLOAD_SIZE_MB
from app.utils.logger import get_logger
from app.utils.validators import validate_file_size

logger = get_logger(__name__)


def load_csv(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Carrega um arquivo CSV a partir de bytes.

    Args:
        file_bytes: Conteúdo do arquivo em bytes.
        filename: Nome original do arquivo.

    Returns:
        Tupla (DataFrame, mensagem de sucesso).

    Raises:
        ValueError: Se o arquivo for inválido ou muito grande.
    """
    if not validate_file_size(len(file_bytes), MAX_UPLOAD_SIZE_MB):
        raise ValueError(
            f"Arquivo muito grande. Tamanho máximo: {MAX_UPLOAD_SIZE_MB}MB."
        )

    detected = chardet.detect(file_bytes)
    encoding = detected.get("encoding") or "utf-8"
    logger.info(f"Encoding detectado para '{filename}': {encoding}")

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")

    if df.empty:
        raise ValueError("O arquivo CSV está vazio.")

    return df, f"Arquivo '{filename}' carregado com sucesso: {len(df)} linhas, {len(df.columns)} colunas."


def load_xlsx(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Carrega um arquivo XLSX a partir de bytes.

    Args:
        file_bytes: Conteúdo do arquivo em bytes.
        filename: Nome original do arquivo.

    Returns:
        Tupla (DataFrame, mensagem de sucesso).

    Raises:
        ValueError: Se o arquivo for inválido ou muito grande.
    """
    if not validate_file_size(len(file_bytes), MAX_UPLOAD_SIZE_MB):
        raise ValueError(
            f"Arquivo muito grande. Tamanho máximo: {MAX_UPLOAD_SIZE_MB}MB."
        )

    try:
        df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    except Exception as e:
        raise ValueError(f"Erro ao ler XLSX: {e}")

    if df.empty:
        raise ValueError("O arquivo XLSX está vazio.")

    return df, f"Arquivo '{filename}' carregado com sucesso: {len(df)} linhas, {len(df.columns)} colunas."


def load_file(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Detecta o tipo de arquivo e delega ao loader correto.

    Args:
        file_bytes: Conteúdo do arquivo em bytes.
        filename: Nome original do arquivo.

    Returns:
        Tupla (DataFrame, mensagem de sucesso).

    Raises:
        ValueError: Se o formato não for suportado.
    """
    lower = filename.lower()
    if lower.endswith(".csv"):
        return load_csv(file_bytes, filename)
    elif lower.endswith(".xlsx") or lower.endswith(".xls"):
        return load_xlsx(file_bytes, filename)
    else:
        raise ValueError(
            f"Formato '{filename.split('.')[-1]}' não suportado. Use .csv ou .xlsx."
        )
