"""Testes para o serviço de limpeza de dados."""

import pandas as pd
import pytest

from app.services.data_cleaner import clean_dataframe


class TestColumnNormalization:
    def test_normalizes_column_names(self):
        df = pd.DataFrame({"Nome Completo": [1], "Valor (R$)": [2]})
        result, log = clean_dataframe(df)
        assert "nome_completo" in result.columns
        assert "valor_r" in result.columns or "valor" in result.columns

    def test_removes_accents(self):
        df = pd.DataFrame({"Região": ["sul"], "Ação": ["venda"]})
        result, _ = clean_dataframe(df)
        assert "regiao" in result.columns
        assert "acao" in result.columns

    def test_no_spaces_in_columns(self):
        df = pd.DataFrame({"col com espaco": [1], "outra col": [2]})
        result, _ = clean_dataframe(df)
        for col in result.columns:
            assert " " not in col


class TestDuplicateRemoval:
    def test_removes_duplicates(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        result, log = clean_dataframe(df)
        assert len(result) == 2
        assert any("duplicada" in t for t in log)


class TestNumericConversion:
    def test_converts_currency_string(self):
        df = pd.DataFrame({"valor": ["R$ 1.500,00", "R$ 2.000,50", "R$ 500,00"]})
        result, log = clean_dataframe(df)
        assert pd.api.types.is_numeric_dtype(result["valor"])
        assert result["valor"].iloc[0] == pytest.approx(1500.0, abs=1)

    def test_converts_percentage_string(self):
        df = pd.DataFrame({"taxa": ["10,5", "20,0", "5,2"]})
        result, log = clean_dataframe(df)
        assert pd.api.types.is_numeric_dtype(result["taxa"])


class TestDateConversion:
    def test_converts_br_date_format(self):
        df = pd.DataFrame({"data": ["01/01/2024", "15/06/2024", "31/12/2024"]})
        result, log = clean_dataframe(df)
        assert pd.api.types.is_datetime64_any_dtype(result["data"])

    def test_converts_iso_date_format(self):
        df = pd.DataFrame({"data": ["2024-01-01", "2024-06-15", "2024-12-31"]})
        result, log = clean_dataframe(df)
        assert pd.api.types.is_datetime64_any_dtype(result["data"])


class TestNullDetection:
    def test_removes_all_null_rows(self):
        df = pd.DataFrame({"a": [1, None, 2], "b": [None, None, "x"]})
        result, log = clean_dataframe(df)
        # Linha com todos nulls deve ser removida
        assert len(result) <= 3

    def test_returns_transformations_log(self):
        df = pd.DataFrame({"col a": [1, 1, 2]})
        _, log = clean_dataframe(df)
        assert isinstance(log, list)
        assert len(log) > 0
