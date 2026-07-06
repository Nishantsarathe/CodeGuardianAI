"""Project management routes — list, create, fetch, delete, get stats."""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import ProjectCreate, ProjectOut, ProjectStats
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError, FileUploadError
from app.db.database import get_db
from app.db.models import Project, ProjectFile, User
from app.security.rbac import Role, require_roles
from app.services.project_service import scan_project_folder, validate_source_ref, fetch_github_repo


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectOut])
def list_projects(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[ProjectOut]:
    q = db.query(Project).filter(Project.owner_id == current.id)
    if search:
        q = q.filter(Project.name.ilike(f"%{search}%"))
    projects = q.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()
    return [ProjectOut.model_validate(p) for p in projects]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectOut:
    """Create a project record and import the source code.

    The source_ref can be a GitHub URL, a path to a local ZIP, or a path
    to a local folder. The project workspace is materialized under
    ``upload_dir/<project_id>``.
    """
    if payload.source_type not in {"github", "zip", "folder", "file"}:
        raise ValidationError(detail=f"Unsupported source_type: {payload.source_type}")

    project = Project(
        name=payload.name,
        description=payload.description,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        language=payload.language,
        owner_id=current.id,
    )
    db.add(project)
    db.flush()

    work_dir = Path(settings.upload_dir) / project.id
    work_dir.mkdir(parents=True, exist_ok=True)

    if payload.source_type == "github":
        if not payload.source_ref:
            raise ValidationError(detail="source_ref required for GitHub projects")
        fetch_github_repo(payload.source_ref, str(work_dir), token=settings.github_token)
    elif payload.source_type in {"zip", "folder", "file"}:
        if not payload.source_ref or not validate_source_ref(payload.source_ref, payload.source_type):
            raise ValidationError(detail="Invalid source_ref for the given type")
        scan_project_folder(str(work_dir), payload.source_ref, payload.source_type)

    # Recompute stats and persist
    stats = scan_project_folder(str(work_dir), str(work_dir), "folder")
    project.size_bytes = stats["size_bytes"]
    project.file_count = stats["total_files"]
    project.language = (
        max(stats["languages"], key=stats["languages"].get)
        if stats.get("languages")
        else None
    )

    # Index files in DB
    for f in Path(work_dir).rglob("*"):
        if f.is_file() and f.stat().st_size <= 5 * 1024 * 1024:
            rel = str(f.relative_to(work_dir))
            db.add(ProjectFile(
                project_id=project.id,
                path=rel,
                size_bytes=f.stat().st_size,
                line_count=_count_lines(f),
            ))

    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectOut:
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current.id
    ).first()
    if not project:
        raise NotFoundError(detail="Project not found")
    return ProjectOut.model_validate(project)


@router.get("/{project_id}/stats", response_model=ProjectStats)
def project_stats(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ProjectStats:
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current.id
    ).first()
    if not project:
        raise NotFoundError(detail="Project not found")
    work_dir = Path(settings.upload_dir) / project.id
    stats = scan_project_folder(str(work_dir), str(work_dir), "folder")
    return ProjectStats(**stats)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
):
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == current.id
    ).first()
    if not project:
        raise NotFoundError(detail="Project not found")
    # Cleanup workspace
    work_dir = Path(settings.upload_dir) / project.id
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    db.delete(project)
    return None


def _count_lines(path: Path) -> int:
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0
