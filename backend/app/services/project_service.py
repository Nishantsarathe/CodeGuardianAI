"""
Project ingestion and scanning service.

Supports GitHub clone, ZIP extraction, and direct folder / single-file
ingestion. Builds a quick file index with language detection.
"""
from __future__ import annotations

import os
import shutil
import tarfile
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core.constants import LANGUAGE_EXTENSIONS
from app.core.exceptions import FileUploadError, ValidationError
from app.core.logging import get_logger


logger = get_logger("codeguardian.project")


LANGUAGE_LOOKUP: Dict[str, str] = {}
for lang, exts in LANGUAGE_EXTENSIONS.items():
    for ext in exts:
        LANGUAGE_LOOKUP[ext] = lang


def detect_language(path: Path) -> Optional[str]:
    return LANGUAGE_LOOKUP.get(path.suffix.lower())


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    """Safely extract a zip protecting against zip-slip traversal.

    Preserves subdirectory structure while rejecting any entry whose
    resolved path escapes ``dest``.
    """
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Build the target path and resolve it
            target = (dest / member.filename).resolve()
            # Reject entries that escape the destination directory
            try:
                target.relative_to(dest_resolved)
            except ValueError:
                raise FileUploadError(
                    detail=f"Unsafe zip entry (path traversal): {member.filename}",
                    code="zip_slip",
                )
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)


def _safe_extract_tar(tgz_path: Path, dest: Path) -> None:
    """Safely extract a tarball, blocking path traversal and symlink attacks.

    Validates every member against the destination directory before
    extracting (Python 3.11 compatible — does not rely on filter='data').
    """
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    with tarfile.open(tgz_path, "r:*") as tf:
        for member in tf.getmembers():
            # Reject absolute paths, symlinks pointing outside, and traversal
            if os.path.isabs(member.name) or member.name.startswith(".."):
                raise FileUploadError(
                    detail=f"Unsafe tar entry: {member.name}", code="tar_slip"
                )
            target = (dest / member.name).resolve()
            try:
                target.relative_to(dest_resolved)
            except ValueError:
                raise FileUploadError(
                    detail=f"Unsafe tar entry (path traversal): {member.name}",
                    code="tar_slip",
                )
            if member.issym() or member.islnk():
                # Resolve symlink destination and check it stays inside dest
                link_target = (target.parent / member.linkname).resolve()
                try:
                    link_target.relative_to(dest_resolved)
                except ValueError:
                    raise FileUploadError(
                        detail=f"Symlink escapes destination: {member.name} -> {member.linkname}",
                        code="tar_symlink",
                    )
        # All members validated — now extract
        tf.extractall(dest)  # noqa: S202 — already validated above


def fetch_github_repo(url: str, dest_dir: str, token: Optional[str] = None) -> None:
    """Clone a GitHub repository (or download a tarball if git is unavailable)."""
    if not url.startswith(("http://", "https://", "git@")):
        raise ValidationError(detail=f"Invalid GitHub URL: {url}")
    parsed = urlparse(url)
    if "github.com" not in (parsed.netloc or ""):
        raise ValidationError(detail="Only github.com URLs are supported")

    # Try git clone first
    try:
        import subprocess
        cmd = ["git", "clone", "--depth", "1"]
        clone_url = url
        if token and parsed.netloc == "github.com":
            # Inject token into https URL safely
            clone_url = url.replace("https://", f"https://{token}@")
        cmd += [clone_url, dest_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return
        logger.warning(f"git clone failed: {(result.stderr or '')[:500]}")
    except FileNotFoundError:
        pass  # git not installed
    except Exception as e:
        logger.warning(f"git clone exception: {e}")

    # Fallback: download tarball via the GitHub API
    try:
        import httpx
        parts = parsed.path.strip("/").replace(".git", "").split("/")
        if len(parts) < 2:
            raise ValidationError(detail="Cannot derive owner/repo from URL")
        owner, repo = parts[0], parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/tarball"
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp:
            tgz_path = Path(tmp.name)

        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            with client.stream("GET", api_url, headers=headers) as r:
                r.raise_for_status()
                with tgz_path.open("wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)

        # Extract safely into a temp dir, then move contents to dest_dir
        with tempfile.TemporaryDirectory() as td:
            _safe_extract_tar(tgz_path, Path(td))
            inner = next(Path(td).iterdir(), None)
            if inner and inner.is_dir():
                for child in inner.iterdir():
                    shutil.move(str(child), str(Path(dest_dir) / child.name))
            else:
                # Flat tarball — move everything
                for child in Path(td).iterdir():
                    shutil.move(str(child), str(Path(dest_dir) / child.name))

        tgz_path.unlink(missing_ok=True)
    except (FileUploadError, ValidationError):
        raise
    except Exception as e:
        raise FileUploadError(detail=f"Failed to fetch GitHub repo: {e}", code="github_fetch") from e


def validate_source_ref(source_ref: str, source_type: str) -> bool:
    """Return True if ``source_ref`` is acceptable for ``source_type``."""
    if not source_ref:
        return False
    if source_type == "file":
        return Path(source_ref).exists() and Path(source_ref).is_file()
    if source_type in {"zip", "folder"}:
        return Path(source_ref).exists()
    return True


def scan_project_folder(work_dir: str, source_ref: str, source_type: str) -> Dict:
    """Index files in the workspace and return basic statistics."""
    root = Path(work_dir)
    if source_type == "zip" and source_ref.endswith(".zip") and Path(source_ref).is_file():
        _safe_extract_zip(Path(source_ref), root)
    elif source_type == "file" and Path(source_ref).is_file():
        shutil.copy2(source_ref, root / Path(source_ref).name)

    total_lines = 0
    total_files = 0
    size_bytes = 0
    languages: Counter = Counter()
    file_types: Counter = Counter()

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        total_files += 1
        stat = p.stat()
        size_bytes += stat.st_size
        ext = p.suffix.lower()
        file_types[ext] += 1
        lang = LANGUAGE_LOOKUP.get(ext)
        if lang:
            languages[lang] += 1
        try:
            if stat.st_size <= 5 * 1024 * 1024:
                total_lines += p.read_bytes().count(b"\n")
        except OSError:
            pass

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "languages": dict(languages),
        "size_bytes": size_bytes,
        "file_types": dict(file_types),
    }


def list_project_files(work_dir: str) -> List[Path]:
    """Return all source files under ``work_dir``."""
    root = Path(work_dir)
    if not root.exists():
        return []
    exts = set(LANGUAGE_LOOKUP.keys())
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def read_file_safe(path: Path, max_bytes: int = 5 * 1024 * 1024) -> Optional[str]:
    """Read a source file, capping at ``max_bytes``."""
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
