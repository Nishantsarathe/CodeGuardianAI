"""Structured logging utilities with PII redaction."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

# Patterns that look like secrets — redacted in logs
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*['\"]?([\w\-./+=]{6,})"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]


def redact(value: Any) -> Any:
    """Recursively redact secret-like substrings in a log payload."""
    if isinstance(value, str):
        for pat in _SECRET_PATTERNS:
            value = pat.sub(lambda m: m.group(0).split(m.group(2))[0] + "***REDACTED***", value)
        return value
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


class RedactingFilter(logging.Filter):
    """Filter that scrubs secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            record.args = tuple(redact(a) for a in record.args) if isinstance(record.args, tuple) \
                else redact(record.args)
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the redacting filter attached."""
    logger = logging.getLogger(name)
    if not any(isinstance(f, RedactingFilter) for f in logger.filters):
        logger.addFilter(RedactingFilter())
    return logger


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Log a structured event with redacted fields."""
    safe = redact(fields)
    extras = " ".join(f"{k}={v!r}" for k, v in safe.items())
    logger.log(level, f"{event} | {extras}")
