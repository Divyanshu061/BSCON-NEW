# File: backend/app/routers/convert.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
import io
import pdfplumber

from app.core.deps import get_db, get_current_user
from app.schemas import StatementItem, ConversionResponse, TransactionOut
from app.services.parser import ParserService
from app import crud, models

router = APIRouter(
    tags=["Convert"],
    dependencies=[Depends(get_current_user)],
)

@router.post(
    "/file",
    response_model=ConversionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def convert_file_and_persist(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Accept an uploaded PDF or CSV bank statement, parse it, persist to DB,
    and return the new file_id for history/retrieval.
    Deduct credits (1 per PDF page) only after successful conversion.
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
        # Use the correct attribute for credits
        if current_user.credits_remaining < page_count:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=(f"Not enough credits: you need {page_count} "
                        f"but have {current_user.credits_remaining}."),
            )

    # 1. Parse file
    try:
        items: List[StatementItem] = ParserService.parse_file(raw_bytes, original_name)
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
    tx_dicts = [item.dict() for item in items]
    crud.create_transactions(db, statement_id=db_statement.id, transactions=tx_dicts)

    # 3. Mark processed and deduct credits post-success
    # Ensure we track processed flag and timestamp
    db_statement.processed = True
    crud.mark_statement_processed(db, db_statement)

    if ext == "pdf" and page_count > 0:
        crud.decrement_credits(db, current_user.id, page_count)

    return ConversionResponse(download_url=f"{db_statement.file_id}")
