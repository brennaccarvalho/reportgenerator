"""
Testes para MeridianFramework — apenas métodos que não dependem de GPU/TensorFlow.
"""
import sys
import os
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Garante que o project root está no path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Verificar se o módulo existe
try:
    from app.analysis_frameworks.meridian_framework import MeridianFramework, MERIDIAN_AVAILABLE
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False
    MeridianFramework = None
    MERIDIAN_AVAILABLE = False

# Pular todos os testes se o módulo não existe
pytestmark = pytest.mark.skipif(not MODULE_EXISTS, reason="meridian_framework.py não encontrado")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def df_portugues():
    """DataFrame com nomes de colunas em português."""
    n = 60
    return pd.DataFrame({
        "data": pd.date_range("2023-01-01", periods=n, freq="W"),
        "vendas": np.random.randint(1000, 10000, n),
        "gasto_tv": np.random.uniform(5000, 20000, n),
        "gasto_digital": np.random.uniform(2000, 10000, n),
        "custo_radio": np.random.uniform(1000, 5000, n),
        "impressoes_tv": np.random.uniform(100000, 500000, n),
        "alcance_digital": np.random.uniform(50000, 200000, n),
        "temperatura": np.random.uniform(15, 35, n),  # controle
    })


@pytest.fixture
def df_ingles():
    """DataFrame com nomes de colunas em inglês."""
    n = 80
    return pd.DataFrame({
        "date": pd.date_range("2022-01-01", periods=n, freq="W"),
        "revenue": np.random.randint(5000, 50000, n),
        "tv_spend": np.random.uniform(10000, 40000, n),
        "digital_spend": np.random.uniform(5000, 20000, n),
        "tv_impressions": np.random.uniform(200000, 800000, n),
        "clicks": np.random.uniform(10000, 50000, n),
        "seasonality": np.random.uniform(0, 1, n),  # controle
    })


@pytest.fixture
def df_sem_midia():
    """DataFrame sem colunas de mídia identificáveis."""
    n = 60
    return pd.DataFrame({
        "periodo": pd.date_range("2023-01-01", periods=n, freq="W"),
        "resultado": np.random.randint(100, 1000, n),
        "temperatura": np.random.uniform(15, 35, n),
        "umidade": np.random.uniform(40, 90, n),
        "vento": np.random.uniform(0, 30, n),
    })


@pytest.fixture
def column_mapping_valido(df_portugues):
    """Mapeamento de colunas válido para df_portugues."""
    return {
        "kpi": "vendas",
        "media_spend": ["gasto_tv", "gasto_digital", "custo_radio"],
        "media_impressions": ["impressoes_tv", "alcance_digital"],
        "date_col": "data",
        "controls": ["temperatura"],
    }


@pytest.fixture
def mock_results():
    """Resultado mockado para testar generate_html_report sem GPU."""
    return {
        "roi_by_channel": {
            "gasto_tv": {"mean": 1.5, "lower": 0.8, "upper": 2.2},
            "gasto_digital": {"mean": 2.1, "lower": 1.2, "upper": 3.0},
            "custo_radio": {"mean": 0.7, "lower": 0.3, "upper": 1.1},
        },
        "contribution_by_channel": {
            "gasto_tv": 0.35,
            "gasto_digital": 0.28,
            "custo_radio": 0.12,
        },
        "baseline_contribution": 0.25,
        "total_revenue_decomposition": {},
        "model_fit_r2": 0.87,
    }


@pytest.fixture
def mock_metadata():
    """Metadados mockados do treino."""
    return {
        "tempo_segundos": 1800.0,
        "n_chains": 4,
        "n_adapt": 1000,
        "n_burnin": 500,
        "n_keep": 500,
        "timestamp": "2024-01-01T12:00:00",
    }


# ─── Testes ────────────────────────────────────────────────────────────────────

class TestDetectColumnsPT:
    """Testes de detecção com nomes em português."""

    def test_detect_columns_com_nomes_em_portugues(self, df_portugues):
        fw = MeridianFramework()
        result = fw.detect_columns(df_portugues)

        assert isinstance(result, dict)
        assert "kpi" in result
        assert "media_spend" in result
        assert "media_impressions" in result
        assert "date_col" in result
        assert "controls" in result
        assert "has_minimum_columns" in result

        # Deve detectar vendas como KPI
        assert result["kpi"]["column"] == "vendas"

        # Deve detectar colunas de spend
        spend_cols = result["media_spend"]["columns"]
        assert len(spend_cols) > 0
        assert any("gasto" in c or "custo" in c for c in spend_cols)

        # Deve detectar coluna de data
        assert result["date_col"]["column"] == "data"

        # Deve ter mínimo de colunas
        assert result["has_minimum_columns"] is True


