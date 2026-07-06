"""Authentication routes — register, login, refresh, me."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import LoginIn, TokenOut, UserCreate, UserOut
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.db.database import get_db
from app.db.models import AuditLog, User, UserRole
from app.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _audit(
    db: Session,
    user_id: str | None,
    action: str,
    request: Request,
    status_code: int = 200,
    extras: dict | None = None,
) -> None:
    db.add(AuditLog(
        user_id=user_id,
        action=action,
        target=str(request.url.path),
        ip_address=request.client.host if request.client else None,
        status_code=status_code,
        extras=extras or {},
    ))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> UserOut:
    """Register a new user. The very first registered user becomes admin."""
    existing = db.query(User).filter(
        (User.email == payload.email) | (User.username == payload.username)
    ).first()
    if existing:
        raise ValidationError(detail="Email or username already registered", code="user_exists")

    user_count = db.query(User).count()
    # First user ever → admin. Every subsequent self-registration is forced
    # to viewer regardless of what the client sends in payload.role — role
    # is not something a client should be able to grant itself. Admins
    # promote users afterwards via PATCH /users/{id}/role.
    role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.flush()
    _audit(db, user.id, "user.register", request, status_code=201)
    db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    """Authenticate a user and return access + refresh tokens."""
    user = db.query(User).filter(
        (User.email == payload.username_or_email) | (User.username == payload.username_or_email)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        _audit(db, user.id if user else None, "user.login_failed", request, status_code=401)
        raise AuthenticationError(detail="Invalid credentials", code="invalid_credentials")

    if not user.is_active:
        raise AuthenticationError(detail="Account is disabled", code="user_disabled")

    user.last_login = datetime.now(timezone.utc)
    access  = create_access_token(user.id, extra_claims={"role": user.role.value, "username": user.username})
    refresh = create_refresh_token(user.id)
    _audit(db, user.id, "user.login", request)
    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_ttl_min * 60,
    )


@router.post("/refresh", response_model=TokenOut)
def refresh_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db),
) -> TokenOut:
    """Exchange a refresh token for a fresh access + refresh pair."""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except ValueError as e:
        raise AuthenticationError(detail=str(e)) from e
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user or not user.is_active:
        raise AuthenticationError(detail="User not found", code="user_not_found")
    access      = create_access_token(user.id, extra_claims={"role": user.role.value, "username": user.username})
    new_refresh = create_refresh_token(user.id)
    _audit(db, user.id, "user.refresh", request)
    return TokenOut(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.jwt_access_ttl_min * 60,
    )


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)) -> UserOut:
    """Return the currently authenticated user."""
    return UserOut.model_validate(current)
