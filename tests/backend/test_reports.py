"""Report generation tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_ENV", "test")

import pytest  # noqa: E402

from app.db.database import SessionLocal, init_db  # noqa: E402
from app.db.models import (  # noqa: E402
    Analysis, AnalysisStatus, Finding, Project, Severity, User, UserRole,
)
from app.security.auth import hash_password  # noqa: E402
from app.services.report_service import (  # noqa: E402
    build_markdown_report, build_patch,
)


@pytest.fixture
def db_session():
    """Fresh DB with a user, project, and analysis containing one finding."""
    init_db()
    db = SessionLocal()
    try:
        # Wipe any prior test data so the fixture is repeatable.
        from app.db.models import AgentRun, AuditLog, ChatMessage, ChatSession
        db.query(ChatMessage).delete()
        db.query(ChatSession).delete()
        db.query(AgentRun).delete()
        db.query(Finding).delete()
        db.query(Analysis).delete()
        db.query(Project).delete()
        db.query(AuditLog).delete()
        db.query(User).delete()
        db.commit()

        # Use a unique email/username per call to avoid collisions when
        # this fixture is invoked more than once in the same process.
        import uuid as _uuid
        uniq = _uuid.uuid4().hex[:8]
        user = User(
            email=f"reporter-{uniq}@codeguardian.ai",
            username=f"reporter-{uniq}",
            full_name="Reporter",
            hashed_password=hash_password("p@ssword!1"),
            role=UserRole.REVIEWER,
        )
        db.add(user)
        db.flush()

        project = Project(
            name="Demo", description="t", source_type="folder",
            source_ref=".", language="python", owner_id=user.id,
        )
        db.add(project)
        db.flush()

        analysis = Analysis(
            project_id=project.id,
            status=AnalysisStatus.COMPLETED,
            health_score=80.0,
            summary={"note": "demo"},
        )
        db.add(analysis)
        db.flush()

        finding = Finding(
            analysis_id=analysis.id,
            agent_name="security",
            category="security",
            severity=Severity.CRITICAL,
            title="SQL injection",
            description="String-built SQL query",
            file_path="app/db.py",
            line_start=1, line_end=1,
            rule_id="CG-SEC-89",
            cvss_score=9.8,
            cwe_id="CWE-89",
            recommendation="Use parameterized queries.",
            code_snippet="q = 'SELECT *' + name",
        )
        db.add(finding)
        db.commit()

        # Refresh the analysis so its .findings relationship is loaded.
        db.refresh(analysis)
        yield db, analysis
    finally:
        db.close()


def test_markdown_includes_severity_table(db_session) -> None:
    db, analysis = db_session
    md = build_markdown_report(db, analysis)
    assert "SQL injection" in md
    assert "critical" in md
    assert "CVSS" in md or "cvss" in md.lower()


def test_patch_contains_diff(db_session) -> None:
    db, analysis = db_session
    patch = build_patch(db, analysis)
    assert "diff --git" in patch
