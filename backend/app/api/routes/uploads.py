"""File upload routes — single source file or ZIP project."""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import FileUploadError, ValidationError
from app.db.models import User
from app.security.rbac import Role, require_roles


router = APIRouter(prefix="/uploads", tags=["uploads"])


_MAX_BYTES = settings.max_upload_bytes
_ALLOWED_EXTS = tuple(settings.allowed_extensions)


def _safe_filename(name: str) -> str:
    """Strip directory components and limit length."""
    name = os.path.basename(name or "upload")
    name = "".join(c for c in name if c.isalnum() or c in "._-")
    return name[:200] or f"file_{uuid.uuid4().hex[:8]}"


def _validate_extension(filename: str) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if not ext:
        raise FileUploadError(detail="File has no extension", code="bad_extension")
    if ext not in _ALLOWED_EXTS:
        raise FileUploadError(
            detail=f"Extension {ext!r} not allowed. Permitted: {', '.join(_ALLOWED_EXTS)}",
            code="extension_not_allowed",
        )


@router.post("/file", status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(default=None),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
) -> JSONResponse:
    """Upload a single source file. Returns the file's saved location."""
    if not file or not file.filename:
        raise FileUploadError(detail="No file provided", code="no_file")
    _validate_extension(file.filename)

    safe = _safe_filename(file.filename)
    work_dir = Path(settings.upload_dir) / f"file_{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    target = work_dir / safe

    written = 0
    with target.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > _MAX_BYTES:
                f.close()
                shutil.rmtree(work_dir, ignore_errors=True)
                raise FileUploadError(
                    detail=f"File exceeds {settings.max_upload_mb} MB limit",
                    code="file_too_large",
                )
            f.write(chunk)

    return JSONResponse({
        "filename": safe,
        "size_bytes": written,
        "stored_at": str(target),
        "work_dir": str(work_dir),
        "project_name": project_name or safe,
    })


@router.post("/zip", status_code=status.HTTP_201_CREATED)
async def upload_zip(
    request: Request,
    file: UploadFile = File(...),
    project_name: Optional[str] = Form(default=None),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
) -> JSONResponse:
    """Upload a ZIP archive and extract it to a fresh project directory.

    Uses ``_safe_extract_zip`` which preserves subdirectory structure
    while blocking path-traversal (zip-slip) attacks.
    """
    if not file or not file.filename:
        raise FileUploadError(detail="No file provided", code="no_file")
    if not file.filename.lower().endswith(".zip"):
        raise FileUploadError(detail="Only .zip archives are accepted", code="not_a_zip")

    work_dir = Path(settings.upload_dir) / f"zip_{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    archive_path = work_dir / _safe_filename(file.filename)

    written = 0
    with archive_path.open("wb") as f:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > _MAX_BYTES:
                f.close()
                shutil.rmtree(work_dir, ignore_errors=True)
                raise FileUploadError(
                    detail=f"File exceeds {settings.max_upload_mb} MB limit",
                    code="file_too_large",
                )
            f.write(chunk)

    # Extract to a sub-directory so the archive and its contents don't collide
    extract_dir = work_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)
    try:
        from app.services.project_service import _safe_extract_zip
        _safe_extract_zip(archive_path, extract_dir)
    except FileUploadError:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as e:
        import zipfile
        if isinstance(e, zipfile.BadZipFile):
            shutil.rmtree(work_dir, ignore_errors=True)
            raise FileUploadError(detail=f"Invalid ZIP: {e}", code="bad_zip") from e
        shutil.rmtree(work_dir, ignore_errors=True)
        raise FileUploadError(detail=f"Extraction failed: {e}", code="extract_error") from e
    finally:
        # Always remove the original archive to save space
        try:
            archive_path.unlink()
        except OSError:
            pass

    return JSONResponse({
        "filename": _safe_filename(file.filename),
        "size_bytes": written,
        "work_dir": str(extract_dir),
        "project_name": project_name or "uploaded-project",
    })
