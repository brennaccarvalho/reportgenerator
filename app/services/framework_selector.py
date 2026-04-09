"""Serviço de seleção e execução de frameworks analíticos."""

from typing import Any, Dict

import pandas as pd

from app.analysis_frameworks import get_framework
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_framework(framework_id: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executa o framework selecionado e retorna as seções analíticas.

    Args:
        framework_id: ID do framework (ooda, funnel, performance, eda, temporal).
        df: DataFrame processado.

    Returns:
        Dicionário de seções analíticas.

    Raises:
        ValueError: Se o framework não existir ou ocorrer erro na análise.
    """
    try:
        framework = get_framework(framework_id, df)
        result = framework.analyze()
        logger.info(
            f"Framework '{framework_id}' executado: {len(result)} seção(ões) gerada(s)."
        )
        return result
    except Exception as e:
        logger.error(f"Erro ao executar framework '{framework_id}': {e}")
        raise
