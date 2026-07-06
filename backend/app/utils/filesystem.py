"""
Utility helpers used across the backend.
"""
from __future__ import annotations

import hashlib
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


_WHITESPACE = re.compile(r"\s+")


def sha256_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text or "").strip()


def truncate(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def safe_join(root: str, *parts: str) -> str:
    """Join paths safely, raising if the result escapes ``root``."""
    base = os.path.realpath(root)
    target = os.path.realpath(os.path.join(base, *parts))
    if not target.startswith(base):
        raise ValueError("Path traversal attempt")
    return target


def list_source_files(root: Path, exts: Iterable[str]) -> List[Path]:
    exts = tuple(e.lower() for e in exts)
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]


@contextmanager
def timed() -> Iterator[float]:
    """Context manager that yields a mutable float holding elapsed ms."""
    start = time.perf_counter()
    elapsed = [0.0]

    def _elapsed() -> float:
        return (time.perf_counter() - start) * 1000.0

    try:
        yield _elapsed
    finally:
        elapsed[0] = _elapsed()


def chunked(seq: List, size: int) -> Iterable[list]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def safe_read_text(path: Path, max_bytes: int = 5 * 1024 * 1024) -> Optional[str]:
    try:
        if path.stat().st_size > max_bytes:
            return None
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None
