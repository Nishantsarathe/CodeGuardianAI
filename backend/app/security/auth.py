"""
JWT-based authentication with refresh tokens and password hashing.

Uses ``bcrypt`` directly for password storage (passlib is incompatible
with bcrypt ≥ 4.x in some environments) and PyJWT for token signing.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)

# bcrypt hard-limit: passwords are truncated to 72 bytes before hashing
_MAX_BYTES = 72


def _prepare(password: str) -> bytes:
    """Encode and truncate a password to the bcrypt byte limit."""
    return password.encode("utf-8")[:_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt (cost 12)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(_prepare(password), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def _create_token(
    payload: Dict[str, Any],
    expires_delta: timedelta,
    token_type: str = "access",
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "type": token_type,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str | int, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Generate a short-lived access JWT."""
    payload: Dict[str, Any] = {"sub": str(subject)}
    if extra_claims:
        payload.update(extra_claims)
    return _create_token(
        payload,
        expires_delta=timedelta(minutes=settings.jwt_access_ttl_min),
        token_type="access",
    )


def create_refresh_token(subject: str | int) -> str:
    """Generate a long-lived refresh JWT."""
    return _create_token(
        {"sub": str(subject)},
        expires_delta=timedelta(days=settings.jwt_refresh_ttl_days),
        token_type="refresh",
    )


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate a JWT, raising ``ValueError`` on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as e:
        raise ValueError("token_expired") from e
    except jwt.InvalidTokenError as e:
        raise ValueError(f"invalid_token: {e}") from e

    if payload.get("type") != expected_type:
        raise ValueError(
            f"wrong_token_type: expected={expected_type}, got={payload.get('type')}"
        )
    return payload
