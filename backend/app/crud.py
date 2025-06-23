# File: backend/app/crud.py
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import uuid
from datetime import datetime

from app import models


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).get(user_id)


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(
    db: Session,
    email: str,
    name: Optional[str] = None,
    profile_picture: Optional[str] = None
) -> models.User:
    new_user = models.User(
        email=email,
        name=name,
        profile_picture=profile_picture,
        credits_remaining=5,
        created_at=datetime.utcnow(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(
    db: Session,
    user: models.User,
    name: Optional[str] = None,
    profile_picture: Optional[str] = None
) -> models.User:
    if name is not None:
        user.name = name
    if profile_picture is not None:
        user.profile_picture = profile_picture
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_statement(
    db: Session,
    user_id: int,
    original_filename: str,
    fmt: str
) -> models.Statement:
    stmt = models.Statement(
        user_id=user_id,
        original_filename=original_filename,
        file_id=uuid.uuid4().hex,
        format=fmt,
        uploaded_at=datetime.utcnow(),
    )
    db.add(stmt)
    db.commit()
    db.refresh(stmt)
    return stmt

def create_transactions(
    db: Session,
    statement_id: int,
    transactions: List[Dict]
) -> List[models.Transaction]:
    objs = []
    for tx in transactions:
        # Defensive check to avoid KeyError
        if 'date' not in tx or 'amount' not in tx or 'description' not in tx:
            print(f"⚠️ Skipping transaction due to missing keys: {tx}")
            continue
        obj = models.Transaction(
            statement_id=statement_id,
            date=tx['date'],
            amount=tx['amount'],
            balance=tx.get('balance'),
            description=tx['description'],
        )
        objs.append(obj)
    db.bulk_save_objects(objs)
    db.commit()
    return objs


def get_statement_by_file_id(db: Session, file_id: str) -> Optional[models.Statement]:
    return db.query(models.Statement).filter(models.Statement.file_id == file_id).first()

def decrement_credits(db: Session, user_id: int, amount: int) -> None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found.")
    user.credits_remaining = max(user.credits_remaining - amount, 0)
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()

def increment_credits(db: Session, user_id: int, amount: int) -> None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found.")
    user.credits_remaining += amount
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()

def mark_statement_processed(db: Session, statement: models.Statement) -> None:
    statement.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(statement)