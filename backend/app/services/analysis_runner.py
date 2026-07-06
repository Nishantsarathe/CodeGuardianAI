"""
Background analysis orchestrator — parallel agent execution.

Agents run in two parallel waves:
  Wave 1 (fast static): code_review, security, bug, dependency   (all at once)
  Wave 2 (generative):  refactor, documentation, test, uml       (all at once)
  Wave 3 (patch):       auto_fix                                  (needs wave-1 results)

This cuts wall-clock time roughly from N×T to max(T_wave1, T_wave2) + T_auto_fix.
"""
from __future__ import annotations

import asyncio
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.constants import HEALTH_SCORE_WEIGHTS
from app.core.logging import get_logger, log_event
from app.db.database import session_scope
from app.db.models import AgentRun, Analysis, AnalysisStatus, Finding, Project
from app.agents import BaseAgent, AGENT_REGISTRY, agent_for
from app.agents.base import AgentResult
from app.services.llm_service import check_ollama_available
from app.services.project_service import list_project_files, read_file_safe
from app.utils.filesystem import truncate


logger = get_logger("codeguardian.runner")

# Wave plan — agents within each wave run in parallel
WAVE_PLAN: List[List[str]] = [
    ["code_review", "security", "bug", "dependency"],   # Wave 1 — fast static
    ["refactor", "documentation", "test", "uml"],       # Wave 2 — generative
    ["auto_fix"],                                        # Wave 3 — patch
]

_loop: Optional[asyncio.AbstractEventLoop] = None
_loop_thread: Optional[threading.Thread] = None


def ensure_event_loop_thread() -> None:
    global _loop, _loop_thread
    if _loop is not None:
        return
    ready = threading.Event()

    def _run() -> None:
        global _loop
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        ready.set()
        _loop.run_forever()

    t = threading.Thread(target=_run, name="cg-loop", daemon=True)
    t.start()
    ready.wait(timeout=5.0)


def run_async(coro):
    if _loop is None:
        ensure_event_loop_thread()
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()  # type: ignore[arg-type]


def _build_agent_payload(project_id: str) -> dict:
    from pathlib import Path
    workdir = str(Path(settings.upload_dir) / project_id)
    files_on_disk = list_project_files(workdir)
    payload_files = []
    for f in files_on_disk[:150]:
        text = read_file_safe(f)
        if not text:
            continue
        try:
            rel = str(f.relative_to(workdir))
        except ValueError:
            rel = f.name
        payload_files.append({
            "path": rel,
            "language": _detect_lang(f),
            "content": text,
            "size": f.stat().st_size,
        })
    return {"project_id": project_id, "workdir": workdir, "files": payload_files}


def _detect_lang(path) -> str:
    from app.services.project_service import detect_language
    return detect_language(path) or "text"


def _compute_health_score(agent_summaries: dict) -> float:
    score = 0.0
    total_weight = 0.0
    for key, weight in HEALTH_SCORE_WEIGHTS.items():
        s = agent_summaries.get(key, {}).get("score")
        if s is None:
            continue
        try:
            score += float(s) * weight
            total_weight += weight
        except (TypeError, ValueError):
            continue
    if total_weight == 0:
        sec = agent_summaries.get("security", {})
        score = max(0.0, 100.0 - (
            sec.get("critical_count", 0) * 15
            + sec.get("high_count", 0) * 7
            + sec.get("medium_count", 0) * 2
        ))
    return round(max(0.0, min(100.0, score)), 2)


def _persist_findings(analysis_id: str, agent_name: str, findings: list) -> None:
    if not findings:
        return
    with session_scope() as db:
        for f in findings:
            db.add(Finding(
                analysis_id=analysis_id,
                agent_name=agent_name,
                category=f.get("category", "general"),
                severity=f.get("severity", "info"),
                title=(f.get("title") or "")[:255],
                description=f.get("description", ""),
                file_path=f.get("file_path"),
                line_start=f.get("line_start"),
                line_end=f.get("line_end"),
                rule_id=f.get("rule_id"),
                cvss_score=f.get("cvss_score"),
                cwe_id=f.get("cwe_id"),
                recommendation=f.get("recommendation"),
                code_snippet=f.get("code_snippet"),
                extras=f.get("extras") or {},
            ))


