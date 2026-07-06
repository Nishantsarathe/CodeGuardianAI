"""AI chat routes — create session, list messages, send message."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import ChatMessageIn, ChatMessageOut, ChatSessionOut
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import Analysis, ChatMessage, ChatSession, Project, User
from app.services.chat_service import generate_assistant_reply


router = APIRouter(prefix="/chat", tags=["chat"])


def _get_session(db: Session, session_id: str, user: User) -> ChatSession:
    s = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    ).first()
    if not s:
        raise NotFoundError(detail="Chat session not found")
    return s


@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    request: Request,
    analysis_id: Optional[str] = None,
    title: str = "New chat",
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ChatSessionOut:
    """Create a new chat session optionally bound to an analysis."""
    s = ChatSession(user_id=current.id, analysis_id=analysis_id, title=title)
    db.add(s)
    db.flush()
    db.refresh(s)
    return ChatSessionOut.model_validate(s)


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[ChatSessionOut]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current.id)
        .order_by(desc(ChatSession.created_at))
        .limit(100)
        .all()
    )
    return [ChatSessionOut.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ChatSessionOut:
    s = _get_session(db, session_id, current)
    return ChatSessionOut.model_validate(s)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def post_message(
    session_id: str,
    payload: ChatMessageIn,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ChatMessageOut:
    s = _get_session(db, session_id, current)
    # Persist user message
    user_msg = ChatMessage(session_id=s.id, role="user", content=payload.content)
    db.add(user_msg)
    db.flush()

    # Build a project context for the assistant
    context = _build_context(db, s)

    reply_text, extras = generate_assistant_reply(
        user_id=current.id,
        session_id=s.id,
        user_message=payload.content,
        context=context,
    )
    assistant_msg = ChatMessage(
        session_id=s.id, role="assistant", content=reply_text, extras=extras or {}
    )
    db.add(assistant_msg)
    db.flush()  # assign PK so the row is "persistent" for db.refresh() below
    # Auto-name the session from the first user message
    if s.title == "New chat" and payload.content.strip():
        s.title = payload.content.strip()[:60]
    db.refresh(assistant_msg)
    return ChatMessageOut.model_validate(assistant_msg)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    s = _get_session(db, session_id, current)
    db.delete(s)
    return None


def _build_context(db: Session, session: ChatSession) -> dict:
    """Return a small dict describing the analysis the user is chatting about."""
    if not session.analysis_id:
        return {}
    analysis = db.query(Analysis).filter(Analysis.id == session.analysis_id).first()
    if not analysis:
        return {}
    project = db.query(Project).filter(Project.id == analysis.project_id).first()
    return {
        "project_name": project.name if project else None,
        "project_language": project.language if project else None,
        "analysis_status": analysis.status.value if hasattr(analysis.status, "value") else str(analysis.status),
        "health_score": analysis.health_score,
        "findings_count": len(analysis.findings or []),
    }
