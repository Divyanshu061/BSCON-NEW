# File: backend/app/routers/upload.py

from fastapi import (
    APIRouter, UploadFile, File, HTTPException,
    Depends, status, Request, Header
)
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import uuid
import re
import logging
import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_jwt_token
from app.utils.database import get_db
from app.schemas import UploadResponse, UploadedFileResponse
from app.services.parser import ParserService
from app.models import UploadedFile

router = APIRouter(tags=["Upload"])
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv", ".pdf"}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\-]", "_", Path(filename).stem)


def generate_unique_filename(original_name: str, extension: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex
    stem = sanitize_filename(original_name)
    return f"{stem}_{ts}_{uid}{extension}"


def human_readable_size(n_bytes: int) -> str:
    if n_bytes < 1024:
        return f"{n_bytes} B"
    elif n_bytes < 1024**2:
        return f"{n_bytes / 1024:.2f} KB"
    else:
        return f"{n_bytes / 1024**2:.2f} MB"


def get_token_from_request(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> str:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
    logger.debug("🧪 Extracted JWT token: %s", token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: No JWT provided")
    return token


@router.post("/", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(get_token_from_request)
) -> UploadResponse:
    """
    Upload one or more PDF/CSV files, save to disk and DB,
    and return metadata with download URLs.
    """
    user_id = verify_jwt_token(token)
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    base_download = str(settings.VITE_API_URL).rstrip("/")
    results: List[UploadedFileResponse] = []

    for idx, upload in enumerate(files, start=1):
        orig = Path(upload.filename).name
        ext = Path(orig).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File {idx}: Unsupported type '{ext}'")

        content = await upload.read()
        size_bytes = len(content)
        if size_bytes > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {idx}: '{orig}' exceeds size limit of {human_readable_size(MAX_FILE_SIZE)}"
            )

        saved_name = generate_unique_filename(orig, ext)
        dest = upload_dir / saved_name
        dest.write_bytes(content)

        db_file = UploadedFile(
            user_id=user_id,
            original_filename=orig,
            saved_filename=saved_name,
            size=size_bytes,
        )
        db.add(db_file)
        db.flush()

        results.append(UploadedFileResponse(
            id=db_file.id,
            original_filename=orig,
            saved_filename=saved_name,
            size=db_file.size,
            size_human=human_readable_size(size_bytes),
            upload_time=db_file.upload_time.replace(microsecond=0).isoformat(),
            download_url=f"{base_download}/download/{db_file.id}"
        ))

        logger.info("📥 Saved file %s (id=%s, %s) for user %s", saved_name, db_file.id, human_readable_size(size_bytes), user_id)

    db.commit()
    return UploadResponse(files=results)


def safe_serialize(obj):
    """
    Converts datetime, date, and Decimal values to string/float for JSON compatibility.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


@router.post("/parse/", response_model=None)
async def parse_uploaded_file(
    request: Request,
    file: UploadFile = File(...),
    token: str = Depends(get_token_from_request)
):
    """
    Parse a single uploaded PDF/CSV file in-memory and return extracted transactions.
    """
    user_id = verify_jwt_token(token)
    orig = Path(file.filename).name
    ext = Path(orig).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Only .pdf and .csv files are supported")

    content = await file.read()
    raw_text = None
    try:
        raw_text = ParserService.extract_text(content)
        parsed = ParserService.parse_file(content, orig)
    except HTTPException as he:
        if he.status_code == status.HTTP_400_BAD_REQUEST and "No valid transactions" in str(he.detail):
            logger.warning("⚠️ ParserService: %s", he.detail)
            preview = raw_text.splitlines()[:20] if raw_text else []
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"parsed_data": [], "raw_text_preview": preview}
            )
        logger.error("❌ HTTPException parsing '%s': %s", orig, he.detail, exc_info=True)
        raise
    except Exception as e:
        logger.error("❌ Unexpected error parsing '%s': %s", orig, e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Parsing failed for '{orig}': {e}")

    if not parsed:
        preview = raw_text.splitlines()[:20]
        logger.warning("⚠️ No transactions parsed from '%s'; returning raw text preview.", orig)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"parsed_data": [], "raw_text_preview": preview}
        )

    logger.info("✅ Parsed %d transactions from '%s'", len(parsed), orig)

    # Ensure JSON-safe response
    parsed_json = [
        json.loads(json.dumps(item.dict(), default=safe_serialize))
        for item in parsed
    ]
    return JSONResponse(status_code=status.HTTP_200_OK, content={"parsed_data": parsed_json})
