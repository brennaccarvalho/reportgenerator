"""Testes para o gerador de insights automáticos."""

import pandas as pd
import pytest

from app.services.insight_generator import generate_insights


def _make_df():
    return pd.DataFrame({
        "canal": ["organico", "pago", "email", "direto", "organico", "pago"] * 5,
        "receita": [1000, 5000, 200, 800, 1200, 4500] * 5,
        "custo": [200, 1500, 80, 300, 250, 1200] * 5,
    })


class TestMaxMinInsights:
    def test_detects_max(self):
        df = _make_df()
        insights = generate_insights(df)
        types = [i["type"] for i in insights]
        assert "max" in types

    def test_detects_min(self):
        df = _make_df()
        insights = generate_insights(df)
        types = [i["type"] for i in insights]
        assert "min" in types

    def test_max_insight_has_required_fields(self):
        df = _make_df()
        insights = generate_insights(df)
        max_insights = [i for i in insights if i["type"] == "max"]
        assert len(max_insights) > 0
        for ins in max_insights:
            assert "title" in ins
            assert "description" in ins
            assert "severity" in ins


class TestConcentrationInsight:
    def test_detects_high_concentration(self):
        df = pd.DataFrame({
            "canal": ["pago"] * 18 + ["email"] * 2,
            "receita": [1000] * 18 + [10] * 2,
        })
        insights = generate_insights(df)
        types = [i["type"] for i in insights]
        assert "concentration" in types

    def test_no_concentration_when_balanced(self):
        df = pd.DataFrame({
            "canal": ["A"] * 10 + ["B"] * 10 + ["C"] * 10,
            "receita": [100] * 30,
        })
        insights = generate_insights(df)
        concentration = [i for i in insights if i["type"] == "concentration"]
        assert len(concentration) == 0


class TestOutlierInsight:
    def test_detects_outlier(self):
        receita = [100, 110, 105, 98, 102, 107, 99, 103, 5000, 101]
        df = pd.DataFrame({
            "canal": ["a"] * len(receita),
            "receita": receita,
        })
        insights = generate_insights(df)
        types = [i["type"] for i in insights]
        assert "outlier" in types

    def test_outlier_severity_is_valid(self):
        receita = [100, 110, 105, 98, 102, 107, 99, 103, 5000, 101]
        df = pd.DataFrame({
            "canal": ["a"] * len(receita),
            "receita": receita,
        })
        insights = generate_insights(df)
        for ins in insights:
            assert ins["severity"] in ("info", "warning", "critical")


class TestRankingInsight:
    def test_generates_ranking(self):
        df = _make_df()
        insights = generate_insights(df)
        types = [i["type"] for i in insights]
        assert "ranking" in types


class TestNoNumericCols:
    def test_handles_no_numeric_cols(self):
        df = pd.DataFrame({"canal": ["a", "b"], "produto": ["x", "y"]})
        insights = generate_insights(df)
        assert len(insights) >= 1
        assert insights[0]["type"] == "info"
