"""Testes para todos os frameworks analíticos."""

import pandas as pd
import pytest

from app.analysis_frameworks import get_framework, FRAMEWORK_MAP


def _make_full_df():
    """DataFrame completo com datas, categorias e múltiplas métricas."""
    return pd.DataFrame({
        "data": pd.date_range("2024-01-01", periods=30, freq="10D"),
        "canal": (["organico", "pago", "email"] * 10),
        "produto": (["Basic", "Pro", "Enterprise"] * 10),
        "receita": [1000 + i * 50 for i in range(30)],
        "custo": [300 + i * 15 for i in range(30)],
        "conversoes": [10 + i for i in range(30)],
        "sessoes": [500 + i * 20 for i in range(30)],
    })


REQUIRED_SECTION_KEYS = {"title", "text", "data", "chart_config"}
REQUIRED_CHART_CONFIG_KEYS = {"chart_type", "x", "y", "title", "aggregation"}


def _validate_sections(sections: dict) -> None:
    """Valida estrutura de retorno de qualquer framework."""
    assert isinstance(sections, dict), "Retorno deve ser dict"
    assert len(sections) > 0, "Deve retornar ao menos uma seção"

    for key, section in sections.items():
        assert isinstance(section, dict), f"Seção '{key}' deve ser dict"
        for req_key in REQUIRED_SECTION_KEYS:
            assert req_key in section, f"Seção '{key}' falta campo '{req_key}'"

        chart_config = section["chart_config"]
        assert isinstance(chart_config, dict)
        for req_key in REQUIRED_CHART_CONFIG_KEYS:
            assert req_key in chart_config, f"chart_config falta '{req_key}'"

        assert isinstance(section["title"], str)
        assert isinstance(section["text"], str)
        assert isinstance(section["data"], pd.DataFrame)
        assert chart_config["chart_type"] in ("bar", "line", "pie", "scatter", "table")


class TestGetFramework:
    def test_returns_valid_framework(self):
        df = _make_full_df()
        for fw_id in FRAMEWORK_MAP.keys():
            fw = get_framework(fw_id, df)
            assert fw is not None

    def test_invalid_framework_raises(self):
        df = _make_full_df()
        with pytest.raises(ValueError, match="não encontrado"):
            get_framework("invalid_id", df)


class TestOodaFramework:
    def test_returns_four_sections(self):
        df = _make_full_df()
        fw = get_framework("ooda", df)
        sections = fw.analyze()
        assert "observe" in sections
        assert "orient" in sections
        assert "decide" in sections
        assert "act" in sections

    def test_section_structure_valid(self):
        df = _make_full_df()
        fw = get_framework("ooda", df)
        _validate_sections(fw.analyze())

    def test_text_not_empty(self):
        df = _make_full_df()
        fw = get_framework("ooda", df)
        for key, section in fw.analyze().items():
            assert len(section["text"]) > 10, f"Texto da seção '{key}' está vazio"


class TestFunnelFramework:
    def test_returns_funnel_sections(self):
        df = _make_full_df()
        fw = get_framework("funnel", df)
        sections = fw.analyze()
        assert "topo" in sections

    def test_section_structure_valid(self):
        df = _make_full_df()
        fw = get_framework("funnel", df)
        _validate_sections(fw.analyze())


class TestPerformanceFramework:
    def test_returns_performance_sections(self):
        df = _make_full_df()
        fw = get_framework("performance", df)
        sections = fw.analyze()
        assert "volume" in sections
        assert "eficiencia" in sections
        assert "qualidade" in sections

    def test_section_structure_valid(self):
        df = _make_full_df()
        fw = get_framework("performance", df)
        _validate_sections(fw.analyze())


class TestEdaFramework:
    def test_returns_eda_sections(self):
        df = _make_full_df()
        fw = get_framework("eda", df)
        sections = fw.analyze()
        assert "distribuicoes" in sections
        assert "correlacoes" in sections
        assert "outliers" in sections

    def test_section_structure_valid(self):
        df = _make_full_df()
        fw = get_framework("eda", df)
        _validate_sections(fw.analyze())


class TestTemporalFramework:
    def test_returns_temporal_sections(self):
        df = _make_full_df()
        fw = get_framework("temporal", df)
        sections = fw.analyze()
        assert "tendencia" in sections
        assert "crescimento" in sections
        assert "sazonalidade" in sections

    def test_section_structure_valid(self):
        df = _make_full_df()
        fw = get_framework("temporal", df)
        _validate_sections(fw.analyze())

    def test_without_date_column_returns_message(self):
        df = pd.DataFrame({
            "canal": ["a", "b", "c", "d", "e", "f", "g"],
            "receita": [100, 200, 300, 400, 500, 600, 700],
        })
        fw = get_framework("temporal", df)
        sections = fw.analyze()
        assert "tendencia" in sections
        assert "data" in sections["tendencia"]["title"].lower() or "Sem" in sections["tendencia"]["title"]


class TestAllFrameworksWithMinimalData:
    def test_handles_small_dataset(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        for fw_id in FRAMEWORK_MAP.keys():
            fw = get_framework(fw_id, df)
            sections = fw.analyze()
            assert isinstance(sections, dict)
            assert len(sections) > 0
