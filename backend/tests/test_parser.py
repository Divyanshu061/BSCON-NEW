# File: backend/tests/test_parser.py

import os
import sys
import pytest
from datetime import date

# ──────────────────────────────────────────────────────────────────────────────
# Ensure that “backend/” is on Python’s import path so “import app…” works.
# This assumes this test lives in backend/tests/.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# ──────────────────────────────────────────────────────────────────────────────

from app.services.parser import ParserService
from app.schemas import StatementItem


def test_parse_csv_basic():
    """
    Create an in-memory CSV, parse it with ParserService.parse_file, and verify output.
    """
    sample_csv = (
        "Date,Description,Amount,Balance\n"
        "2024-01-01,Test Transaction A,100.50,500.00\n"
        "01/02/2024,Test Transaction B,-50.25,449.75\n"
    )
    csv_bytes = sample_csv.encode("utf-8")

    items = ParserService.parse_file(csv_bytes, "sample.csv")
    assert isinstance(items, list)
    assert len(items) == 2

    first = items[0]
    assert isinstance(first, StatementItem)
    assert first.date == date(2024, 1, 1)
    assert first.description == "Test Transaction A"
    assert float(first.amount) == 100.50
    assert float(first.balance) == 500.00

    second = items[1]
    # “01/02/2024” → February 1, 2024 (as per our parser)
    assert second.date == date(2024, 2, 1)
    assert second.description == "Test Transaction B"
    assert float(second.amount) == -50.25
    assert float(second.balance) == 449.75


@pytest.mark.skip("Place a real PDF at backend/tests/data/sample_statement.pdf to enable")
def test_parse_pdf_sample():
    """
    Place a sample PDF at backend/tests/data/sample_statement.pdf,
    then remove the @pytest.mark.skip to validate PDF parsing.
    """
    pdf_path = os.path.join(ROOT_DIR, "tests", "data", "sample_statement.pdf")
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    items = ParserService.parse_file(pdf_bytes, "sample_statement.pdf")
    assert isinstance(items, list)
    assert len(items) > 0
    for record in items:
        assert isinstance(record, StatementItem)
        assert record.amount is not None
        assert record.date is not None


def test_parse_csv_error_handling():
    """
    Malformed CSV content should raise ValueError.
    """
    bad_csv = "Not a real,CSV"
    with pytest.raises(ValueError):
        ParserService.parse_file(bad_csv.encode("utf-8"), "bad.csv")


def test_parse_file_unsupported_extension():
    """
    If an unsupported extension is passed, ValueError should be raised.
    """
    dummy_bytes = b""
    with pytest.raises(ValueError):
        ParserService.parse_file(dummy_bytes, "file.unsupported")
