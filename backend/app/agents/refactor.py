"""
Refactoring Agent — proposes SOLID-aligned, design-pattern-friendly
refactors.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


class RefactorAgent(BaseAgent):
    name = "refactor"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        files = self._truncate_files(payload, max_files=5, max_chars=2200)
        if not files:
            return AgentResult(self.name, summary={"score": 0}, confidence=0.5)

        prompt = (
            "Suggest refactorings aligned with SOLID, KISS, DRY and the GoF design patterns. "
            "Return JSON {\"suggestions\":[...]} with fields: title, severity (info|low|medium), "
            "category (architecture|performance|maintainability|readability|reusability), "
            "description, file_path, line_start, line_end, recommendation, pattern (optional).\n\n"
            f"Files:\n{self._format_files(files)}"
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            data = {"suggestions": []}

        out: List[Dict[str, Any]] = []
        for s in (data.get("suggestions") or []):
            out.append({
                "category": s.get("category", "maintainability"),
                "severity": s.get("severity", "info"),
                "title": (s.get("title") or "Refactor suggestion")[:200],
                "description": s.get("description", ""),
                "file_path": s.get("file_path"),
                "line_start": s.get("line_start"),
                "line_end": s.get("line_end"),
                "rule_id": "CG-REF",
                "recommendation": s.get("recommendation", ""),
                "extras": {"pattern": s.get("pattern")},
            })

        return AgentResult(
            agent_name=self.name,
            findings=out[:50],
            output={"total": len(out)},
            summary={"score": max(0.0, 100.0 - len(out) * 1.5), "total": len(out)},
            confidence=0.7,
        )
