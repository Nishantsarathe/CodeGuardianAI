"""
Auto-Fix Agent — generates unified-diff patches for top issues.

Strategy:
  • Collect high/critical findings from the same analysis (we re-run
    heuristics here to keep the agent self-contained for tests).
  • Ask the LLM to propose a minimal patch for each file with fixes.
  • Bundle the patches into a single diff and surface it both as an
    artifact and as a list of finding-level "fix recommendations".
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import AgentResult, BaseAgent
from .security import SecurityAgent
from .bug_detection import BugDetectionAgent


class AutoFixAgent(BaseAgent):
    name = "auto_fix"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        # Reuse heuristics for self-contained analysis
        sec = SecurityAgent()
        bug = BugDetectionAgent()
        sec_findings = []
        bug_findings = []
        for f in payload.get("files", []):
            sec_findings += sec._regex_scan(f.get("content", ""), f.get("path", ""), f.get("language", ""))
            for i, line in enumerate(f.get("content", "").splitlines(), start=1):
                from .bug_detection import PATTERNS
                import re
                for pat in PATTERNS:
                    if re.search(pat["regex"], line):
                        bug_findings.append({
                            **pat, "file_path": f.get("path", ""),
                            "line_start": i, "line_end": i,
                            "code_snippet": line[:300],
                        })
        high = [x for x in sec_findings + bug_findings if x.get("severity") in {"high", "critical"}][:8]

        patches: List[Dict[str, Any]] = []
        for issue in high:
            patch = await self._propose_patch(payload, issue)
            if patch:
                patches.append(patch)

        return AgentResult(
            agent_name=self.name,
            findings=[
                {
                    "category": "auto-fix", "severity": "info",
                    "title": f"Auto-fix proposed for {issue['title']}",
                    "description": issue.get("description", ""),
                    "file_path": issue.get("file_path"),
                    "line_start": issue.get("line_start"),
                    "line_end": issue.get("line_end"),
                    "rule_id": "CG-FIX",
                    "recommendation": (patch or {}).get("description", ""),
                    "extras": {"diff": (patch or {}).get("diff", "")},
                }
                for issue, patch in zip(high, patches)
            ],
            output={"patches": [p["diff"] for p in patches]},
            summary={"score": 90.0 if patches else 70.0, "patches_generated": len(patches)},
            confidence=0.7,
        )

    async def _propose_patch(self, payload: Dict[str, Any], issue: Dict[str, Any]) -> Dict[str, Any] | None:
        path = issue.get("file_path")
        if not path:
            return None
        target = next((f for f in payload.get("files", []) if f["path"] == path), None)
        if not target:
            return None
        prompt = (
            "Propose a minimal, safe unified-diff patch to fix this issue. The patch must "
            "apply cleanly to the original file below. Output JSON with `diff` and `description`.\n\n"
            f"File: {path}\nIssue: {issue['title']}\n"
            f"Recommendation: {issue.get('recommendation','')}\n\n"
            f"Original file (first 4000 chars):\n```\n{target['content'][:4000]}\n```"
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            return None
        diff = (data or {}).get("diff") or ""
        if not diff or "+++" not in diff or "---" not in diff:
            return {"diff": "", "description": (data or {}).get("description", "")}
        return {"diff": diff, "description": (data or {}).get("description", "")}
