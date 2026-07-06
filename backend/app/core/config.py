"""
Centralized application configuration.

All values are read from environment variables — never hard-code
secrets. A single ``Settings`` instance is exported and reused
everywhere via FastAPI's dependency injection system.
"""
from __future__ import annotations

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/core/config.py → repo root


class Settings(BaseSettings):
    """Application settings populated from the environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", str(PROJECT_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- General -----
    app_name: str = Field(default="CodeGuardian-AI", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    frontend_base_url: str = Field(default="http://localhost:3000", alias="FRONTEND_BASE_URL")

    # ----- Security -----
    secret_key: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY") or secrets.token_hex(32),
        alias="SECRET_KEY",
    )
    jwt_secret: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET") or secrets.token_hex(32),
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_ttl_min: int = Field(default=60, alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(default=7, alias="JWT_REFRESH_TTL_DAYS")
    rate_limit_per_min: int = Field(default=60, alias="RATE_LIMIT_PER_MIN")

    # ----- Database -----
    database_url: str = Field(default="sqlite:///./codeguardian.db", alias="DATABASE_URL")

    # ----- Vector DB -----
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")
    chroma_collection: str = Field(default="codeguardian", alias="CHROMA_COLLECTION")

    # ----- LLM -----
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_default_model: str = Field(default="gemma2:2b", alias="OLLAMA_DEFAULT_MODEL")
    ollama_fallback_model: str = Field(default="qwen2.5-coder:7b", alias="OLLAMA_FALLBACK_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")
    llm_timeout_sec: int = Field(default=120, alias="LLM_TIMEOUT_SEC")

    # ----- Agents -----
    agent_max_retries: int = Field(default=2, alias="AGENT_MAX_RETRIES")
    agent_parallel_limit: int = Field(default=4, alias="AGENT_PARALLEL_LIMIT")
    agent_verbose: bool = Field(default=True, alias="AGENT_VERBOSE")

    # ----- Uploads -----
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=100, alias="MAX_UPLOAD_MB")
    allowed_exts: str = Field(
        default=".py,.java,.js,.ts,.tsx,.jsx,.go,.rs,.c,.cc,.cpp,.h,.hpp,.cs,.zip,.tar,.gz",
        alias="ALLOWED_EXTS",
    )

    # ----- MCP -----
    enable_mcp_filesystem: bool = Field(default=True, alias="ENABLE_MCP_FILESYSTEM")
    enable_mcp_github: bool = Field(default=True, alias="ENABLE_MCP_GITHUB")
    enable_mcp_sqlite: bool = Field(default=True, alias="ENABLE_MCP_SQLITE")
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # ----- Demo -----
    demo_admin_password: Optional[str] = Field(default=None, alias="DEMO_ADMIN_PASSWORD")

    # ----- Logging -----
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="./logs/codeguardian.log", alias="LOG_FILE")

    # -------------------- helpers --------------------
    @property
    def allowed_extensions(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_exts.split(",") if ext.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @field_validator("app_env")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        if v.lower() not in {"development", "staging", "production", "test"}:
            raise ValueError("APP_ENV must be development|staging|production|test")
        return v.lower()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    Using ``lru_cache`` ensures we read the environment only once
    and avoid hitting the disk on every request.
    """
    return Settings()


settings = get_settings()


def configure_logging() -> None:
    """Configure root + application loggers with rotating file handler."""
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

    root = logging.getLogger()
    root.setLevel(level)
    # Reset handlers (uvicorn may have added its own)
    root.handlers.clear()

    # File handler
    try:
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
        fh.setFormatter(logging.Formatter(fmt))
        root.addHandler(fh)
    except Exception:
        # Fallback to stderr if file logging fails
        pass

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(fmt))
    root.addHandler(sh)

    # Quiet noisy libs
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("codeguardian").setLevel(level)
