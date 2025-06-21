# backend/app/services/bank_specific/hdfc/parser.py
"""
from typing import Dict

def normalize(entry: Dict) -> Dict:
    
    Normalize HDFC bank entry.
    This can include standardizing date formats, fixing inconsistent descriptions, etc.
    
    # Example normalization logic
    entry["description"] = entry["description"].replace("POS", "Point Of Sale").strip()

    # You can adjust amount if needed based on description
    if "debit" in entry["description"].lower():
        entry["amount"] = -abs(entry["amount"])
    elif "credit" in entry["description"].lower():
        entry["amount"] = abs(entry["amount"])

    return entry
"""