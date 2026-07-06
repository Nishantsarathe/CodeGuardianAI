"""Admin-only user management — list users and change roles.

Self-registration always creates a `viewer` (see auth.register). The only
way to grant `reviewer`/`admin` afterwards is through these endpoints, which
require the caller to already be an admin.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import UserOut, UserRoleUpdate
from app.core.exceptions import NotFoundError, ValidationError
from app.db.database import get_db
from app.db.models import AuditLog, User, UserRole
from app.security.rbac import Role, require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_roles(Role.ADMIN))])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    """List all users. Admin only."""
    users = db.query(User).order_by(User.created_at.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.patch(
    "/{user_id}/role",
    response_model=UserOut,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def update_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserOut:
    """Promote or demote a user's role. Admin only.

    An admin cannot demote themselves out of the admin role — that would
    risk leaving the instance with no admin able to undo the change.
    """
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise NotFoundError(detail="User not found")

    if target.id == current.id and payload.role != UserRole.ADMIN:
        raise ValidationError(
            detail="You can't remove your own admin role. Ask another admin to do it.",
            code="cannot_self_demote",
        )

    previous_role = target.role.value if hasattr(target.role, "value") else target.role
    target.role = payload.role
    db.add(AuditLog(
        user_id=current.id,
        action="user.role_updated",
        target=f"user:{target.id}",
        ip_address=request.client.host if request.client else None,
        status_code=200,
        extras={"previous_role": previous_role, "new_role": payload.role.value, "target_email": target.email},
    ))
    db.flush()
    db.refresh(target)
    return UserOut.model_validate(target)