class TestDetectColumnsEN:
    """Testes de detecção com nomes em inglês."""

    def test_detect_columns_com_nomes_em_ingles(self, df_ingles):
        fw = MeridianFramework()
        result = fw.detect_columns(df_ingles)

        assert isinstance(result, dict)

        # Deve detectar revenue como KPI
        assert result["kpi"]["column"] == "revenue"

        # Deve detectar colunas com 'spend'
        spend_cols = result["media_spend"]["columns"]
        assert len(spend_cols) > 0
        assert any("spend" in c for c in spend_cols)

        # Deve detectar impressions/clicks
        impression_cols = result["media_impressions"]["columns"]
        assert len(impression_cols) > 0

        # Deve detectar coluna de data
        assert result["date_col"]["column"] == "date"

        # Deve ter mínimo de colunas
        assert result["has_minimum_columns"] is True


class TestDetectColumnsSemMidia:
    """Testes de detecção sem colunas de mídia."""

    def test_detect_columns_sem_colunas_de_midia(self, df_sem_midia):
        fw = MeridianFramework()
        result = fw.detect_columns(df_sem_midia)

        assert isinstance(result, dict)

        # Não deve ter spend detectado
        spend_cols = result.get("media_spend", {}).get("columns", [])
        assert len(spend_cols) == 0

        # Deve indicar que não tem mínimo de colunas
        assert result.get("has_minimum_columns") is False

        # Deve ter mensagem explicativa
        assert result.get("message") is not None
        assert len(result["message"]) > 0


class TestValidateData:
    """Testes de validação de dados."""

    def test_validate_data_dados_insuficientes(self):
        fw = MeridianFramework()
        # DataFrame com menos de 52 linhas
        n = 20
        df_pequeno = pd.DataFrame({
            "vendas": np.random.randint(100, 1000, n),
            "gasto_tv": np.random.uniform(1000, 5000, n),
        })
        mapping = {
            "kpi": "vendas",
            "media_spend": ["gasto_tv"],
            "media_impressions": [],
            "date_col": None,
            "controls": [],
        }

        result = fw.validate_data(df_pequeno, mapping)

        assert isinstance(result, dict)
        assert "errors" in result
        assert "warnings" in result
        assert "valid" in result

        # Com 20 linhas, deve ter erro de dados insuficientes
        assert len(result["errors"]) > 0
        assert result["valid"] is False

        # A mensagem de erro deve mencionar linhas ou semanas
        error_text = " ".join(result["errors"])
        assert "linhas" in error_text.lower() or "52" in error_text or "insuficiente" in error_text.lower()

    def test_validate_data_kpi_negativo(self):
        fw = MeridianFramework()
        n = 60
        df_neg = pd.DataFrame({
            "vendas": [-100] * 10 + list(np.random.randint(100, 1000, n - 10)),
            "gasto_tv": np.random.uniform(1000, 5000, n),
            "gasto_digital": np.random.uniform(500, 3000, n),
        })
        mapping = {
            "kpi": "vendas",
            "media_spend": ["gasto_tv", "gasto_digital"],
            "media_impressions": [],
            "date_col": None,
            "controls": [],
        }

        result = fw.validate_data(df_neg, mapping)

        assert result["valid"] is False
        error_text = " ".join(result["errors"])
        assert "negativo" in error_text.lower() or "negat" in error_text.lower()

    def test_validate_data_muitos_nulos(self):
        fw = MeridianFramework()
        n = 60
        # Coluna de KPI com >20% de nulos
        kpi_values = [None] * 15 + list(np.random.randint(100, 1000, n - 15))
        df_nulos = pd.DataFrame({
            "vendas": kpi_values,
            "gasto_tv": np.random.uniform(1000, 5000, n),
        })
        mapping = {
            "kpi": "vendas",
            "media_spend": ["gasto_tv"],
            "media_impressions": [],
            "date_col": None,
            "controls": [],
        }

        result = fw.validate_data(df_nulos, mapping)

        assert result["valid"] is False
        error_text = " ".join(result["errors"])
        assert "nulos" in error_text.lower() or "null" in error_text.lower() or "20" in error_text


class TestGenerateHtmlReport:
    """Testes de geração do relatório HTML."""

    def test_generate_html_report_estrutura_basica(self, mock_results, mock_metadata):
        fw = MeridianFramework()

        # Gera charts com resultados mockados (sem GPU)
        charts = fw.generate_charts(mock_results)

        html = fw.generate_html_report(
            results=mock_results,
            charts=charts,
            optimization_results=None,
            metadata=mock_metadata,
        )

        # Deve retornar string HTML válida
        assert isinstance(html, str)
        assert len(html) > 100

        # Deve ter estrutura HTML básica
        assert "<!DOCTYPE html>" in html or "<html" in html
        assert "<head>" in html
        assert "<body>" in html

        # Deve mencionar "Media Mix" ou "MMM" ou "Meridian"
        assert any(kw in html for kw in ["Media Mix", "MMM", "Meridian", "meridian"])

        # Deve ter ROI dos canais
        assert "gasto_tv" in html or "TV" in html
        assert "gasto_digital" in html or "Digital" in html
