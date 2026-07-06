"""
MCP server implementations.

The application integrates with the Model Context Protocol via three
local servers:
  * Filesystem MCP — safe file IO on the project workspace
  * GitHub MCP — repository metadata + clone helpers
  * SQLite MCP — typed query helpers

Each server exposes a small, well-typed Python API. They are designed
to be called from the agents/services layer.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger


logger = get_logger("codeguardian.mcp")


class FilesystemMCP:
    """Safe, sandboxed file IO for agent workloads."""

    def __init__(self, root: Optional[str] = None) -> None:
        self.root = Path(root or settings.upload_dir).resolve()

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if not str(target).startswith(str(self.root)):
            raise ValidationError(detail="Path traversal attempt blocked",
                                  code="path_traversal")
        return target

    def read(self, path: str, max_bytes: int = 1_000_000) -> str:
        p = self._resolve(path)
        if not p.exists():
            raise NotFoundError(detail=f"File not found: {path}")
        if p.stat().st_size > max_bytes:
            with p.open("rb") as f:
                return f.read(max_bytes).decode("utf-8", errors="ignore")
        return p.read_text(encoding="utf-8", errors="ignore")

    def write(self, path: str, content: str) -> Dict[str, Any]:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "size": p.stat().st_size}

    def list_dir(self, path: str = ".") -> List[Dict[str, Any]]:
        p = self._resolve(path)
        if not p.is_dir():
            raise NotFoundError(detail=f"Directory not found: {path}")
        return [
            {
                "name": child.name,
                "is_dir": child.is_dir(),
                "size": child.stat().st_size if child.is_file() else 0,
            }
            for child in sorted(p.iterdir())
        ]

    def exists(self, path: str) -> bool:
        try:
            return self._resolve(path).exists()
        except ValidationError:
            return False


class GitHubMCP:
    """GitHub metadata + clone helpers."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or settings.github_token
        self.base = "https://api.github.com"

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "User-Agent": "CodeGuardian-AI"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        import httpx
        r = httpx.get(f"{self.base}/repos/{owner}/{repo}",
                      headers=self._headers(), timeout=15.0)
        r.raise_for_status()
        return r.json()

    def list_branches(self, owner: str, repo: str) -> List[str]:
        import httpx
        r = httpx.get(f"{self.base}/repos/{owner}/{repo}/branches",
                      headers=self._headers(), timeout=15.0)
        r.raise_for_status()
        return [b["name"] for b in r.json()]

    def clone(self, url: str, dest: str) -> Dict[str, Any]:
        cmd = ["git", "clone", "--depth", "1", url, dest]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise ValidationError(detail=f"git clone failed: {result.stderr[:500]}")
        return {"path": dest, "url": url}


class SQLiteMCP:
    """Typed helper for the application's SQLite database.

    Wraps a few read-only queries so the agents can answer
    "how many findings did I produce last time" without learning
    SQLAlchemy internals.
    """

    def __init__(self, engine) -> None:
        from sqlalchemy import text
        self._text = text
        self._engine = engine

    def count_findings(self, project_id: str) -> int:
        with self._engine.connect() as conn:
            res = conn.execute(
                self._text("SELECT COUNT(*) FROM findings f "
                           "JOIN analyses a ON a.id = f.analysis_id "
                           "WHERE a.project_id = :pid"),
                {"pid": project_id},
            ).scalar()
            return int(res or 0)

    def severity_breakdown(self, project_id: str) -> Dict[str, int]:
        from sqlalchemy import text
        with self._engine.connect() as conn:
            rows = conn.execute(
                self._text("SELECT f.severity, COUNT(*) FROM findings f "
                           "JOIN analyses a ON a.id = f.analysis_id "
                           "WHERE a.project_id = :pid GROUP BY f.severity"),
                {"pid": project_id},
            ).all()
            return {row[0]: int(row[1]) for row in rows}

    def latest_analysis(self, project_id: str) -> Optional[Dict[str, Any]]:
        from sqlalchemy import text
        with self._engine.connect() as conn:
            row = conn.execute(
                self._text("SELECT id, status, health_score, created_at FROM analyses "
                           "WHERE project_id = :pid ORDER BY created_at DESC LIMIT 1"),
                {"pid": project_id},
            ).first()
            if not row:
                return None
            return {
                "id": row[0], "status": row[1],
                "health_score": row[2], "created_at": row[3],
            }


# Module-level singletons (lazily initialized)
_filesystem: Optional[FilesystemMCP] = None
_github: Optional[GitHubMCP] = None


def filesystem() -> FilesystemMCP:
    global _filesystem
    if _filesystem is None:
        _filesystem = FilesystemMCP()
    return _filesystem


def github() -> GitHubMCP:
    global _github
    if _github is None:
        _github = GitHubMCP()
    return _github
