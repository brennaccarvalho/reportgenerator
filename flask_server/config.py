"""Configuracoes do servidor Flask."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_DATABASE = (BASE_DIR / "data" / "reports.db").as_posix()


class Config:
    # Chave secreta para assinar cookies de sessao.
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-me-before-production")

    # Em Docker/producao, use PostgreSQL via DATABASE_URL.
    # Sem DATABASE_URL, cai para SQLite local para facilitar desenvolvimento.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{DEFAULT_SQLITE_DATABASE}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Limite de upload: 50 MB
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    # Pastas de armazenamento em disco
    UPLOAD_FOLDER = str(BASE_DIR / "data" / "uploads")
    PUBLISHED_REPORTS_DIR = str(BASE_DIR / "data" / "published_reports")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
