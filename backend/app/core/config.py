# file app/core/config.py

import os
from enum import Enum as PyEnum
from typing import Optional
from pydantic import Field, HttpUrl, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


def _ensure_directory(path: str) -> str:
    """
    Ensure a directory exists and return its absolute path.
    """
    abs_path = os.path.abspath(path)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


class BillingCycle(str, PyEnum):
    monthly = "monthly"
    annual = "annual"


class Plan(BaseModel):
    name: str
    monthly_cost: Optional[float]
    annual_cost: Optional[float]
    credits_monthly: Optional[int]
    credits_annual: Optional[int]


PLANS = {
    "starter": Plan(
        name="starter",
        monthly_cost=15.00,
        annual_cost=162.00,    # 10% off
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


class Settings(BaseSettings):
    """
    Global application settings loaded from environment variables or `.env` file.
    """

    # App mode
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Secrets and JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    JWT_SECRET: str = Field(..., env="JWT_SECRET")  # Can be used interchangeably
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )  # 24 hrs

    # OAuth2 (Google)
    GOOGLE_CLIENT_ID: str = Field(..., env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: HttpUrl = Field(..., env="GOOGLE_REDIRECT_URI")

    # Frontend / API URLs
    FRONTEND_URL: HttpUrl = Field(..., env="FRONTEND_URL")
    VITE_API_URL: HttpUrl = Field(..., env="VITE_API_URL")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Upload / Result folders
    UPLOAD_DIR: str = Field(default="./uploads", env="UPLOAD_DIR")
    RESULT_DIR: str = Field(default="./results", env="RESULT_DIR")
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE"
    )  # 10 MB

    # Optional monitoring
    SENTRY_DSN: str = Field(default="", env="SENTRY_DSN")

    # Cookie name
    COOKIE_NAME: str = Field(default="access_token", env="COOKIE_NAME")

    # Pydantic v2 model config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid"
    )

    def __init__(self, **data):
        super().__init__(**data)
        print(f"[config] ✅ Loaded GOOGLE_REDIRECT_URI: {self.GOOGLE_REDIRECT_URI}")

    def model_post_init(self, __context__) -> None:
        self.UPLOAD_DIR = _ensure_directory(self.UPLOAD_DIR)
        self.RESULT_DIR = _ensure_directory(self.RESULT_DIR)


# Instantiate global settings object
settings = Settings()
