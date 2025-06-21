# File: backend/app/services/bank_specific/sbi/parse.py

from typing import List
from decimal import Decimal
from datetime import datetime
import io
import logging
import pdfplumber
import pandas as pd
from app.schemas import StatementItem

logger = logging.getLogger(__name__)

EXPECTED_HEADERS = {"date", "narration", "ref_no", "debit", "credit", "balance"}

HEADER_ALIASES = {
    "date": [
        "date",
        "txn date",
        "transaction date",
        "value date",
        "date(value date)",
        "date (value date)",
        "posting date",
        "date\n(value date)",  # multiline headers
        "transaction\n date",
        "date value"
    ],
    "narration": [
        "narration",
        "description",
        "particulars",
        "transaction details",
        "details",
        "narration/description",
        "transaction\nparticulars"
    ],
    "ref_no": [
        "ref/chequeno.",
        "ref/cheque no.",
        "ref no",
        "ref",
        "cheque no.",
        "cheque no",
        "instrument no",
        "transaction id",
        "utr no",
        "reference no",
        "utr/reference no",
        "ref. no"
    ],
    "debit": [
        "debit",
        "withdrawal",
        "withdrawn",
        "dr",
        "amount withdrawn",
        "debit amount",
        "debit\namount",
        "withdrawal amount"
    ],
    "credit": [
        "credit",
        "deposit",
        "cr",
        "amount deposited",
        "credit amount",
        "credit\namount"
    ],
    "balance": [
        "balance",
        "available balance",
        "closing balance",
        "balanceamount",
        "running balance",
        "balance\namount",
        "available\nbalance"
    ]
}


def _normalize_header(text: str) -> str:
    return (
        text.lower()
        .strip()
        .replace("\n", "")
        .replace(" ", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
    )


def _map_header(raw_headers: List[str]) -> dict:
    normalized_to_raw = {_normalize_header(h): h for h in raw_headers}
    mapped = {}

    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            norm_alias = alias.replace(" ", "")
            if norm_alias in normalized_to_raw:
                mapped[field] = normalized_to_raw[norm_alias]
                break
            
    if not EXPECTED_HEADERS.issubset(mapped.keys()):
        logger.warning(f"[SBI] Could not map headers from: {raw_headers}")
        return {}

    return mapped if EXPECTED_HEADERS.issubset(mapped.keys()) else {}


def parse_sbi(file_bytes: bytes) -> List[StatementItem]:
    items: List[StatementItem] = []
    last_valid_header = None
    last_valid_header_map = None

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            logger.debug(f"[SBI] Page {i}: Found {len(tables or [])} tables")

            for table_index, table in enumerate(tables or [], start=1):
                rows = [[cell.strip() if cell else "" for cell in row] for row in table]
                if not rows or len(rows) < 1:
                    continue

                raw_header = rows[0]
                header_map = _map_header(raw_header)

                # If this table has a valid header
                if header_map:
                    logger.debug(f"[SBI] Matching header found → mapped as: {header_map}")
                    last_valid_header = raw_header
                    last_valid_header_map = header_map
                    data_rows = rows[1:]
                # Else use previous valid header
                elif last_valid_header and last_valid_header_map:
                    logger.debug(f"[SBI] No header found — using last known header for Page {i}, Table {table_index}")
                    raw_header = last_valid_header
                    header_map = last_valid_header_map
                    data_rows = rows  # treat whole table as data
                else:
                    logger.debug(f"[SBI] Skipping table — no valid or fallback header: {raw_header}")
                    continue

                try:
                    df = pd.DataFrame(data_rows, columns=raw_header)
                    df = df.rename(columns={
                        header_map["date"]: "date",
                        header_map["narration"]: "description",
                        header_map["ref_no"]: "ref_no",
                        header_map["debit"]: "debit",
                        header_map["credit"]: "credit",
                        header_map["balance"]: "balance"
                    })
                    df = df[df["date"].notna()]

                    for _, row in df.iterrows():
                        try:
                            date_str = row["date"].strip().split("\n")[0]
                            date = datetime.strptime(date_str, "%d-%b-%y").date()

                            desc = row["description"].strip()
                            ref_no = row["ref_no"].strip()

                            debit = (
                                Decimal(row["debit"].replace(",", ""))
                                if row.get("debit") and row["debit"].strip()
                                else None
                            )
                            credit = (
                                Decimal(row["credit"].replace(",", ""))
                                if row.get("credit") and row["credit"].strip()
                                else None
                            )
                            balance = Decimal(row["balance"].replace(",", ""))

                            items.append(StatementItem(
                                date=date,
                                description=desc,
                                ref_no=ref_no,
                                debit=debit,
                                credit=credit,
                                balance=balance
                            ))
                        except Exception as e:
                            logger.warning(f"[SBI] Skipping row due to parse error: {e} — {row}", exc_info=True)

                except Exception as df_err:
                    logger.error(f"[SBI] Error while processing table: {df_err}", exc_info=True)

    logger.info(f"[SBI] Total transactions parsed: {len(items)}")
    return items
