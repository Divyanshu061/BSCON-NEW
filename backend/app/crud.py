from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import uuid
from datetime import datetime

from app import models

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    Fetch a user by their ID.
    """
    return db.query(models.User).get(user_id)


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """
    Fetch a user by their email address.
    """
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(
    db: Session,
    email: str,
    name: Optional[str] = None,
    profile_picture: Optional[str] = None
) -> models.User:
    """
    Create a new user entry from OAuth data (Google), assigning timestamps.
    """
    new_user = models.User(
        email=email,
        name=name,
        profile_picture=profile_picture,
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
    """
    Update user profile details.
    """
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
    """
    Create a new Statement entry with a unique file_id and timestamp.
    """
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
    """
    Bulk insert transactions linked to a statement.

    `transactions` is a list of dicts with keys: date, amount, balance, description.
    """
    objs = []
    for tx in transactions:
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


def get_statement_by_id(db: Session, stmt_id: int) -> Optional[models.Statement]:
    """
    Fetch a statement by its ID, including transactions.
    """
    return (
        db.query(models.Statement)
        .filter(models.Statement.id == stmt_id)
        .options(
            # eager load transactions
        )
        .first()
    )
