"""Inicialização e gerenciamento do banco de dados SQLite."""

import sqlite3
from pathlib import Path
from app.config.settings import DATABASE_PATH
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão com o banco de dados SQLite."""
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas necessárias se ainda não existirem."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                framework TEXT NOT NULL,
                source TEXT NOT NULL,
                source_name TEXT,
                path TEXT NOT NULL,
                n_rows INTEGER,
                n_cols INTEGER
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Banco de dados inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise
