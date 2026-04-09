"""Configurações globais da aplicação."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv(
    "GOOGLE_SHEETS_CREDENTIALS_PATH",
    str(BASE_DIR / "credentials" / "service_account.json")
)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(BASE_DIR / "data" / "reports.db")
)

PUBLISHED_REPORTS_DIR = os.getenv(
    "PUBLISHED_REPORTS_DIR",
    str(BASE_DIR / "data" / "published_reports")
)

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

APP_NAME = os.getenv("APP_NAME", "Report Generator")

TEMPLATES_DIR = str(BASE_DIR / "templates")
STATIC_DIR = str(BASE_DIR / "static")

SUPPORTED_FRAMEWORKS = {
    "ooda": "OODA Loop",
    "funnel": "Funil de Conversão",
    "performance": "Diagnóstico de Performance",
    "eda": "Análise Exploratória",
    "temporal": "Comparação Temporal",
}

CHART_TYPES = ["bar", "line", "pie", "scatter", "table"]
AGGREGATIONS = ["sum", "mean", "count", "max", "min"]
