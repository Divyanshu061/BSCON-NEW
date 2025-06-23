from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Text,
    Boolean,
    Enum,
    func,
    text
)
from sqlalchemy.orm import relationship

from app.utils.database import Base
from app.core.config import BillingCycle as BillingCycleEnum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
    credits_remaining = Column(
        Integer,
        default=5,
        server_default=text("5"),
        nullable=False,
        comment="Credits for PDF pages (1 credit = 1 page)"
    )

    statements = relationship(
        "Statement",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    uploads = relationship(
        "UploadedFile",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscription = relationship(
        "UserSubscription",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    conversion_history = relationship(
        "ConversionHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email!r}>"


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    file_id = Column(String(100), unique=True, index=True, nullable=False)
    format = Column(String(50), nullable=False, default="xlsx")
    uploaded_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when this statement was marked processed"
    )

    owner = relationship("User", back_populates="statements")
    transactions = relationship(
        "Transaction",
        back_populates="statement",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Statement id={self.id} file_id={self.file_id!r} "
            f"format={self.format!r} processed={self.processed}>"
        )

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(
        Integer,
        ForeignKey("statements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Float, nullable=False)
    balance = Column(Float, nullable=True)
    description = Column(Text, nullable=False, index=True)
    ref_no = Column(String, nullable=True)

    statement = relationship("Statement", back_populates="transactions")

    def __repr__(self):
        date_str = self.date.isoformat() if self.date else "N/A"
        return (
            f"<Transaction id={self.id} date={date_str} "
            f"amount={self.amount} description={self.description!r}>"
        )


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    saved_filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    upload_time = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    user = relationship("User", back_populates="uploads")

    def __repr__(self):
        return (
            f"<UploadedFile id={self.id} user_id={self.user_id} "
            f"saved_filename={self.saved_filename!r} size={self.size}>"
        )


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String, nullable=False)
    billing_cycle = Column(Enum(BillingCycleEnum), nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return (
            f"<UserSubscription id={self.id} user_id={self.user_id} "
            f"plan={self.plan_name} cycle={self.billing_cycle}>"
        )


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )
    description = Column(String, nullable=False)
    pages_converted = Column(Integer, nullable=False)
    credits_spent = Column(Integer, nullable=False)

    user = relationship("User", back_populates="conversion_history")

    def __repr__(self):
        return (
            f"<ConversionHistory id={self.id} user_id={self.user_id} "
            f"pages={self.pages_converted} credits={self.credits_spent}>"
        )