"""Pydantic v2 schemas for the public API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import AnalysisStatus, Severity, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ----------- Auth -----------
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER


class UserOut(ORMModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: UserRole


class LoginIn(BaseModel):
    username_or_email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ----------- Project -----------
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: str = Field(default="folder", pattern="^(github|zip|folder|file)$")
    source_ref: Optional[str] = None
    language: Optional[str] = None


class ProjectOut(ORMModel):
    id: str
    name: str
    description: Optional[str]
    source_type: str
    source_ref: Optional[str]
    language: Optional[str]
    size_bytes: int
    file_count: int
    health_score: Optional[float]
    owner_id: str
    created_at: datetime
    updated_at: datetime


class ProjectStats(BaseModel):
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    size_bytes: int
    file_types: Dict[str, int]


# ----------- Analysis -----------
class AnalysisCreate(BaseModel):
    project_id: str
    config: Optional[Dict[str, Any]] = None
    agents: Optional[List[str]] = None  # subset of agents to run


class AgentRunOut(ORMModel):
    id: str
    agent_name: str
    status: AnalysisStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    confidence: Optional[float]
    error: Optional[str]


class FindingOut(ORMModel):
    id: str
    agent_name: str
    category: str
    severity: Severity
    title: str
    description: str
    file_path: Optional[str]
    line_start: Optional[int]
    line_end: Optional[int]
    rule_id: Optional[str]
    cvss_score: Optional[float]
    cwe_id: Optional[str]
    recommendation: Optional[str]
    code_snippet: Optional[str]
    extras: Optional[Dict[str, Any]]
    created_at: datetime


class AnalysisOut(ORMModel):
    id: str
    project_id: str
    status: AnalysisStatus
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    health_score: Optional[float]
    summary: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    agent_runs: List[AgentRunOut] = Field(default_factory=list)
    findings: List[FindingOut] = Field(default_factory=list)


class AnalysisStatusOut(BaseModel):
    id: str
    status: AnalysisStatus
    progress: int = Field(default=0, ge=0, le=100)
    current_agent: Optional[str] = None
    current_agents: List[str] = []
    message: Optional[str] = None
    agent_runs: List[AgentRunOut] = Field(default_factory=list)


# ----------- Chat -----------
class ChatMessageIn(BaseModel):
    content: str
    analysis_id: Optional[str] = None


class ChatMessageOut(ORMModel):
    id: str
    role: str
    content: str
    extras: Optional[Dict[str, Any]]
    created_at: datetime


class ChatSessionOut(ORMModel):
    id: str
    title: str
    analysis_id: Optional[str]
    created_at: datetime
    messages: List[ChatMessageOut] = Field(default_factory=list)


# ----------- Reports -----------
class ReportOut(BaseModel):
    id: str
    analysis_id: str
    format: str
    url: str
    size_bytes: int
    created_at: datetime
