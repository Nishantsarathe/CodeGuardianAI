"""
UML Agent — produces Mermaid diagrams for class, sequence, component
and dependency views.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List

from .base import AgentResult, BaseAgent


CLASS_RE_PY = re.compile(r"^class\s+(\w+)(?:\(([\w,\s]+)\))?\s*:", re.MULTILINE)
FN_RE_PY = re.compile(r"^\s+def\s+(\w+)\s*\((self)?", re.MULTILINE)
IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)


class UMLAgent(BaseAgent):
    name = "uml"

    async def run(self, payload: Dict[str, Any]) -> AgentResult:
        files = payload.get("files", [])
        class_diagram = self._class_diagram(files)
        component_diagram = self._component_diagram(files)
        sequence_diagram = self._sequence_diagram(files)
        dependency_diagram = self._dependency_diagram(files)
        architecture_diagram = self._architecture_diagram(files)

        out = {
            "class": class_diagram,
            "component": component_diagram,
            "sequence": sequence_diagram,
            "dependency": dependency_diagram,
            "architecture": architecture_diagram,
        }
        return AgentResult(
            agent_name=self.name,
            findings=[{
                "category": "uml", "severity": "info",
                "title": "UML diagrams generated",
                "description": "Mermaid diagrams ready to paste into any markdown renderer.",
                "file_path": "docs/diagrams.md",
                "rule_id": "CG-UML",
                "recommendation": "Render with mermaid-cli or paste into GitLab/GitHub markdown.",
                "extras": out,
            }],
            output=out,
            summary={"score": 90.0, "diagrams": list(out.keys())},
            confidence=0.9,
        )

    # ---------------- class diagram ----------------
    def _class_diagram(self, files: List[Dict[str, Any]]) -> str:
        classes = []
        for f in files:
            if f.get("language") != "python":
                continue
            content = f.get("content", "")
            for m in CLASS_RE_PY.finditer(content):
                name = m.group(1)
                parents = m.group(2) or ""
                methods = []
                for fn in FN_RE_PY.finditer(content):
                    methods.append(fn.group(1))
                classes.append((name, parents, methods[:8], f.get("path", "")))
        if not classes:
            return "```mermaid\nclassDiagram\n  note \"No Python classes found.\"\n```"
        lines = ["```mermaid", "classDiagram"]
        for name, parents, methods, _ in classes:
            lines.append(f"  class {name} {{")
            for m in methods:
                lines.append(f"    +{m}()")
            lines.append("  }")
        for name, parents, _, _ in classes:
            for p in [x.strip() for x in parents.split(",") if x.strip()]:
                lines.append(f"  {p} <|-- {name}")
        lines.append("```")
        return "\n".join(lines)

    # ---------------- component diagram ----------------
    def _component_diagram(self, files: List[Dict[str, Any]]) -> str:
        groups: Dict[str, List[str]] = defaultdict(list)
        for f in files:
            top = f.get("path", "").split("/", 1)[0] or "root"
            groups[top].append(f.get("path", ""))
        lines = ["```mermaid", "flowchart LR"]
        for g, paths in groups.items():
            label = f"{g} [{len(paths)} files]"
            lines.append(f"  subgraph {g}[/{g}]")
            for p in paths[:5]:
                lines.append(f"    {g}_{abs(hash(p)) % 10000}['{p}']")
            lines.append("  end")
        lines.append("```")
        return "\n".join(lines)

    # ---------------- sequence diagram ----------------
    def _sequence_diagram(self, files: List[Dict[str, Any]]) -> str:
        # Use the first file with route definitions for a sample sequence
        for f in files:
            content = f.get("content", "")
            if "@app." in content or "router." in content:
                lines = ["```mermaid", "sequenceDiagram",
                         "  participant Client", "  participant API",
                         "  participant Service", "  participant DB"]
                for kw in ("get", "post", "put", "delete"):
                    if f"@{kw}" in content or f"router.{kw}" in content:
                        lines.append(f"  Client->>API: HTTP {kw.upper()} /resource")
                        lines.append("  API->>Service: handle()")
                        lines.append("  Service->>DB: query()")
                        lines.append("  DB-->>Service: rows")
                        lines.append("  Service-->>API: result")
                        lines.append("  API-->>Client: 200 OK")
                        break
                lines.append("```")
                return "\n".join(lines)
        return "```mermaid\nsequenceDiagram\n  note \"No HTTP routes detected.\"\n```"

    # ---------------- dependency diagram ----------------
    def _dependency_diagram(self, files: List[Dict[str, Any]]) -> str:
        edges = set()
        for f in files:
            if f.get("language") != "python":
                continue
            content = f.get("content", "")
            for m in IMPORT_RE.finditer(content):
                mod = m.group(1) or m.group(2)
                if mod and "." not in mod.split(".")[0]:
                    edges.add((f.get("path", "root"), mod))
        if not edges:
            return "```mermaid\nflowchart LR\n  root --> none\n```"
        lines = ["```mermaid", "flowchart LR"]
        for src, dst in list(edges)[:80]:
            lines.append(f"  {src.replace('/', '_').replace('.', '_')[:30]} --> {dst}")
        lines.append("```")
        return "\n".join(lines)

    # ---------------- architecture diagram ----------------
    def _architecture_diagram(self, files: List[Dict[str, Any]]) -> str:
        return (
            "```mermaid\n"
            "flowchart TB\n"
            "  subgraph Frontend\n    UI[Next.js UI]\n  end\n"
            "  subgraph Backend\n    API[FastAPI]\n    Agents[AI Agents]\n  end\n"
            "  subgraph Data\n    DB[(SQLite)]\n    VDB[(ChromaDB)]\n  end\n"
            "  subgraph AI\n    LLM[Ollama LLM]\n  end\n"
            "  UI -->|REST| API\n"
            "  API --> Agents\n"
            "  API --> DB\n"
            "  Agents --> VDB\n"
            "  Agents --> LLM\n"
            "```"
        )