async def _run_one_agent(
    agent_name: str,
    analysis_id: str,
    payload: dict,
) -> Tuple[str, Optional[AgentResult]]:
    """Run a single agent, create/update its AgentRun, persist findings."""
    # Create run record
    with session_scope() as db:
        ar = AgentRun(
            analysis_id=analysis_id,
            agent_name=agent_name,
            status=AnalysisStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        db.add(ar)
        db.flush()
        agent_run_id = ar.id

    try:
        t0 = time.perf_counter()
        agent: BaseAgent = agent_for(agent_name)
        result: AgentResult = await agent.run(payload)
        duration = int((time.perf_counter() - t0) * 1000)

        with session_scope() as db:
            ar = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
            if ar:
                ar.status = AnalysisStatus.COMPLETED
                ar.finished_at = datetime.now(timezone.utc)
                ar.duration_ms = duration
                ar.output = getattr(result, "output", {}) or {}
                ar.confidence = getattr(result, "confidence", 0.8)

        _persist_findings(analysis_id, agent_name, result.findings or [])
        log_event(logger, 20, "agent_ok", agent=agent_name, ms=duration)
        return agent_name, result

    except Exception as e:
        msg = truncate(str(e), 500)
        log_event(logger, 40, "agent_failed", agent=agent_name, error=msg)
        with session_scope() as db:
            ar = db.query(AgentRun).filter(AgentRun.id == agent_run_id).first()
            if ar:
                ar.status = AnalysisStatus.FAILED
                ar.finished_at = datetime.now(timezone.utc)
                ar.error = msg
        return agent_name, None


async def _run_analysis_async(analysis_id: str) -> None:
    started = datetime.now(timezone.utc)

    with session_scope() as db:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        project_id = analysis.project_id
        analysis.status = AnalysisStatus.RUNNING
        analysis.started_at = started

    payload = _build_agent_payload(project_id)
    log_event(logger, 20, "analysis_started",
              analysis_id=analysis_id, files=len(payload["files"]))

    # Fail fast if the LLM backend is unreachable — without this check, every
    # agent's every LLM call independently retries against its own 30s
    # timeout (x2 for the fallback model), which compounds across dozens of
    # calls into a run that can take hours instead of failing in seconds.
    if not await check_ollama_available():
        with session_scope() as db:
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.finished_at = datetime.now(timezone.utc)
                analysis.error = (
                    "Could not reach the LLM backend (Ollama) at "
                    f"{settings.ollama_base_url}. Make sure `ollama serve` is "
                    "running and reachable from the backend process, then "
                    "retry the analysis."
                )
        log_event(logger, 40, "analysis_aborted_llm_unreachable",
                  analysis_id=analysis_id, ollama_base_url=settings.ollama_base_url)
        return

    agent_summaries: dict = {}

    # Execute each wave in parallel, waves sequentially
    for wave_idx, wave in enumerate(WAVE_PLAN):
        active = [name for name in wave if name in AGENT_REGISTRY]
        if not active:
            continue
        log_event(logger, 20, "wave_start", wave=wave_idx + 1, agents=active)

        tasks = [_run_one_agent(name, analysis_id, payload) for name in active]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        for agent_name, result in results:
            if result is not None:
                agent_summaries[agent_name] = getattr(result, "summary", {}) or {}

    # Finalise
    finished = datetime.now(timezone.utc)
    health = _compute_health_score(agent_summaries)

    with session_scope() as db:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = AnalysisStatus.COMPLETED
            analysis.finished_at = finished
            analysis.duration_ms = int((finished - started).total_seconds() * 1000)
            analysis.health_score = health
            analysis.summary = {
                "agents_run": list(agent_summaries.keys()),
                "agent_summaries": agent_summaries,
            }
            project = db.query(Project).filter(Project.id == analysis.project_id).first()
            if project:
                project.health_score = health
                project.updated_at = finished

    log_event(logger, 20, "analysis_finished",
              analysis_id=analysis_id, health=health,
              ms=int((finished - started).total_seconds() * 1000))


def run_analysis_job(analysis_id: str) -> None:
    """Entry point called from BackgroundTasks — runs in the background loop."""
    run_async(_run_analysis_async(analysis_id))


def run_single_agent(analysis_id: str, agent_name: str) -> None:
    with session_scope() as db:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        project_id = analysis.project_id
    payload = _build_agent_payload(project_id)

    async def _go():
        return await _run_one_agent(agent_name, analysis_id, payload)

    run_async(_go())
