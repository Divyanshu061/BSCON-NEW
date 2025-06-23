from pydantic import BaseModel, EmailStr, Field, HttpUrl, ConfigDict
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Annotated

# ================================
# 🔐 Auth / User Schemas
# ================================

class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    profile_picture: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ================================
# 📁 Upload Schemas
# ================================

class FileMeta(BaseModel):
    original_filename: str
    saved_filename: str
    size: int
    size_human: str
    upload_time: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class UploadedFileResponse(FileMeta):
    id: int
    download_url: HttpUrl

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class UploadResponse(BaseModel):
    files: List[UploadedFileResponse]

    model_config = ConfigDict(extra="forbid")


# ================================
# 📄 Parsed Statement Item Schema
# ================================

class StatementItem(BaseModel):
    date: date
    description: str
    ref_no: Optional[str] = None

    # Either debit or credit can be set (optional), not both required
    debit: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None
    credit: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None

    balance: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None

    model_config = ConfigDict(extra="ignore")


# ================================
# 📤 Conversion Response Schema
# ================================

class ConversionResponse(BaseModel):
    download_url: str

    model_config = ConfigDict(extra="forbid")


# ================================
# 📚 History / Transactions / Statements
# ================================

class Transaction(BaseModel):
    id: int
    date: datetime
    description: str
    debit: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None
    credit: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None
    balance: Optional[Annotated[Decimal, Field(max_digits=12, decimal_places=2)]] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class TransactionOut(Transaction):
    pass


class StatementOut(BaseModel):
    id: int
    original_filename: str
    file_id: str
    format: str
    uploaded_at: datetime
    processed: bool

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class StatementDetail(StatementOut):
    transactions: List[Transaction] = []

    model_config = ConfigDict(from_attributes=True, extra="ignore")

class ConversionHistoryOut(BaseModel):
    id: int
    user_id: int
    timestamp: datetime
    description: str
    pages_converted: int
    credits_spent: int

    class Config:
        orm_mode = True
