"""
FastAPI application entry-point.

Wires together:
- Configuration & logging
- Database bootstrap
- CORS, rate limiting, error handlers
- Routers
- Startup tasks (ChromaDB warm-up, demo user seeding — dev/test only)
"""
from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import (
    agents_router, analyses_router, auth_router, chat_router,
    dashboard_router, projects_router, reports_router, uploads_router,
    users_router,
)
from app.core.config import configure_logging, settings
from app.core.exceptions import CodeGuardianException
from app.core.logging import get_logger, log_event
from app.db.database import init_db
from app.db.models import User, UserRole
from app.security.auth import hash_password
from app.services.analysis_runner import ensure_event_loop_thread
from app.services.vector_store import warm_up


logger = get_logger("codeguardian.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup/shutdown hooks for the FastAPI app."""
    configure_logging()
    log_event(logger, 20, "startup", env=settings.app_env, version=settings.app_version)

    # Database
    init_db()

    # Seed a demo admin only in non-production environments
    if not settings.is_production:
        _seed_demo_user()

    # Background loop for sync agents
    ensure_event_loop_thread()

    # Vector store
    try:
        warm_up()
    except Exception as e:  # pragma: no cover
        log_event(logger, 30, "chroma_warmup_failed", error=str(e))

    yield
    log_event(logger, 20, "shutdown", env=settings.app_env)


# Disable interactive docs in production for security
_docs_url = None if settings.is_production else "/docs"
_redoc_url = None if settings.is_production else "/redoc"
_openapi_url = None if settings.is_production else "/openapi.json"

app = FastAPI(
    title="CodeGuardian AI",
    description="Autonomous Multi-Agent Code Review & Security Platform",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# CORS — allow the configured frontend origin (and localhost variants for dev)
_cors_origins = [settings.frontend_base_url]
if not settings.is_production:
    _cors_origins += ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Error handlers --------------------
@app.exception_handler(CodeGuardianException)
async def _app_exception_handler(request: Request, exc: CodeGuardianException) -> JSONResponse:
    log_event(logger, 30, "app_error", path=request.url.path, code=exc.code, message=str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": "validation_error", "message": "Request validation failed", "data": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": "http_error", "message": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:  # noqa: BLE001
    log_event(logger, 40, "unhandled", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"code": "internal_error", "message": "Internal server error"})


# -------------------- Routers --------------------
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(analyses_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


# -------------------- Health & root --------------------
@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "docs": "/docs" if not settings.is_production else None,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


def _seed_demo_user() -> None:
    """Create a default admin account on first start (development/test only).

    The password is printed to the log so operators know what it is without
    it being baked into the login form or visible in source code.
    A random suffix is added so this cannot be brute-forced by knowing the
    repo's default. Set DEMO_ADMIN_PASSWORD in your .env to override.
    """
    from app.db.database import session_scope

    with session_scope() as db:
        existing = db.query(User).filter(User.email == "admin@codeguardian.ai").first()
        if existing:
            return

        raw = settings.demo_admin_password or f"CG-{secrets.token_urlsafe(10)}"
        demo_password = raw[:72]  # bcrypt enforces 72-byte max
        admin = User(
            email="admin@codeguardian.ai",
            username="admin",
            full_name="CodeGuardian Admin",
            hashed_password=hash_password(demo_password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        log_event(logger, 20, "demo_user_seeded",
                  email=admin.email,
                  password_hint=f"{demo_password[:4]}***  (set DEMO_ADMIN_PASSWORD to override)")
