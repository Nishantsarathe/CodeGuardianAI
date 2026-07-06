"""Unit tests for the agent layer."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_ENV", "test")

from app.agents import (  # noqa: E402
    agent_for, AGENT_REGISTRY,
)


def _payload(content: str = "def foo():\n    print('hello')\n"):
    return {"project_id": "p1", "workdir": "/tmp/p1", "files": [
        {"path": "main.py", "language": "python", "content": content, "size": len(content)},
    ]}


def test_coordinator_runs() -> None:
    res = asyncio.run(AGENT_REGISTRY["coordinator"].run(_payload()))
    assert res.agent_name == "coordinator"
    assert "plan" in res.summary


def test_security_regex_finds_hardcoded_secret() -> None:
    payload = _payload("api_key = 'sk-12345678901234567890'\n")
    res = asyncio.run(AGENT_REGISTRY["security"].run(payload))
    titles = [f["title"] for f in res.findings]
    assert any("secret" in t.lower() for t in titles)


def test_bug_detection_flags_eval() -> None:
    payload = _payload("result = eval('1+1')\n")
    res = asyncio.run(AGENT_REGISTRY["bug"].run(payload))
    titles = [f["title"] for f in res.findings]
    assert any("eval" in t.lower() for t in titles)


def test_code_review_flags_long_function() -> None:
    body = "def f():\n" + "    pass\n" * 100
    res = asyncio.run(AGENT_REGISTRY["code_review"].run(_payload(body)))
    titles = [f["title"] for f in res.findings]
    assert any("too long" in t.lower() for t in titles)


def test_all_agents_registered() -> None:
    expected = {"coordinator", "code_review", "security", "bug", "auto_fix",
                "documentation", "refactor", "test", "uml", "dependency"}
    assert set(AGENT_REGISTRY.keys()) == expected
    for name in expected:
        agent_for(name)
