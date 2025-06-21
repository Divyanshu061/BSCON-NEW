# File: app/utils/csv_parser.py
"""
app/utils/csv_parser.py

CSV parsing utility—reads CSV bytes and outputs transactions.
"""
from typing import List, Dict, Any
import csv
import io

def parse_csv(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parses CSV content into a list of dicts matching StatementItem fields.
    """
    text = file_bytes.decode('utf-8')
    reader = csv.DictReader(io.StringIO(text))
    results: List[Dict[str, Any]] = []
    for row in reader:
        results.append(dict(row))
    return results