"""Reports routes — generate and download reports in multiple formats."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.db.database import get_db
from app.db.models import Analysis, Project, User
from app.services.report_service import (
    build_html_report,
    build_json_payload,
    build_markdown_report,
    build_pdf_report,
    build_patch,
)


router = APIRouter(prefix="/reports", tags=["reports"])


def _load_analysis(db: Session, analysis_id: str, user: User) -> Analysis:
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not a:
        raise NotFoundError(detail="Analysis not found")
    project = db.query(Project).filter(
        Project.id == a.project_id, Project.owner_id == user.id
    ).first()
    if not project:
        raise NotFoundError(detail="Project not found")
    return a


@router.get("/{analysis_id}/markdown")
def report_markdown(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Response:
    a = _load_analysis(db, analysis_id, current)
    body = build_markdown_report(db, a)
    return Response(content=body, media_type="text/markdown",
                    headers={"Content-Disposition": f'attachment; filename="report_{analysis_id}.md"'})


@router.get("/{analysis_id}/html", response_class=HTMLResponse)
def report_html(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> HTMLResponse:
    a = _load_analysis(db, analysis_id, current)
    body = build_html_report(db, a)
    return HTMLResponse(content=body)


@router.get("/{analysis_id}/pdf")
def report_pdf(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Response:
    a = _load_analysis(db, analysis_id, current)
    pdf_bytes = build_pdf_report(db, a)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{analysis_id}.pdf"'},
    )


@router.get("/{analysis_id}/patch")
def report_patch(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Response:
    a = _load_analysis(db, analysis_id, current)
    patch = build_patch(db, a)
    return Response(
        content=patch,
        media_type="text/x-diff",
        headers={"Content-Disposition": f'attachment; filename="codeguardian_{analysis_id}.patch"'},
    )


@router.get("/{analysis_id}/bundle")
def report_bundle(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download a ZIP containing every report format + JSON payload."""
    a = _load_analysis(db, analysis_id, current)
    md = build_markdown_report(db, a).encode()
    html = build_html_report(db, a).encode()
    pdf = build_pdf_report(db, a)
    patch = build_patch(db, a).encode()
    payload = json.dumps(build_json_payload(db, a), indent=2, default=str).encode()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("report.md", md)
        zf.writestr("report.html", html)
        zf.writestr("report.pdf", pdf)
        zf.writestr("codeguardian.patch", patch)
        zf.writestr("report.json", payload)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="codeguardian_{analysis_id}.zip"'},
    )
