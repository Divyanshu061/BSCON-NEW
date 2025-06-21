from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(tags=["Admin"])

class Stats(BaseModel):
    total_conversions: int
    xlsx_count: int
    csv_count: int

def fake_admin_user():
    # Simulate admin check - replace with real auth logic
    user = {"is_admin": True}
    if not user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

@router.get("/stats", response_model=Stats)
async def get_stats(admin=Depends(fake_admin_user)):
    """
    Return fake conversion stats.
    Replace with real DB queries or analytics logic.
    """
    return {
        "total_conversions": 123,
        "xlsx_count": 100,
        "csv_count": 23
    }
