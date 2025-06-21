# backend/app/services/credits.py

from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User, UserSubscription
from app.core.config import get_plan, BillingCycle


def deduct_credits(db: Session, user: User, pages: int):
    """
    Deduct a number of credits (pages) from the user's remaining balance.
    """
    if user.credits_remaining < pages:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits; please subscribe or top up."
        )
    user.credits_remaining -= pages
    db.add(user)
    db.commit()
    return user.credits_remaining


def subscribe_user(db: Session, user: User, plan_name: str, cycle: BillingCycle):
    """
    Subscribe or resubscribe a user to a plan, refill credits, and set expiry.
    """
    # Retrieve plan details
    plan = get_plan(plan_name)

    # Compute expiry date based on billing cycle
    if cycle == BillingCycle.monthly:
        expires = datetime.utcnow() + relativedelta(months=1)
        refill_credits = plan.credits_monthly
    else:
        expires = datetime.utcnow() + relativedelta(years=1)
        refill_credits = plan.credits_annual

    # Upsert subscription record
    sub = (
        db.query(UserSubscription)
          .filter_by(user_id=user.id, active=True)
          .one_or_none()
    )
    if sub:
        sub.plan_name = plan_name
        sub.billing_cycle = cycle
        sub.start_date = datetime.utcnow()
        sub.expires_at = expires
    else:
        sub = UserSubscription(
            user_id=user.id,
            plan_name=plan_name,
            billing_cycle=cycle,
            start_date=datetime.utcnow(),
            expires_at=expires,
            active=True,
        )
        db.add(sub)

    # Refill user credits
    if refill_credits is not None:
        user.credits_remaining = refill_credits
    else:
        # Enterprise or special plan: credits must be handled separately
        user.credits_remaining = 0

    db.add(user)
    db.commit()

    return {"expires_at": expires, "credits": user.credits_remaining}
