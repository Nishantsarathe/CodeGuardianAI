"""Shared pytest fixtures for the CodeGuardian AI test suite."""
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-padded!!")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-32-chars-padded!!!")
os.environ.setdefault("DEMO_ADMIN_PASSWORD", "TestPass123!")  # < 72 bytes

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
