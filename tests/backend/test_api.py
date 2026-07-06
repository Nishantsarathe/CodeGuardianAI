"""Smoke tests for the FastAPI app."""
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEMO_ADMIN_PASSWORD", "TestPass123!")

def test_health(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_root(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "CodeGuardian" in r.json()["name"]

def test_login_flow(client) -> None:
    demo_password = os.environ["DEMO_ADMIN_PASSWORD"]
    r = client.post("/api/v1/auth/login", json={
        "username_or_email": "admin@codeguardian.ai",
        "password": demo_password,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body

def test_me_requires_auth(client) -> None:
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401

def test_docs_available_in_dev(client) -> None:
    r = client.get("/docs")
    assert r.status_code == 200
