# File: backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging

from app.routers import auth, users, upload, history, transactions, admin, convert
from app.utils.database import Base, engine
from app.core.config import settings

import logging
from app.routers import auth, users, upload, history, transactions, admin, convert, subscription

# ─── QUIET DOWN PDFMINER ───────────────────────────────────────────────────────
# suppress all pdfminer warnings and below
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# or, if you want to be surgical and only silence CropBox warnings:
logging.getLogger("pdfminer.pdfpage").setLevel(logging.ERROR)

# suppress all pdfminer warnings and below
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Turn off pdfminer debug chatter
logging.getLogger("pdfminer").setLevel(logging.WARNING)

# suppress pdfplumber (which uses pdfminer internally)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)

# suppress Starlette/fastapi multipart‐parser debug logs
logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)

# ---------- Logging Configuration ----------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("Starting BankStatementConverter API")

# ---------- App Initialization ----------
app = FastAPI(
    title="BankStatementConverter API",
    description="API for uploading, parsing, converting bank statements with Google OAuth.",
    version="1.0.0"
)

# ---------- Database Auto Migration (DEBUG only) ----------
if settings.DEBUG:
    logger.debug("DEBUG mode enabled: Auto-creating database tables.")
    Base.metadata.create_all(bind=engine)

# ---------- Middleware Configuration ----------
allowed_origins = [settings.FRONTEND_URL] if settings.FRONTEND_URL else ["*"]
logger.debug(f"CORS allowed origins: {allowed_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    same_site="lax",
    https_only=not settings.DEBUG
)

# ---------- API Routing ----------
API_PREFIX = "/api"
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Auth"])
app.include_router(users.router, prefix=f"{API_PREFIX}/users", tags=["Users"])
app.include_router(upload.router, prefix=f"{API_PREFIX}/upload", tags=["Upload"])
app.include_router(history.router, prefix=f"{API_PREFIX}/history", tags=["History"])
app.include_router(transactions.router, prefix=f"{API_PREFIX}/transactions", tags=["Transactions"])
app.include_router(admin.router, prefix=f"{API_PREFIX}/admin", tags=["Admin"])
app.include_router(convert.router, prefix=f"{API_PREFIX}/convert", tags=["Convert"])
app.include_router(subscription.router, prefix=f"{API_PREFIX}/subscriptions", tags=["subscriptions"])
logger.info("✅ Subscriptions router included")

# ---------- Health Check ----------
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
                "Convert": f"{API_PREFIX}/convert"
            }
        }
    
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": "Health check failed"}
    

    
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"🔗 Route registered: {route.path}")
