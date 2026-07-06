"""
Role-based access control.

Defines :class:`Role` and :func:`require_roles` to gate routes.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable

from fastapi import Depends, Request

from app.core.exceptions import AuthorizationError


class Role(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


ROLE_HIERARCHY = {
    Role.VIEWER: 0,
    Role.REVIEWER: 1,
    Role.ADMIN: 2,
}


def has_role(user_role: str | Role, required: Role) -> bool:
    """Return True if ``user_role`` satisfies ``required`` (hierarchical)."""
    try:
        user = Role(user_role)
    except ValueError:
        return False
    return ROLE_HIERARCHY[user] >= ROLE_HIERARCHY[required]


def require_roles(*required: Role):
    """Build a FastAPI dependency that enforces a role (or higher)."""
    async def _dep(request: Request) -> None:
        user = getattr(request.state, "user", None)
        if not user:
            raise AuthorizationError(detail="Authentication required")
        user_role = user.get("role", Role.VIEWER.value)
        for r in required:
            if not has_role(user_role, r):
                raise AuthorizationError(detail=f"Requires role: {r.value}")
    return _dep
