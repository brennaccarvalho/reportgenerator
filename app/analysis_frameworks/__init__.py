"""Pacote de frameworks analíticos do Report Generator."""

from app.analysis_frameworks.ooda_framework import OodaFramework
from app.analysis_frameworks.funnel_framework import FunnelFramework
from app.analysis_frameworks.performance_framework import PerformanceFramework
from app.analysis_frameworks.eda_framework import EdaFramework
from app.analysis_frameworks.temporal_framework import TemporalFramework

FRAMEWORK_MAP = {
    "ooda": OodaFramework,
    "funnel": FunnelFramework,
    "performance": PerformanceFramework,
    "eda": EdaFramework,
    "temporal": TemporalFramework,
}


def get_framework(framework_id: str, df):
    """
    Retorna instância do framework correspondente ao ID.

    Args:
        framework_id: ID do framework (ooda, funnel, performance, eda, temporal).
        df: DataFrame processado.

    Returns:
        Instância do framework.

    Raises:
        ValueError: Se o framework_id não for reconhecido.
    """
    if framework_id not in FRAMEWORK_MAP:
        raise ValueError(
            f"Framework '{framework_id}' não encontrado. "
            f"Opções: {list(FRAMEWORK_MAP.keys())}"
        )
    return FRAMEWORK_MAP[framework_id](df)
