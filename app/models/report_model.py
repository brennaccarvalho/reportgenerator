"""Dataclasses e modelos de dados do Report Generator."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class ColumnProfile:
    """Perfil de uma coluna do dataset."""
    name: str
    inferred_type: str
    null_count: int
    null_pct: float
    unique_count: int
    sample_values: List[Any]


@dataclass
class DataProfile:
    """Perfil completo do dataset."""
    n_rows: int
    n_cols: int
    columns: List[ColumnProfile]
    issues: List[str]
    transformations_log: List[str]


@dataclass
class ChartConfig:
    """Configuração de um gráfico."""
    chart_type: str  # bar, line, pie, scatter, table
    x: str
    y: str
    title: str
    aggregation: str = "sum"  # sum, mean, count, max, min
    sort_order: Optional[str] = None  # asc, desc
    top_n: Optional[int] = None
    color: Optional[str] = None


@dataclass
class ReportSection:
    """Seção de um relatório gerado por um framework."""
    section_key: str
    title: str
    text: str
    chart_config: ChartConfig
    data_summary: Optional[Dict[str, Any]] = None


@dataclass
class Insight:
    """Insight gerado automaticamente."""
    type: str  # max, min, concentration, outlier, correlation, ranking
    title: str
    description: str
    severity: str  # info, warning, critical


@dataclass
class ReportConfig:
    """Configuração completa de um relatório."""
    name: str
    framework_id: str
    dimensions: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    groupby: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PublishedReport:
    """Registro de um relatório publicado."""
    id: str
    name: str
    created_at: datetime
    framework: str
    source: str  # upload ou google_sheets
    source_name: Optional[str]
    path: str
    n_rows: int
    n_cols: int
