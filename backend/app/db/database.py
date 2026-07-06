"""
SQLAlchemy database session, engine and base class.

Uses SQLite by default. All session interactions go through
the ``get_db`` dependency.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _make_engine():
    url = settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True, echo=False)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a transactional database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context manager for use outside of FastAPI request lifecycle."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables (idempotent). Safe to call at startup."""
    # Ensure the SQLite file directory exists
    if settings.database_url.startswith("sqlite:///"):
        db_file = settings.database_url.replace("sqlite:///", "", 1)
        os.makedirs(os.path.dirname(os.path.abspath(db_file)) or ".", exist_ok=True)
    # Importing models registers them with Base.metadata
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
