#file app/routers/history.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app import crud, schemas
from app.schemas import ConversionHistoryOut

router = APIRouter(
    tags=["history"]
)

@router.get("/", response_model=list[schemas.StatementOut])
def get_upload_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max number of records to return"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    List all statements uploaded by the current user, with pagination.
    """
    try:
        all_statements = crud.get_statements_for_user(db, user.id)
        # Apply skip/limit
        paginated = all_statements[skip : skip + limit]
        return paginated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@router.get("/{file_id}", response_model=schemas.StatementDetail)
def get_statement_detail(
    file_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Retrieve a specific statement and its transactions by file_id.
    """
    stmt = crud.get_statement_by_file_id(db, file_id)
    if not stmt or stmt.user_id != user.id:
        raise HTTPException(status_code=404, detail="Statement not found.")

    return stmt

@router.get("/conversions", response_model=list[ConversionHistoryOut])
def get_conversion_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    """
    List conversion-history entries (id, user_id, timestamp, description, pages_converted, credits_spent)
    """
    return crud.get_conversion_history_for_user(db, user.id, skip=skip, limit=limit)
