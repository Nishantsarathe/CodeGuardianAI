"""Auth dependency utilities — shared by routers."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.db.database import get_db
from app.db.models import User
from app.security.auth import decode_token


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Decode the Authorization header and return the active user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError(detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as e:
        raise AuthenticationError(detail=str(e)) from e

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    if not user or not user.is_active:
        raise AuthenticationError(detail="User not found or inactive")

    # Stash the role on request state for RBAC
    request.state.user = {"id": user.id, "role": user.role.value if hasattr(user.role, "value") else user.role,
                          "username": user.username}
    return user
