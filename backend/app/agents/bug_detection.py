"""
Bug Detection Agent — finds runtime, logic and performance issues.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


PATTERNS: List[Dict[str, Any]] = [
    {
        "title": "Potential None dereference",
        "regex": r"(\w+)\.(\w+)\s*=\s*\1\.\w+\s*\n\s*if\s+\1\.\w+",
        "category": "logic", "severity": "medium",
        "description": "Object may be null when accessed; suggest a null-check.",
        "rec": "Add a guard clause or refactor to Optional[T].",
    },
    {
        "title": "Bare except clause",
        "regex": r"except\s*:\s*$",
        "category": "error-handling", "severity": "high",
        "description": "Bare `except:` swallows all errors including SystemExit.",
        "rec": "Catch `Exception` or a specific exception type.",
    },
    {
        "title": "Possible infinite loop",
        "regex": r"while\s+True\s*:\s*(?!.*(?:break|return|raise|sys\.exit))",
        "category": "control-flow", "severity": "high",
        "description": "`while True` without a clear exit condition.",
        "rec": "Add an explicit break / return condition.",
    },
    {
        "title": "Use of eval / exec",
        "regex": r"\beval\s*\(|\bexec\s*\(",
        "category": "dangerous-call", "severity": "critical",
        "description": "Use of eval/exec is dangerous and often unnecessary.",
        "rec": "Replace with a safe parser (ast.literal_eval, json, etc.).",
    },
    {
        "title": "Mutable default argument",
        "regex": r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))",
        "category": "logic", "severity": "high",
        "description": "Mutable default arguments are shared across calls.",
        "rec": "Use `None` sentinel and create inside the function body.",
    },
    {
        "title": "Unused variable (heuristic)",
        "regex": r"^\s*([a-z_]\w*)\s*=\s*[^=].*$",
        "category": "dead-code", "severity": "info",
        "description": "Variable assigned but may not be used.",
        "rec": "Remove the assignment or use `_var` to mark intentionally unused.",
    },
    {
        "title": "Print debugging",
        "regex": r"\bprint\s*\(",
        "category": "performance", "severity": "low",
        "description": "Leftover print() call (likely debug output).",
        "rec": "Replace with the project's structured logger.",
    },
    {
        "title": "Time.sleep in async context",
        "regex": r"async\s+def\s+\w+[^)]*:[^#\n]*\n[^#\n]*time\.sleep",
        "category": "performance", "severity": "medium",
        "description": "Blocking sleep inside async function freezes the event loop.",
        "rec": "Use `await asyncio.sleep(...)` instead.",
    },
    {
        "title": "Missing await",
        "regex": r"^\s*[A-Za-z_]\w*\s*=\s*(?!await\b)(fetch|get|post|request|query|save|update|delete)\w*\(",
        "category": "async", "severity": "high",
        "description": "Possible missing `await` on a coroutine.",
        "rec": "Add `await` if the function returns a coroutine.",
    },
    {
        "title": "Resource leak risk",
        "regex": r"open\s*\([^)]*\)(?!\s*as\s+\w+:|\s*$)",
        "category": "resource", "severity": "medium",
        "description": "File opened without a `with` statement.",
        "rec": "Use a `with` block to ensure the file is closed.",
    },
]


class BugDetectionAgent(BaseAgent):
    name = "bug"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        findings: List[Dict[str, Any]] = []
        for f in payload.get("files", []):
            content = f.get("content", "")
            path = f.get("path", "")
            lang = f.get("language", "")
            for i, line in enumerate(content.splitlines(), start=1):
                for pat in PATTERNS:
                    if re.search(pat["regex"], line):
                        findings.append({
                            "category": pat["category"],
                            "severity": pat["severity"],
                            "title": pat["title"],
                            "description": pat["description"],
                            "file_path": path,
                            "line_start": i, "line_end": i,
                            "rule_id": f"CG-BUG-{pat['title'][:6].upper()}",
                            "recommendation": pat["rec"],
                            "code_snippet": line[:300],
                        })

        # LLM pass for context-rich bug hunt
        llm_findings = await self._llm_bug_pass(payload)
        findings.extend(llm_findings)

        score = self._score(findings)
        return AgentResult(
            agent_name=self.name,
            findings=findings[:200],
            output={"total": len(findings)},
            summary={"score": score, "total": len(findings),
                     "critical_count": sum(1 for x in findings if x["severity"] == "critical"),
                     "high_count": sum(1 for x in findings if x["severity"] == "high")},
            confidence=0.78,
        )

    async def _llm_bug_pass(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        files = self._truncate_files(payload, max_files=3, max_chars=800)
        if not files:
            return []
        prompt = (
            "You are a bug-hunting expert. Look for logic errors, race conditions, null-deref "
            "issues, infinite loops, performance bottlenecks and unused variables. Return JSON "
            "{\"findings\":[...]} with keys title, severity (info|low|medium|high|critical), "
            "description, file_path, line_start, line_end, recommendation.\n\n"
            f"Files:\n{self._format_files(files)}"
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        for f in (data.get("findings") or []):
            out.append({
                "category": "logic", "severity": f.get("severity", "info"),
                "title": (f.get("title") or "Bug")[:200],
                "description": f.get("description", ""),
                "file_path": f.get("file_path"),
                "line_start": f.get("line_start"),
                "line_end": f.get("line_end"),
                "rule_id": "CG-BUG-LLM",
                "recommendation": f.get("recommendation", ""),
            })
        return out

    def _score(self, findings):
        weights = {"critical": 12, "high": 6, "medium": 2, "low": 0.4, "info": 0.1}
        return max(0.0, round(100.0 - sum(weights.get(f["severity"], 0) for f in findings), 2))
