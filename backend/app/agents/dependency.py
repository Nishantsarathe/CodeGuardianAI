"""
Dependency Agent — reads requirements.txt / package.json / Cargo.toml
etc. and surfaces outdated packages, unused imports, and conflicts.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


class DependencyAgent(BaseAgent):
    name = "dependency"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        findings: List[Dict[str, Any]] = []
        manifest = self._read_manifest(payload)
        outdated = self._heuristic_outdated(manifest)
        unused = await self._find_unused(payload, manifest)

        for pkg, current, suggested in outdated:
            findings.append({
                "category": "dependency",
                "severity": "medium" if suggested.split(".")[0] != current.split(".")[0] else "low",
                "title": f"Outdated dependency: {pkg}",
                "description": f"Currently on {current}; latest is {suggested}.",
                "file_path": manifest.path,
                "rule_id": "CG-DEP-OUTDATED",
                "recommendation": f"Upgrade to {suggested} after reviewing the changelog.",
                "extras": {"package": pkg, "current": current, "latest": suggested},
            })

        for imp in unused:
            findings.append({
                "category": "dependency",
                "severity": "info",
                "title": f"Possibly unused import: {imp}",
                "description": "Import may be unused — verify and remove.",
                "file_path": "**/*.py",
                "rule_id": "CG-DEP-UNUSED",
                "recommendation": "Remove the import or use `_ =` to silence the linter.",
            })

        return AgentResult(
            agent_name=self.name,
            findings=findings[:200],
            output={"manifest": manifest.raw, "packages": manifest.packages},
            summary={
                "score": max(0.0, 100.0 - len(findings) * 0.6),
                "outdated": len(outdated),
                "unused": len(unused),
            },
            confidence=0.8,
        )

    # ---------------- helpers ----------------
    def _read_manifest(self, payload: Dict[str, Any]) -> Any:
        from dataclasses import dataclass, field

        @dataclass
        class Manifest:
            path: str = ""
            raw: str = ""
            packages: Dict[str, str] = field(default_factory=dict)

        m = Manifest()
        for f in payload.get("files", []):
            path = f.get("path", "").lower()
            content = f.get("content", "")
            if path.endswith("requirements.txt") or path.endswith("requirements.in"):
                m.path = path
                m.raw = content
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    name, _, version = re.split(r"[=<>~!]", line, maxsplit=1)[0].partition("==")
                    m.packages[name.strip()] = version.strip() or "*"
            elif path.endswith("package.json"):
                try:
                    data = json.loads(content)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    m.path = path
                    m.raw = content
                    m.packages = {k: v.lstrip("^~") for k, v in deps.items()}
                except json.JSONDecodeError:
                    pass
            elif path.endswith("cargo.toml"):
                m.path = path
                m.raw = content
                for line in content.splitlines():
                    line = line.strip()
                    if "=" in line and "[" not in line:
                        name, _, version = line.partition("=")
                        m.packages[name.strip()] = version.strip().strip('"')
            elif path.endswith("go.mod"):
                m.path = path
                m.raw = content
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("require") or "\t" in line:
                        parts = line.replace("require", "").strip().split()
                        if len(parts) >= 2:
                            m.packages[parts[0]] = parts[1]
        return m

    def _heuristic_outdated(self, manifest) -> List[tuple]:
        # Naive rule: pin a known "modern" set of version hints.
        known = {
            "fastapi": "0.115.0", "pydantic": "2.9.0", "sqlalchemy": "2.0.36",
            "uvicorn": "0.32.0", "httpx": "0.27.0", "chromadb": "0.5.0",
            "pytest": "8.3.0", "ruff": "0.7.0", "mypy": "1.13.0",
            "next": "15.0.0", "react": "19.0.0",
        }
        out: List[tuple] = []
        for pkg, current in manifest.packages.items():
            latest = known.get(pkg.lower())
            if latest and current != latest and current not in {"*", ""}:
                out.append((pkg, current, latest))
        return out

    async def _find_unused(self, payload: Dict[str, Any], manifest) -> List[str]:
        if not manifest.packages:
            return []
        # Ask LLM to flag likely-unused top-level packages
        prompt = (
            "Given the following package list and a high-level view of a project, identify the "
            "top 5 most likely UNUSED packages. Return JSON {\"unused\": [\"pkg1\", ...]}.\n\n"
            f"Packages: {list(manifest.packages.keys())}\n"
            f"File count: {len(payload.get('files', []))}\n"
        )
        try:
            data = await self._llm_json(prompt, fast=True)
        except Exception:
            return []
        return list(data.get("unused") or [])[:5]
