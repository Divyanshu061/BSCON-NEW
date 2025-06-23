# File: backend/app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.utils.database import Base, engine
from app.routers import (
    auth, users, upload, history, transactions, admin, convert, subscription
)

# ───── QUIET UNWANTED LOGGERS ────────────────────────────────────────────────
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)
logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)

# ───── LOGGING SETUP ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("🚀 Starting BankStatementConverter API...")

# ───── FASTAPI APP INITIALIZATION ────────────────────────────────────────────
app = FastAPI(
    title="BankStatementConverter API",
    description="API for uploading, parsing, converting bank statements with Google OAuth.",
    version="1.0.0"
)

# ───── AUTO DB MIGRATIONS (DEV ONLY) ─────────────────────────────────────────
if settings.DEBUG:
    logger.debug("🛠 DEBUG mode enabled: Creating all tables.")
    Base.metadata.create_all(bind=engine)

# ───── CORS CONFIGURATION ────────────────────────────────────────────────────
frontend_origin = settings.FRONTEND_URL or "http://localhost:3000"
logger.debug(f"🌍 Allowing CORS from: {frontend_origin}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───── SESSION COOKIE MIDDLEWARE ─────────────────────────────────────────────
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    same_site="lax" if settings.DEBUG else "none",  # "none" in prod if on HTTPS
    https_only=not settings.DEBUG,
)

# ───── ROUTES ────────────────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{API_PREFIX}/users", tags=["Users"])
app.include_router(upload.router, prefix=f"{API_PREFIX}/upload", tags=["Upload"])
app.include_router(history.router, prefix=f"{API_PREFIX}/history", tags=["History"])
app.include_router(transactions.router, prefix=f"{API_PREFIX}/transactions", tags=["Transactions"])
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin", tags=["Admin"])
app.include_router(convert.router, prefix=f"{API_PREFIX}/convert", tags=["Convert"])
app.include_router(subscription.router, prefix=f"{API_PREFIX}/subscriptions", tags=["Subscriptions"])

logger.info("✅ All routers registered successfully.")

# ───── HEALTH CHECK ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    try:
        return {
            "status": "ok",
            "message": "Welcome to the BankStatementConverter API",
            "version": app.version,
            "docs": "/docs",
            "endpoints": {
                "Google Login": f"{API_PREFIX}/auth/login/google",
                "Upload": f"{API_PREFIX}/upload",
                "Convert": f"{API_PREFIX}/convert",
            }
        }
    except Exception as e:
        logger.exception("❌ Health check failed:")
        return {"status": "error", "message": "Health check failed"}

# ───── LOG ALL ROUTES (DEBUG) ────────────────────────────────────────────────
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"🔗 Registered route: {route.path}")
