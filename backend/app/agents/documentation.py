"""
Documentation Agent — generates README, API docs, architecture overview.

The output is stored in the analysis summary and surfaced through the
``/analyses/{id}`` endpoint and the report bundle.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


class DocumentationAgent(BaseAgent):
    name = "documentation"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        files = payload.get("files", [])
        project = {
            "name": os.path.basename(payload.get("workdir", "project")),
            "file_count": len(files),
            "languages": sorted({f.get("language") for f in files if f.get("language")}),
        }

        readme = await self._readme(project, files)
        api_doc = await self._api_doc(files)
        arch = await self._architecture(project, files)
        dev_guide = self._dev_guide(project, files)

        return AgentResult(
            agent_name=self.name,
            findings=[],
            output={
                "readme": readme,
                "api_doc": api_doc,
                "architecture": arch,
                "developer_guide": dev_guide,
            },
            summary={"score": self._score(files), "sections_generated": 4},
            confidence=0.75,
        )

    async def _readme(self, project: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        sample = self._truncate_files({"files": files}, max_files=4, max_chars=2200)
        prompt = (
            f"Generate a professional README.md for a project named '{project['name']}' with "
            f"languages {project['languages']} and {project['file_count']} files. Include: "
            "Overview, Features, Tech Stack, Installation, Usage, Folder Structure, Contributing, License. "
            "Output markdown only.\n\nSample files:\n" + self._format_files(sample)
        )
        try:
            return await self._llm(prompt, system="You are a senior developer-advocate who writes clean, concise READMEs.")
        except Exception:
            return self._default_readme(project)

    async def _api_doc(self, files: List[Dict[str, Any]]) -> str:
        # Look for obvious route / function definitions
        routes = []
        for f in files:
            content = f.get("content", "")
            path = f.get("path", "")
            for i, line in enumerate(content.splitlines(), start=1):
                line_stripped = line.strip()
                if line_stripped.startswith(("@app.route", "@router.", "app.get", "app.post",
                                              "router.get", "router.post", "router.put", "router.delete",
                                              "@app.get", "@app.post", "@app.put", "@app.delete")):
                    routes.append({"file": path, "line": i, "deco": line_stripped})
        if not routes:
            return "## API\n\n_No HTTP routes detected._"
        listing = "\n".join(f"- `{r['file']}:{r['line']}` — `{r['deco']}`" for r in routes[:100])
        return f"## API Endpoints\n\n{listing}\n\nTotal detected: {len(routes)}"

    async def _architecture(self, project: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        # Group files by top-level directory
        groups: Dict[str, int] = {}
        for f in files:
            top = f.get("path", "").split("/", 1)[0] or f.get("path", "").split("\\", 1)[0]
            groups[top] = groups.get(top, 0) + 1
        layers = "\n".join(f"- **{k}/** — {v} files" for k, v in sorted(groups.items()))
        return (
            f"## Architecture Overview\n\n**Project:** {project['name']}\n\n"
            f"**Languages:** {', '.join(project['languages']) or 'N/A'}\n\n"
            f"### Top-level layout\n\n{layers}\n\n"
            "### Suggested architecture style\n"
            "- Clean Architecture / Layered\n- Hexagonal (Ports & Adapters) for cross-cutting concerns\n- "
            "CQRS / Event-driven for high-throughput services."
        )

    def _dev_guide(self, project: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        return (
            "# Developer Guide\n\n"
            f"## Working with {project['name']}\n"
            "1. Install dependencies (see README).\n"
            "2. Run tests: `pytest -q`\n"
            "3. Format code: `ruff format .` and `ruff check --fix .`\n"
            "4. Lint: `mypy .`\n"
            "5. Commit messages follow Conventional Commits.\n"
        )

    def _default_readme(self, project: Dict[str, Any]) -> str:
        return (
            f"# {project['name']}\n\n"
            "## Overview\nProject analyzed by CodeGuardian AI.\n\n"
            f"## Languages\n{', '.join(project['languages']) or 'N/A'}\n"
        )

    def _score(self, files):
        # Reward more files / more languages up to a cap
        if not files:
            return 0.0
        return min(100.0, 50.0 + len(files) * 0.4)
