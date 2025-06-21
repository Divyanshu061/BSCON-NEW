from enum import Enum
from pydantic import BaseModel

class BillingCycle(str, Enum):
    monthly = "monthly"
    annual  = "annual"

class Plan(BaseModel):
    name: str
    monthly_cost: float
    annual_cost: float
    credits_monthly: int
    credits_annual: int

# central source of truth for all your plans
PLANS = {
    "starter": Plan(
        name="starter",
        monthly_cost=15.00,
        annual_cost=162.00,    # e.g. 10% off: 15*12*0.9
        credits_monthly=400,
        credits_annual=4800,
    ),
    "professional": Plan(
        name="professional",
        monthly_cost=30.00,
        annual_cost=324.00,
        credits_monthly=1000,
        credits_annual=12000,
    ),
    "business": Plan(
        name="business",
        monthly_cost=50.00,
        annual_cost=540.00,
        credits_monthly=4000,
        credits_annual=48000,
    ),
    "enterprise": Plan(
        name="enterprise",
        monthly_cost=None,
        annual_cost=None,
        credits_monthly=None,
        credits_annual=None,
    ),
}

def get_plan(name: str) -> Plan:
    try:
        return PLANS[name]
    except KeyError:
        raise ValueError(f"Unknown plan: {name}")
