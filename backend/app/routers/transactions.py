# backend/app/routers/transactions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.schemas import Transaction
from app.utils.database import get_db
from app import crud, models

router = APIRouter(
    tags=["Transactions"],
)

@router.get("/", response_model=List[Transaction])
def list_transactions(db: Session = Depends(get_db)):
    """
    Retrieve all transactions from the database.
    """
    txs = db.query(models.Job).all()  # Assuming Job model stores transactions
    # Convert Job entries to Transaction schema if needed
    return [
        Transaction(
            id=job.id,
            date=str(job.created_at.date()),
            amount=0.0,              # placeholder, update with real amount field
            description=job.filename  # placeholder, update with real description
        )
        for job in txs
    ]

@router.get("/{tx_id}", response_model=Transaction)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single transaction by its ID.
    """
    job = db.query(models.Job).filter(models.Job.id == tx_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Transaction(
        id=job.id,
        date=str(job.created_at.date()),
        amount=0.0,                # placeholder
        description=job.filename   # placeholder
    )
