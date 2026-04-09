"""Serviço de carregamento de dados via Google Sheets."""

from typing import List, Tuple

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

from app.config.settings import GOOGLE_SHEETS_CREDENTIALS_PATH
from app.utils.logger import get_logger
from app.utils.validators import validate_google_sheets_url

logger = get_logger(__name__)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def _get_client() -> gspread.Client:
    """Autentica e retorna um cliente gspread."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_SHEETS_CREDENTIALS_PATH, SCOPES
        )
        return gspread.authorize(creds)
    except FileNotFoundError:
        raise ValueError(
            "Arquivo de credenciais não encontrado. "
            "Configure GOOGLE_SHEETS_CREDENTIALS_PATH no .env."
        )
    except Exception as e:
        raise ValueError(f"Erro ao autenticar no Google Sheets: {e}")


def list_sheets(url: str) -> List[str]:
    """
    Lista as abas disponíveis em uma planilha Google Sheets.

    Args:
        url: URL completa da planilha.

    Returns:
        Lista com os nomes das abas.

    Raises:
        ValueError: Se a URL for inválida ou sem permissão.
    """
    spreadsheet_id = validate_google_sheets_url(url)
    if not spreadsheet_id:
        raise ValueError("URL do Google Sheets inválida.")

    client = _get_client()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        return [ws.title for ws in spreadsheet.worksheets()]
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError("Planilha não encontrada. Verifique as permissões de compartilhamento.")
    except Exception as e:
        raise ValueError(f"Erro ao acessar planilha: {e}")


def load_sheet(url: str, sheet_name: str) -> Tuple[pd.DataFrame, str]:
    """
    Carrega uma aba específica do Google Sheets.

    Args:
        url: URL completa da planilha.
        sheet_name: Nome da aba a carregar.

    Returns:
        Tupla (DataFrame, mensagem de sucesso).

    Raises:
        ValueError: Em caso de erro de acesso ou dados inválidos.
    """
    spreadsheet_id = validate_google_sheets_url(url)
    if not spreadsheet_id:
        raise ValueError("URL do Google Sheets inválida.")

    client = _get_client()
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        records = worksheet.get_all_records()

        if not records:
            raise ValueError(f"A aba '{sheet_name}' está vazia.")

        df = pd.DataFrame(records)
        return df, (
            f"Aba '{sheet_name}' carregada com sucesso: "
            f"{len(df)} linhas, {len(df.columns)} colunas."
        )
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(f"Aba '{sheet_name}' não encontrada.")
    except Exception as e:
        raise ValueError(f"Erro ao carregar aba: {e}")
