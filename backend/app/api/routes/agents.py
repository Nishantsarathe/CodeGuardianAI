"""Agent introspection routes — list, trigger, re-run single agent."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import AgentRunOut, FindingOut
from app.core.constants import AGENT_NAMES
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import AgentRun, Analysis, Finding, Project, User
from app.security.rbac import Role, require_roles
from app.services.analysis_runner import run_single_agent


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=List[dict])
def list_agents(
    request: Request,
    current: User = Depends(get_current_user),
) -> List[dict]:
    """Return metadata for all available agents."""
    return [
        {"key": k, "name": v, "description": _description(k)}
        for k, v in AGENT_NAMES.items()
    ]


@router.get("/runs/{analysis_id}", response_model=List[AgentRunOut])
def list_runs(
    analysis_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[AgentRunOut]:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    return [AgentRunOut.model_validate(r) for r in analysis.agent_runs]


@router.get("/findings/{analysis_id}", response_model=List[FindingOut])
def list_findings(
    analysis_id: str,
    request: Request,
    agent: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[FindingOut]:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    q = db.query(Finding).filter(Finding.analysis_id == analysis_id)
    if agent:
        q = q.filter(Finding.agent_name == agent)
    if severity:
        q = q.filter(Finding.severity == severity)
    return [FindingOut.model_validate(f) for f in q.all()]


@router.post("/runs/{analysis_id}/{agent_name}", response_model=AgentRunOut, status_code=status.HTTP_202_ACCEPTED)
def re_run_agent(
    analysis_id: str,
    agent_name: str,
    background: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    _: None = Depends(require_roles(Role.REVIEWER)),
) -> AgentRunOut:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise NotFoundError(detail="Analysis not found")
    if agent_name not in AGENT_NAMES:
        raise NotFoundError(detail=f"Unknown agent: {agent_name}")
    background.add_task(run_single_agent, analysis_id, agent_name)
    # We can't return the run synchronously because it was just queued.
    # Return a placeholder reflecting "pending" status.
    return AgentRunOut(
        id="",
        agent_name=agent_name,
        status="pending",
        started_at=None,
        finished_at=None,
        duration_ms=None,
        confidence=None,
        error=None,
    )


def _description(key: str) -> str:
    return {
        "coordinator": "Plans, delegates, and merges agent results.",
        "code_review": "Analyzes code quality, complexity, and smells.",
        "security": "Detects security vulnerabilities and computes risk scores.",
        "bug": "Hunts for runtime, logic, and performance bugs.",
        "auto_fix": "Generates patches and applies safe fixes.",
        "documentation": "Generates READMEs, API docs, and developer guides.",
        "refactor": "Suggests refactors aligned with SOLID principles.",
        "test": "Produces pytest unit and integration tests.",
        "uml": "Builds class, sequence, and component diagrams.",
        "dependency": "Audits dependencies for vulnerabilities and upgrades.",
    }.get(key, "")
