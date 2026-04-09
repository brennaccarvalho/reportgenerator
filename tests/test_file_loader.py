"""Testes para o serviço de carregamento de arquivos."""

import io
import pytest
import pandas as pd


def _make_csv_bytes(data: dict) -> bytes:
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def _make_xlsx_bytes(data: dict) -> bytes:
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


class TestLoadCSV:
    def test_load_valid_csv(self):
        from app.services.file_loader import load_csv
        data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
        csv_bytes = _make_csv_bytes(data)
        df, msg = load_csv(csv_bytes, "test.csv")
        assert len(df) == 3
        assert "col1" in df.columns
        assert "test.csv" in msg

    def test_load_csv_returns_dataframe(self):
        from app.services.file_loader import load_csv
        data = {"x": [10, 20], "y": [30, 40]}
        csv_bytes = _make_csv_bytes(data)
        df, _ = load_csv(csv_bytes, "data.csv")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

    def test_load_csv_too_large_raises(self):
        from app.services.file_loader import load_csv
        big_bytes = b"x" * (60 * 1024 * 1024)  # 60MB
        with pytest.raises(ValueError, match="muito grande"):
            load_csv(big_bytes, "big.csv")


class TestLoadXLSX:
    def test_load_valid_xlsx(self):
        from app.services.file_loader import load_xlsx
        data = {"produto": ["A", "B"], "valor": [100, 200]}
        xlsx_bytes = _make_xlsx_bytes(data)
        df, msg = load_xlsx(xlsx_bytes, "test.xlsx")
        assert len(df) == 2
        assert "produto" in df.columns

    def test_load_xlsx_returns_dataframe(self):
        from app.services.file_loader import load_xlsx
        data = {"n": [1, 2, 3]}
        xlsx_bytes = _make_xlsx_bytes(data)
        df, _ = load_xlsx(xlsx_bytes, "file.xlsx")
        assert isinstance(df, pd.DataFrame)


class TestLoadFile:
    def test_unsupported_format_raises(self):
        from app.services.file_loader import load_file
        with pytest.raises(ValueError, match="não suportado"):
            load_file(b"data", "file.json")

    def test_dispatch_csv(self):
        from app.services.file_loader import load_file
        data = {"a": [1, 2]}
        csv_bytes = _make_csv_bytes(data)
        df, _ = load_file(csv_bytes, "data.csv")
        assert isinstance(df, pd.DataFrame)

    def test_dispatch_xlsx(self):
        from app.services.file_loader import load_file
        data = {"b": [3, 4]}
        xlsx_bytes = _make_xlsx_bytes(data)
        df, _ = load_file(xlsx_bytes, "data.xlsx")
        assert isinstance(df, pd.DataFrame)
