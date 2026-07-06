"""
Base classes shared by all agents.

Every agent implements :meth:`BaseAgent.run`, returning an
:class:`AgentResult` that the orchestrator persists into the database.

Speed guidelines for agent LLM calls
-------------------------------------
- Always pass ``fast=True`` to use the 30s/400-token analysis tier.
- Keep prompts under 2 000 tokens — truncate file content aggressively.
- Use ``_truncate_files(max_files=3, max_chars=1200)`` for the LLM pass.
- Rely on regex/heuristics for the bulk of findings; LLM adds context only.
"""
from __future__ import annotations

import abc
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.llm_service import llm_complete, llm_json


logger = get_logger("codeguardian.agents")


@dataclass
class AgentResult:
    agent_name: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8
    error: Optional[str] = None


class BaseAgent(abc.ABC):
    name: str = "base"

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs

    @abc.abstractmethod
    async def run(self, payload: Dict[str, Any]) -> AgentResult: ...

    def _project_meta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "project_id": payload.get("project_id"),
            "workdir": payload.get("workdir"),
            "file_count": len(payload.get("files", [])),
        }

    async def _llm(self, prompt: str, *, system: Optional[str] = None,
                   json_mode: bool = False, fast: bool = True) -> str:
        """Call the LLM. Defaults to fast=True (30s / 400 token analysis tier)."""
        return await llm_complete(prompt, system=system, json_mode=json_mode, fast=fast)

    async def _llm_json(self, prompt: str, *, system: Optional[str] = None,
                        fast: bool = True) -> Dict[str, Any]:
        return await llm_json(prompt, system=system, fast=fast)

    def _truncate_files(self, payload: Dict[str, Any],
                        max_files: int = 3,
                        max_chars: int = 1200) -> List[Dict[str, Any]]:
        """Return at most ``max_files`` files, each capped at ``max_chars`` chars."""
        files = payload.get("files", [])[:max_files]
        return [{**f, "content": (f.get("content") or "")[:max_chars]} for f in files]

    def _format_files(self, files: List[Dict[str, Any]]) -> str:
        return "\n\n".join(
            f"### {f.get('path', '?')}\n```{f.get('language', '')}\n"
            f"{f.get('content', '')}\n```"
            for f in files
        )


def safe_text(text: str, limit: int = 2000) -> str:
    return (text or "")[:limit]


_JSON_BLOCK = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def extract_json_blob(text: str) -> Optional[Any]:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for opener, closer in ("[", "]"), ("{", "}"):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start: end + 1])
            except json.JSONDecodeError:
                continue
    return None
