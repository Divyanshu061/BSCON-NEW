# backend/app/routers/subscription.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Literal
from sqlalchemy.orm import Session

from app.core.config import PLANS, BillingCycle, get_plan
from app.core.deps import get_db, get_current_user
from app.models import User
from app.services.credits import subscribe_user  # implement this in credits.py
from pydantic import BaseModel

router = APIRouter(tags=["subscriptions"])


class SubscribeRequest(BaseModel):
    plan_name: str
    billing_cycle: BillingCycle  # "monthly" or "annual"


@router.get("/plans")
def list_plans():
    """
    Returns all available plans (with costs & credits).
    """
    # Pydantic BaseModels are JSON serializable out of the box
    return {name: plan.dict() for name, plan in PLANS.items()}


@router.post("/subscribe", status_code=status.HTTP_200_OK)
def subscribe(
    req: SubscribeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Subscribes the authenticated user to a plan.
    """
    # Validate plan exists
    try:
        plan = get_plan(req.plan_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{req.plan_name}' not found",
        )

    # Call your credits service
    result = subscribe_user(db, user, plan_name=req.plan_name, cycle=req.billing_cycle)
    return {
        "message": f"Subscribed to {req.plan_name} ({req.billing_cycle})",
        "expires_at": result["expires_at"],
        "credits": result["credits"],
    }
