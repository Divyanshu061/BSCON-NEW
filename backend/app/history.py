from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel

router = APIRouter()

class JobRecord(BaseModel):
    id: int
    date: str
    bank: str
    filename: str
    status: str
    download_url: str

def fake_current_user():
    return {"user_id": 1}

@router.get("/", response_model=List[JobRecord])
async def list_history(user=Depends(fake_current_user)):
    # TODO: query real DB
    return [
        {"id": 1, "date": "2025-05-27", "bank": "HSBC", "filename": "stmt.pdf", "status": "done", "download_url": "/stub/1.xlsx"}
    ]
