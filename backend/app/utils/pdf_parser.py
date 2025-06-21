# backend/app/utils/pdf_parser.py

import io
import pdfplumber
from typing import List, Dict, Any
import re


def parse_pdf(file_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parses a PDF bank statement and extracts transaction data.
    Assumes the table has some combination of date, description, amount/debit/credit, and balance columns.
    """
    transactions: List[Dict[str, Any]] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table or len(table) < 2:
                continue

            # Extract headers and normalize
            headers = [h.strip().lower() if h else "" for h in table[0]]
            for row in table[1:]:
                if len(row) < 2:
                    continue

                row_dict = dict(zip(headers, row))
                try:
                    date_str = row_dict.get("date", "").strip()
                    description = row_dict.get("description", row_dict.get("narration", "")).strip()
                    
                    # Handle possible split columns: debit/credit
                    debit = row_dict.get("debit", "").replace(",", "")
                    credit = row_dict.get("credit", "").replace(",", "")
                    amount = row_dict.get("amount", "").replace(",", "")

                    if debit:
                        amount_val = -float(debit)
                    elif credit:
                        amount_val = float(credit)
                    elif amount:
                        amount_val = float(amount)
                    else:
                        continue  # No valid amount

                    balance = row_dict.get("balance", row_dict.get("closing balance", "")).replace(",", "")
                    balance_val = float(balance) if balance else None

                    transactions.append({
                        "date": date_str,
                        "description": description,
                        "amount": amount_val,
                        "balance": balance_val
                    })

                except Exception:
                    continue  # Skip unparseable row

    return transactions
