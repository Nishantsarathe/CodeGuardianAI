"""
Code Review Agent — quality, complexity, smells, duplication.

Combines lightweight static heuristics with an LLM pass that produces
structured findings. The agent returns a final ``code_quality_score``
in its summary.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent, extract_json_blob, safe_text


# Heuristic rules per language
LONG_LINE = 200
LONG_FUNCTION = 60
DEEP_NESTING = 5


class CodeReviewAgent(BaseAgent):
    name = "code_review"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        files = payload.get("files", [])
        findings: List[Dict[str, Any]] = []
        smells = Counter()
        stats = {"total_lines": 0, "total_functions": 0, "total_classes": 0}

        for f in files:
            content = f.get("content", "")
            path = f.get("path", "")
            lang = f.get("language", "")
            stats["total_lines"] += content.count("\n")
            stats["total_functions"] += self._count_functions(content, lang)
            stats["total_classes"] += self._count_classes(content, lang)

            # Long lines
            for i, line in enumerate(content.splitlines(), start=1):
                if len(line) > LONG_LINE:
                    findings.append(self._mk_finding(
                        category="style", severity="info", title="Line too long",
                        description=f"Line exceeds {LONG_LINE} characters ({len(line)}).",
                        path=path, line_start=i, line_end=i,
                        recommendation=f"Wrap the line or refactor into a helper. "
                                       f"CodeGuardian suggests a max of 100-120 chars.",
                    ))

            # Long functions
            for fn_start, fn_end, name in self._function_spans(content, lang):
                if (fn_end - fn_start) > LONG_FUNCTION:
                    findings.append(self._mk_finding(
                        category="complexity", severity="medium",
                        title=f"Function '{name}' is too long",
                        description=f"Function spans ~{fn_end - fn_start} lines.",
                        path=path, line_start=fn_start, line_end=fn_end,
                        recommendation="Split into smaller helpers following SRP. "
                                       "Extract branches into private methods.",
                    ))

            # Deep nesting
            for i, line in enumerate(content.splitlines(), start=1):
                indent = len(line) - len(line.lstrip())
                if indent > DEEP_NESTING * 4:
                    findings.append(self._mk_finding(
                        category="complexity", severity="medium",
                        title="Deeply nested block",
                        description=f"Indentation suggests nesting depth > {DEEP_NESTING}.",
                        path=path, line_start=i, line_end=i,
                        recommendation="Use guard clauses, polymorphism or strategy pattern.",
                    ))

            # Duplicated code is approximated by repeated literal blocks
            seen = Counter()
            for chunk in self._chunks(content, 5):
                seen[chunk] += 1
            for chunk, n in seen.items():
                if n > 2 and len(chunk) > 100:
                    smells["duplicated_block"] += 1

            # TODO/FIXME/XXX smell
            for i, line in enumerate(content.splitlines(), start=1):
                m = re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line)
                if m:
                    findings.append(self._mk_finding(
                        category="smell", severity="low",
                        title=f"Tracked comment: {m.group(0)}",
                        description=line.strip()[:200],
                        path=path, line_start=i, line_end=i,
                        recommendation="Convert into a tracked ticket or remove.",
                    ))

        smells_summary = dict(smells)

        # LLM pass on a digest for higher-signal findings
        llm_findings = await self._llm_pass(files)
        findings.extend(llm_findings)

        score = self._score(findings, smells_summary)
        return AgentResult(
            agent_name=self.name,
            findings=findings[:200],
            output={"stats": stats, "smells": smells_summary},
            summary={
                "score": score,
                "findings": len(findings),
                "critical_count": sum(1 for f in findings if f["severity"] == "critical"),
                "high_count": sum(1 for f in findings if f["severity"] == "high"),
                "medium_count": sum(1 for f in findings if f["severity"] == "medium"),
                "low_count": sum(1 for f in findings if f["severity"] == "low"),
            },
            confidence=0.82,
        )

    # ---------------- helpers ----------------
    def _mk_finding(self, *, category, severity, title, description, path,
                    line_start=None, line_end=None, recommendation=None,
                    extras=None) -> Dict[str, Any]:
        return {
            "category": category, "severity": severity, "title": title,
            "description": description, "file_path": path,
            "line_start": line_start, "line_end": line_end,
            "rule_id": f"CG-CR-{category}",
            "recommendation": recommendation, "extras": extras or {},
        }

    def _function_spans(self, content: str, lang: str):
        if lang in {"python"}:
            return self._py_functions(content)
        if lang in {"javascript", "typescript"}:
            return self._brace_functions(content)
        if lang in {"java", "go", "rust", "cpp", "c", "csharp"}:
            return self._brace_functions(content)
        return []

    def _py_functions(self, content: str):
        lines = content.splitlines()
        spans = []
        for i, line in enumerate(lines, start=1):
            if re.match(r"^(\s*)def\s+([A-Za-z_][\w]*)\s*\(", line):
                indent = len(line) - len(line.lstrip())
                end = i
                for j in range(i, len(lines)):
                    if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent and not lines[j].lstrip().startswith(("#", "\"\"\"")):
                        end = j
                        break
                else:
                    end = len(lines)
                spans.append((i, end, re.search(r"def\s+([\w]+)", line).group(1)))
        return spans

    def _brace_functions(self, content: str):
        out = []
        depth = 0
        start = None
        name = None
        for i, line in enumerate(content.splitlines(), start=1):
            for ch in line:
                if ch == "{":
                    if depth == 0 and start is None:
                        start = i
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0 and start is not None:
                        out.append((start, i, name or "block"))
                        start = None
                        name = None
            # Heuristic name detection on the line that started the block
            if start == i:
                m = re.search(r"function\s+(\w+)|(\w+)\s*\(.*\)\s*\{|fn\s+(\w+)", line)
                if m:
                    name = next((g for g in m.groups() if g), "block")
        return out

    def _count_functions(self, content: str, lang: str) -> int:
        return len(self._function_spans(content, lang))

    def _count_classes(self, content: str, lang: str) -> int:
        if lang == "python":
            return len(re.findall(r"^class\s+[A-Z]\w*", content, re.MULTILINE))
        return len(re.findall(r"\b(class|struct|interface)\s+[A-Z]\w*", content))

    def _chunks(self, content: str, n: int):
        lines = content.splitlines()
        for i in range(len(lines) - n):
            yield "\n".join(lines[i : i + n])

    async def _llm_pass(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not files:
            return []
        # Only pass a digest to keep token usage low
        sample = self._truncate_files({"files": files}, max_files=3, max_chars=800)
        prompt = (
            "You are a Staff-Engineer code reviewer. Analyse the following source files and "
            "return JSON of the form {\"findings\": [...]}. Each finding must have keys: "
            "title, severity (info|low|medium|high|critical), category (style|smell|complexity|perf|readability), "
            "description, file_path, line_start, line_end, recommendation. Be concise, "
            "focus on real issues, never invent line numbers.\n\n"
            f"Files:\n{self._format_files(sample)}"
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        for f in (data.get("findings") or []):
            out.append({
                "category": f.get("category", "general"),
                "severity": f.get("severity", "info"),
                "title": (f.get("title") or "Issue")[:200],
                "description": f.get("description", ""),
                "file_path": f.get("file_path"),
                "line_start": f.get("line_start"),
                "line_end": f.get("line_end"),
                "rule_id": "CG-CR-LLM",
                "recommendation": f.get("recommendation", ""),
            })
        return out

    def _score(self, findings: List[Dict[str, Any]], smells: Dict[str, int]) -> float:
        weights = {"critical": 12, "high": 6, "medium": 2, "low": 0.5, "info": 0.1}
        penalty = sum(weights.get(f["severity"], 0) for f in findings)
        penalty += smells.get("duplicated_block", 0) * 3
        return max(0.0, round(100.0 - penalty, 2))
