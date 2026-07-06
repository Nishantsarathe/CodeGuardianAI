"""Aggregated dashboard route — KPIs, severity counts, recent analyses."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.db.models import Analysis, AnalysisStatus, Finding, Project, Severity, User
from app.core.constants import SEVERITY_ORDER


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return aggregated KPIs and trend data for the dashboard."""
    projects = db.query(Project).filter(Project.owner_id == current.id).all()
    project_ids = [p.id for p in projects]

    total_projects = len(project_ids)
    total_analyses = db.query(Analysis).filter(Analysis.project_id.in_(project_ids)).count() \
        if project_ids else 0
    completed = db.query(Analysis).filter(
        Analysis.project_id.in_(project_ids),
        Analysis.status == AnalysisStatus.COMPLETED,
    ).count() if project_ids else 0

    findings = db.query(Finding).filter(
        Finding.analysis_id.in_([a.id for a in db.query(Analysis).filter(
            Analysis.project_id.in_(project_ids)).all()]) if project_ids else [None]
    ).all() if project_ids else []

    severity_counts = Counter(f.severity.value if hasattr(f.severity, "value") else f.severity
                              for f in findings)
    severity_data = [{"severity": s, "count": severity_counts.get(s, 0)} for s in SEVERITY_ORDER]

    avg_health = None
    health_scores = [p.health_score for p in projects if p.health_score is not None]
    if health_scores:
        avg_health = round(sum(health_scores) / len(health_scores), 2)

    # Last 7 days analyses trend
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent = (
        db.query(Analysis)
        .filter(Analysis.project_id.in_(project_ids), Analysis.created_at >= seven_days_ago)
        .all()
        if project_ids else []
    )
    daily = Counter(a.created_at.date().isoformat() for a in recent)
    trend = [{"date": (datetime.utcnow().date() - timedelta(days=i)).isoformat(),
              "count": daily.get((datetime.utcnow().date() - timedelta(days=i)).isoformat(), 0)}
             for i in range(6, -1, -1)]

    return {
        "total_projects": total_projects,
        "total_analyses": total_analyses,
        "completed_analyses": completed,
        "pending_analyses": total_analyses - completed,
        "total_findings": len(findings),
        "average_health_score": avg_health,
        "severity_distribution": severity_data,
        "analyses_trend": trend,
        "agent_counts": _agent_counts(db, project_ids),
        "top_projects": [
            {
                "id": p.id, "name": p.name, "health_score": p.health_score,
                "file_count": p.file_count, "language": p.language,
            }
            for p in sorted(projects, key=lambda x: -(x.health_score or 0))[:5]
        ],
    }


def _agent_counts(db: Session, project_ids: List[str]) -> List[Dict[str, Any]]:
    if not project_ids:
        return []
    rows = (
        db.query(Finding.agent_name, func.count(Finding.id))
        .join(Analysis, Analysis.id == Finding.analysis_id)
        .filter(Analysis.project_id.in_(project_ids))
        .group_by(Finding.agent_name)
        .all()
    )
    return [{"agent": a, "count": c} for a, c in rows]
