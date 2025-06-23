# File: backend/app/routers/convert.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
import pandas as pd
import pdfplumber

from app.core.deps import get_db, get_current_user
from app.services.parser import ParserService
from app import crud, models

router = APIRouter(
    tags=["Convert"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/file", status_code=status.HTTP_201_CREATED)
async def convert_file_and_persist(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Accept an uploaded PDF or CSV bank statement, parse it, persist to DB,
    and return an XLSX download stream.
    Deduct credits (1 per PDF page) and record conversion history.
    """
    original_name = file.filename
    ext = original_name.lower().split('.')[-1]
    if ext not in ("pdf", "csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Only PDF or CSV allowed.",
        )

    raw_bytes = await file.read()
    page_count = 0

    # Pre-flight: count pages and ensure credits for PDFs
    if ext == "pdf":
        try:
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                page_count = len(pdf.pages)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unable to read PDF file for page count.",
            )
        if current_user.credits_remaining < page_count:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(f"Not enough credits: you need {page_count} "
                        f"but have {current_user.credits_remaining}."),
            )

    # 1. Parse file
    try:
        items: List[models.StatementItem] = ParserService.parse_file(raw_bytes, original_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    # 2. Persist statement
    db_statement = crud.create_statement(
        db=db,
        user_id=current_user.id,
        original_filename=original_name,
        fmt=ext,
    )
    tx_dicts = []
    for item in items:
        d = item.dict()
        if d.get("debit") is not None:
            d["amount"] = -float(d["debit"] )  # debit = negative amount
        elif d.get("credit") is not None:
            d["amount"] = float(d["credit"])  # credit = positive amount
        else:
            continue
        tx_dicts.append(d)

    crud.create_transactions(db, statement_id=db_statement.id, transactions=tx_dicts)

    # 3. Mark processed and handle credits & history
    db_statement.processed = True
    crud.mark_statement_processed(db, db_statement)

    if ext == "pdf" and page_count > 0:
        # Deduct credits
        crud.decrement_credits(db, current_user.id, page_count)
        # Record conversion in history
        crud.create_conversion_history(
            db=db,
            user_id=current_user.id,
            description=f"Converted {original_name} ({page_count} pages)",
            pages_converted=page_count,
            credits_spent=page_count
        )

    # 4. Build DataFrame and stream Excel
    df = pd.DataFrame(tx_dicts)

    # ensure both debit and credit columns exist, filling None/NaN with empty strings
    df["debit"] = df["debit"].fillna("")
    df["credit"] = df["credit"].fillna("")

    # pick and order columns as you want
    df = df[["date", "description", "debit", "credit", "balance", "ref_no"]]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    output.seek(0)

    headers = {"Content-Disposition": f"attachment; filename={db_statement.file_id}.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
