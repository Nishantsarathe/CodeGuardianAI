"""
Security Agent — OWASP-aligned vulnerability detection.

Strategy: exhaustive regex scan over ALL files (fast, zero LLM cost),
then a single batched LLM call over the 3 most interesting files only.
This replaces the old per-file LLM loop which was the #1 latency source.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


CWE_RISK = {
    "CWE-89": 9.8, "CWE-79": 7.5, "CWE-78": 9.4, "CWE-22": 8.0,
    "CWE-798": 9.0, "CWE-287": 8.5, "CWE-434": 8.0, "CWE-94": 9.5,
    "CWE-611": 7.0, "CWE-918": 9.0, "CWE-502": 8.5, "CWE-601": 6.5,
    "CWE-327": 6.0,
}

SKIP_EXTENSIONS = {".min.js", ".lock", ".map", ".svg", ".png", ".jpg"}


class SecurityAgent(BaseAgent):
    name = "security"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        findings: List[Dict[str, Any]] = []

        # --- Phase 1: full regex scan (all files, no LLM) ---
        for f in payload.get("files", []):
            path = f.get("path", "")
            if any(path.endswith(ext) for ext in SKIP_EXTENSIONS):
                continue
            findings += self._regex_scan(f.get("content", ""), path, f.get("language", ""))

        # --- Phase 2: single LLM call on top 3 files only ---
        llm_findings = await self._llm_batch(payload)
        findings.extend(llm_findings)

        # Assign severity from CVSS
        for f in findings:
            if f.get("cvss_score") is None:
                f["cvss_score"] = CWE_RISK.get(f.get("cwe_id") or "", 5.0)
            f["severity"] = self._sev(f["cvss_score"])

        score = self._score(findings)
        counts = {s: sum(1 for f in findings if f.get("severity") == s)
                  for s in ("critical", "high", "medium", "low")}
        return AgentResult(
            agent_name=self.name,
            findings=findings[:200],
            output={"total": len(findings)},
            summary={"score": score, "total": len(findings),
                     **{f"{k}_count": v for k, v in counts.items()}},
            confidence=0.85,
        )

    # ------------------------------------------------------------------
    def _regex_scan(self, content: str, path: str, lang: str) -> List[Dict]:
        out: List[Dict] = []
        for i, line in enumerate(content.splitlines(), 1):
            # SQL injection
            if re.search(r"(execute|raw|query|exec)\s*\(\s*[\"'].*?\+", line) and "select" in line.lower():
                out.append(self._mk("SQL injection", "CWE-89", line, path, i, "Use parameterized queries."))
            # XSS
            if lang in {"javascript", "typescript"}:
                if re.search(r"\.innerHTML\s*=", line):
                    out.append(self._mk("XSS via innerHTML", "CWE-79", line, path, i, "Use textContent or DOMPurify."))
                if re.search(r"document\.write\s*\(", line):
                    out.append(self._mk("XSS via document.write", "CWE-79", line, path, i, "Use safe DOM APIs."))
            # Command injection
            if re.search(r"(os\.system|subprocess\.call|child_process\.exec|exec\s*\(|Runtime\.getRuntime\(\)\.exec)", line):
                if re.search(r"\+|format|concat|\${", line):
                    out.append(self._mk("Command injection", "CWE-78", line, path, i, "Use argv lists, avoid shell=True."))
            # Path traversal
            if re.search(r"open\s*\([^)]*\+|os\.path\.join\([^)]*request\.", line):
                out.append(self._mk("Path traversal", "CWE-22", line, path, i, "Resolve and validate paths against a whitelist."))
            # Hardcoded secret
            m = re.search(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-./+=]{8,}['\"]", line)
            if m and "example" not in line.lower() and "change_me" not in line.lower():
                out.append(self._mk("Hardcoded secret", "CWE-798", line, path, i, "Move to env vars / secret manager."))
            # Weak hash
            if re.search(r"(?i)(md5|sha1)\s*\(", line):
                out.append(self._mk("Weak hash algorithm", "CWE-327", line, path, i, "Use SHA-256+ or bcrypt for passwords."))
            # Unsafe deserialisation
            if re.search(r"yaml\.load\s*\(|pickle\.loads?\s*\(", line):
                out.append(self._mk("Unsafe deserialization", "CWE-502", line, path, i, "Use yaml.safe_load or json."))
            # Open redirect
            if re.search(r"redirect\s*\(.*request\.|sendRedirect\s*\(.*request\.", line):
                out.append(self._mk("Open redirect", "CWE-601", line, path, i, "Whitelist redirect targets."))
        return out

    async def _llm_batch(self, payload: Dict[str, Any]) -> List[Dict]:
        """ONE LLM call covering at most 3 files, 800 chars each."""
        files = self._truncate_files(payload, max_files=3, max_chars=800)
        if not files:
            return []
        prompt = (
            "Security analyst: identify vulnerabilities in these files. "
            "Reply JSON {\"findings\":[{title,severity,cwe_id,description,file_path,line_start,recommendation}]}. "
            "Only real issues, no hallucinations.\n\n" + self._format_files(files)
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            return []
        out: List[Dict] = []
        for f in (data.get("findings") or [])[:20]:
            cwe = f.get("cwe_id")
            out.append({
                "category": "security", "severity": f.get("severity", "info"),
                "title": (f.get("title") or "Security issue")[:200],
                "description": f.get("description", ""),
                "file_path": f.get("file_path"), "line_start": f.get("line_start"),
                "rule_id": f"CG-SEC-{cwe or 'LLM'}", "cwe_id": cwe,
                "cvss_score": CWE_RISK.get(cwe or "", 5.0),
                "recommendation": f.get("recommendation", ""),
            })
        return out

    def _mk(self, title, cwe, line, path, lineno, rec) -> Dict:
        return {
            "category": "security", "title": title, "cwe_id": cwe,
            "cvss_score": CWE_RISK.get(cwe, 5.0), "severity": "info",
            "description": f"{title} detected.", "file_path": path,
            "line_start": lineno, "line_end": lineno,
            "rule_id": f"CG-SEC-{cwe}",
            "recommendation": rec, "code_snippet": line[:300],
        }

    def _sev(self, cvss: float) -> str:
        if cvss >= 9.0: return "critical"
        if cvss >= 7.0: return "high"
        if cvss >= 4.0: return "medium"
        if cvss > 0:    return "low"
        return "info"

    def _score(self, findings: List[Dict]) -> float:
        w = {"critical": 18, "high": 8, "medium": 3, "low": 0.5, "info": 0.1}
        return max(0.0, round(100.0 - sum(w.get(f.get("severity","info"), 0) for f in findings), 2))
