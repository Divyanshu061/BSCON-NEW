# File: backend/app/routers/convert.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Literal

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
    """
    original_name = file.filename
    ext = original_name.lower().split('.')[-1]
    if ext not in ("pdf", "csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Only PDF or CSV allowed.",
        )

    raw_bytes = await file.read()
    try:
        items: List[StatementItem] = ParserService.parse_file(raw_bytes, original_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    db_statement = crud.create_statement(
        db=db,
        user_id=current_user.id,
        original_filename=original_name,
        fmt=ext,
    )

    tx_dicts = [item.dict() for item in items]
    crud.create_transactions(db, statement_id=db_statement.id, transactions=tx_dicts)
    crud.mark_statement_processed(db, db_statement)

    return ConversionResponse(download_url=f"{db_statement.file_id}")

@router.get(
    "/history/{file_id}",
    response_model=List[TransactionOut],
    status_code=status.HTTP_200_OK,
)
def get_converted_history(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Retrieve all transactions for a given file_id (statement) and return them as JSON.
    """
    stmt = crud.get_statement_by_file_id(db, file_id)
    if not stmt or stmt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Statement not found.")

    return [TransactionOut.from_orm(tx) for tx in stmt.transactions]
