"""Serviço de publicação de relatórios locais."""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.config.db import get_connection, init_db
from app.config.settings import PUBLISHED_REPORTS_DIR
from app.services.report_renderer import render_html
from app.utils.logger import get_logger

logger = get_logger(__name__)


def publish_report(
    name: str,
    framework_id: str,
    sections: Dict[str, Any],
    insights: List[Dict[str, Any]],
    df: pd.DataFrame,
    source: str,
    source_name: str,
) -> str:
    """
    Publica um relatório como HTML estático e registra no SQLite.

    Args:
        name: Nome do relatório.
        framework_id: ID do framework usado.
        sections: Seções analíticas geradas.
        insights: Lista de insights automáticos.
        df: DataFrame processado.
        source: Tipo de fonte ('upload' ou 'google_sheets').
        source_name: Nome do arquivo ou URL de origem.

    Returns:
        ID único do relatório publicado.

    Raises:
        RuntimeError: Se a publicação falhar.
    """
    init_db()

    report_id = str(uuid.uuid4())

    # Garantir diretório de publicação
    Path(PUBLISHED_REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    html_path = os.path.join(PUBLISHED_REPORTS_DIR, f"{report_id}.html")

    # Renderizar HTML
    try:
        html_bytes = render_html(
            report_name=name,
            framework_id=framework_id,
            sections=sections,
            insights=insights,
            df=df,
        )
        with open(html_path, "wb") as f:
            f.write(html_bytes)
        logger.info(f"Relatório HTML salvo em: {html_path}")
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar HTML do relatório: {e}")

    # Registrar no banco
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO reports (id, name, framework, source, source_name, path, n_rows, n_cols)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                name,
                framework_id,
                source,
                source_name,
                html_path,
                len(df),
                len(df.columns),
            ),
        )
        conn.commit()
        conn.close()
        logger.info(f"Relatório registrado no banco: id={report_id}")
    except Exception as e:
        raise RuntimeError(f"Erro ao registrar relatório no banco: {e}")

    return report_id
