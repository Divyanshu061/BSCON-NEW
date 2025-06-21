# File: backend/app/services/bank_specific/__init__.py

BANK_KEYWORDS = {
    "sbi": ["state bank of india", "sbi"],
    "hdfc": ["hdfc bank"],
    "icici": ["icici bank"],
    "axis": ["axis bank"],
    "kotak": ["kotak bank"],
    "yes": ["yes bank"],
}

def detect_bank(text: str) -> str:
    text = text.lower()
    for bank, keywords in BANK_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return bank
    return "unknown"
