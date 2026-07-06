"""Analysis lifecycle routes — create, status, fetch results, delete."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import AnalysisCreate, AnalysisOut, AnalysisStatusOut
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import Analysis, AnalysisStatus, Project, User
from app.security.rbac import Role, require_roles
from app.services.analysis_runner import run_analysis_job

router = APIRouter(prefix="/analyses", tags=["analyses"])

# Total expected agents — used for progress estimation
TOTAL_AGENTS = 9


def _load_project(db: Session, project_id: str, user: User) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id, Project.owner_id == user.id
    ).first()
    if not project:
        raise NotFoundError(detail="Project not found")
    return project


@router.post("", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisCreate,
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
) -> AnalysisOut:
    _load_project(db, payload.project_id, current)
    analysis = Analysis(
        project_id=payload.project_id,
        status=AnalysisStatus.PENDING,
        config=payload.config or {},
    )
    db.add(analysis)
    db.flush()
    db.refresh(analysis)
    background.add_task(run_analysis_job, analysis.id)
    return AnalysisOut.model_validate(analysis)


@router.get("", response_model=List[AnalysisOut])
def list_analyses(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[AnalysisOut]:
    _load_project(db, project_id, current)
    rows = (
        db.query(Analysis)
        .filter(Analysis.project_id == project_id)
        .order_by(desc(Analysis.created_at))
        .limit(50)
        .all()
    )
    return [AnalysisOut.model_validate(r) for r in rows]


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AnalysisOut:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    _load_project(db, analysis.project_id, current)
    return AnalysisOut.model_validate(analysis)


@router.get("/{analysis_id}/status", response_model=AnalysisStatusOut)
def get_status(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> AnalysisStatusOut:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    _load_project(db, analysis.project_id, current)

    runs = analysis.agent_runs or []
    completed = [r for r in runs if r.status == AnalysisStatus.COMPLETED]
    running   = [r for r in runs if r.status == AnalysisStatus.RUNNING]

    if analysis.status == AnalysisStatus.COMPLETED:
        progress = 100
    elif analysis.status == AnalysisStatus.PENDING:
        progress = 0
    else:
        # Weighted: each completed agent = 100/TOTAL_AGENTS points, each running = half that
        progress = min(
            95,
            int(len(completed) * 100 / TOTAL_AGENTS + len(running) * 50 / TOTAL_AGENTS)
        )

    current_agents = [r.agent_name for r in running]
    current_agent: Optional[str] = current_agents[0] if current_agents else None

    # Human-readable status message
    if analysis.status == AnalysisStatus.PENDING:
        message = "Waiting for background worker…"
    elif analysis.status == AnalysisStatus.RUNNING:
        if current_agents:
            message = f"Running: {', '.join(current_agents)}"
        else:
            message = "Agents are starting…"
    elif analysis.status == AnalysisStatus.COMPLETED:
        message = f"Done — {len(completed)} agents completed"
    else:
        message = analysis.error or "Analysis failed"

    return AnalysisStatusOut(
        id=analysis.id,
        status=analysis.status,
        progress=progress,
        current_agent=current_agent,
        current_agents=current_agents,
        message=message,
        agent_runs=runs,
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    _load_project(db, analysis.project_id, current)
    db.delete(analysis)
    return None
