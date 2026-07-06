"""Custom application exceptions mapped to HTTP responses."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class CodeGuardianException(HTTPException):
    """Base exception for all CodeGuardian-specific errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "Internal server error"
    code: str = "internal_error"

    def __init__(self, detail: Optional[str] = None, code: Optional[str] = None,
                 status_code: Optional[int] = None, extras: Optional[Dict[str, Any]] = None):
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        payload: Dict[str, Any] = {"code": self.code, "message": detail or self.detail}
        if extras:
            payload["data"] = extras
        super().__init__(status_code=self.status_code, detail=payload)


class NotFoundError(CodeGuardianException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"
    code = "not_found"


class ValidationError(CodeGuardianException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"
    code = "validation_error"


class AuthenticationError(CodeGuardianException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required"
    code = "auth_error"


class AuthorizationError(CodeGuardianException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
    code = "forbidden"


class RateLimitError(CodeGuardianException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Rate limit exceeded"
    code = "rate_limited"


class AgentExecutionError(CodeGuardianException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Agent execution failed"
    code = "agent_error"


class FileUploadError(CodeGuardianException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "File upload error"
    code = "upload_error"
