"""
Chat service — turns user prompts + analysis context into LLM answers.
Uses a simple RAG pattern: query ChromaDB for relevant snippets, then
ask the LLM to answer grounded in those snippets.

``generate_assistant_reply`` is a synchronous function that runs the
async LLM call via ``asyncio.run`` / the background event loop so it
can be called from sync FastAPI route handlers.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Tuple

from app.core.logging import get_logger
from app.services.llm_service import check_ollama_available, llm_complete
from app.services.vector_store import search


logger = get_logger("codeguardian.chat")


SYSTEM_PROMPT = (
    "You are CodeGuardian Assistant, an expert Staff-Engineer-level AI for code "
    "review, security analysis, refactoring, testing, and architecture. "
    "Answer concisely, with code examples when useful. If a question concerns a "
    "specific project, prefer the supplied context. If you do not know, say so. "
    "Do NOT fabricate file paths, line numbers, or vulnerabilities."
)


def _format_context(context: Dict, retrieved: list) -> str:
    parts: list[str] = []
    if context:
        parts.append("## Project context")
        for k, v in context.items():
            parts.append(f"- {k}: {v}")
    if retrieved:
        parts.append("\n## Relevant code snippets")
        for r in retrieved[:5]:
            meta = r.get("metadata", {})
            path = meta.get("path", meta.get("file", "?"))
            text = (r.get("text") or "")[:1500]
            parts.append(f"### {path}\n```\n{text}\n```")
    return "\n".join(parts)


async def _async_reply(prompt: str) -> str:
    """Internal coroutine — separated so it can be awaited properly."""
    return await llm_complete(prompt, system=SYSTEM_PROMPT)


def generate_assistant_reply(user_id: str, session_id: str, user_message: str,
                              context: Dict | None = None) -> Tuple[str, Dict]:
    """Produce a single assistant turn for the chat session.

    This is a *synchronous* function intentionally — the FastAPI route
    handler that calls it is also sync. The async LLM call is executed
    via the shared background event loop (or a fresh ``asyncio.run``
    if the loop thread isn't available yet).
    """
    retrieved: list = []
    project_id = (context or {}).get("project_id")
    if project_id:
        try:
            retrieved = search(project_id, user_message, n_results=5)
        except Exception:  # pragma: no cover
            retrieved = []

    ctx_block = _format_context(context or {}, retrieved)
    prompt = (
        f"## Conversation context\n{ctx_block}\n\n"
        f"## User question\n{user_message.strip()}\n\n"
        "## Instructions\n- Answer in markdown.\n- Use the provided code snippets when relevant.\n"
        "- Cite file paths in backticks.\n- Keep answers under 400 words unless the user asks for detail."
    )

    try:
        # Re-use the background event loop started by the analysis runner
        from app.services.analysis_runner import _loop

        def _run_with_availability_check():
            async def _guarded():
                if not await check_ollama_available():
                    raise RuntimeError("ollama_unreachable")
                return await _async_reply(prompt)
            return _guarded()

        if _loop is not None and _loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(_run_with_availability_check(), _loop)
            # ~2s to fail if unreachable (see check_ollama_available), else up
            # to the full chat-tier timeout for a real generation.
            reply = fut.result(timeout=125)
        else:
            reply = asyncio.run(_run_with_availability_check())
    except Exception as e:
        logger.warning(f"LLM chat failed: {e}")
        model = (context or {}).get("default_model", "gemma2:2b") if context else "gemma2:2b"
        reply = (
            "I couldn't reach the local language model. "
            "Make sure Ollama is running (`ollama serve`) and the model "
            f"is pulled (`ollama pull {model}`)."
        )
    extras = {"sources": [r.get("metadata", {}).get("path") for r in retrieved]}
    return reply, extras
