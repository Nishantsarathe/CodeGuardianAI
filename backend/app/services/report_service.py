"""
Report generation service.

Produces Markdown, HTML, PDF, and unified-patch outputs from a stored
analysis. Pure functions — no global state — so they're easy to test.
"""
from __future__ import annotations

import io
import json
import re
import textwrap
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.core.constants import SEVERITY_COLORS, SEVERITY_ORDER
from app.core.logging import get_logger
from app.db.models import Analysis, Finding, Project, Severity


logger = get_logger("codeguardian.reports")


# --------------------- JSON payload ---------------------
def build_json_payload(db: Session, analysis: Analysis) -> Dict:
    project = db.query(Project).filter(Project.id == analysis.project_id).first()
    return {
        "id": analysis.id,
        "project": {
            "id": project.id if project else None,
            "name": project.name if project else None,
            "language": project.language if project else None,
        },
        "status": analysis.status.value if hasattr(analysis.status, "value") else analysis.status,
        "health_score": analysis.health_score,
        "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
        "finished_at": analysis.finished_at.isoformat() if analysis.finished_at else None,
        "duration_ms": analysis.duration_ms,
        "summary": analysis.summary,
        "agent_runs": [
            {
                "id": r.id, "agent": r.agent_name,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
                "duration_ms": r.duration_ms,
                "confidence": r.confidence,
                "error": r.error,
            }
            for r in (analysis.agent_runs or [])
        ],
        "findings": [
            {
                "id": f.id, "agent": f.agent_name, "category": f.category,
                "severity": f.severity.value if hasattr(f.severity, "value") else f.severity,
                "title": f.title, "description": f.description,
                "file_path": f.file_path, "line_start": f.line_start, "line_end": f.line_end,
                "rule_id": f.rule_id, "cvss_score": f.cvss_score, "cwe_id": f.cwe_id,
                "recommendation": f.recommendation, "code_snippet": f.code_snippet,
            }
            for f in (analysis.findings or [])
        ],
    }


# --------------------- Markdown ---------------------
def build_markdown_report(db: Session, analysis: Analysis) -> str:
    payload = build_json_payload(db, analysis)
    project = payload["project"]
    findings = payload["findings"]
    sev_counts = Counter(f["severity"] for f in findings)
    lines: List[str] = []
    lines.append(f"# 🛡️ CodeGuardian AI — Analysis Report")
    lines.append("")
    lines.append(f"**Project:** {project.get('name')}  ")
    lines.append(f"**Project ID:** `{project.get('id')}`  ")
    lines.append(f"**Language:** {project.get('language') or 'N/A'}  ")
    lines.append(f"**Status:** {payload['status']}  ")
    lines.append(f"**Health score:** {payload['health_score']} / 100  ")
    lines.append(f"**Generated:** {datetime.utcnow().isoformat(timespec='seconds')}Z  ")
    lines.append("")
    lines.append("## 📊 Severity distribution")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for s in SEVERITY_ORDER:
        lines.append(f"| {s} | {sev_counts.get(s, 0)} |")
    lines.append("")
    lines.append(f"**Total findings:** {len(findings)}")
    lines.append("")
    if payload["summary"]:
        lines.append("## 🤖 Agent runs")
        lines.append("")
        lines.append("| Agent | Status | Duration (ms) | Confidence |")
        lines.append("|-------|--------|---------------|-----------|")
        for r in payload["agent_runs"]:
            lines.append(f"| {r['agent']} | {r['status']} | {r.get('duration_ms') or 0} | {r.get('confidence') or 0:.2f} |")
        lines.append("")

    if findings:
        lines.append("## 🔍 Findings")
        for i, f in enumerate(findings, start=1):
            lines.append(f"### {i}. {f['title']}")
            lines.append(f"- **Severity:** {f['severity']}")
            lines.append(f"- **Agent:** {f['agent']}")
            if f.get("category"):
                lines.append(f"- **Category:** {f['category']}")
            if f.get("file_path"):
                lines.append(f"- **Location:** `{f['file_path']}` (lines {f.get('line_start') or '?'}-{f.get('line_end') or '?'})")
            if f.get("rule_id"):
                lines.append(f"- **Rule:** `{f['rule_id']}`")
            if f.get("cvss_score") is not None:
                lines.append(f"- **CVSS:** {f['cvss_score']}")
            if f.get("cwe_id"):
                lines.append(f"- **CWE:** {f['cwe_id']}")
            lines.append("")
            if f.get("description"):
                lines.append(f"{f['description']}")
                lines.append("")
            if f.get("code_snippet"):
                lines.append("```")
                lines.append(f["code_snippet"])
                lines.append("```")
                lines.append("")
            if f.get("recommendation"):
                lines.append(f"**Recommendation:** {f['recommendation']}")
                lines.append("")

    lines.append("---")
    lines.append("_Generated by CodeGuardian AI — Autonomous Multi-Agent Code Review & Security Platform._")
    return "\n".join(lines)


# --------------------- HTML ---------------------
def build_html_report(db: Session, analysis: Analysis) -> str:
    payload = build_json_payload(db, analysis)
    project = payload["project"]
    findings = payload["findings"]
    sev_counts = Counter(f["severity"] for f in findings)
    sev_cells = "".join(
        f'<div class="sev sev-{s}"><div class="dot" style="background:{SEVERITY_COLORS[s]}"></div>'
        f'<div class="label">{s}</div><div class="count">{sev_counts.get(s, 0)}</div></div>'
        for s in SEVERITY_ORDER
    )
    findings_html = "".join(
        _finding_html(f) for f in findings
    ) or '<div class="empty">No findings 🎉 — looking great!</div>'

    agent_rows = "".join(
        f"<tr><td>{r['agent']}</td><td>{r['status']}</td>"
        f"<td>{r.get('duration_ms') or 0}</td>"
        f"<td>{(r.get('confidence') or 0):.2f}</td></tr>"
        for r in payload["agent_runs"]
    )

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>CodeGuardian AI — Report {analysis.id}</title>
<style>
:root {{
  --bg: #0b0f1a; --card: #111a2c; --border: #1f2a44;
  --text: #e6edf3; --muted: #8a93a6; --accent: #7c3aed;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, "Segoe UI", Inter, Roboto, sans-serif;
  background: linear-gradient(180deg, #0b0f1a 0%, #0d1426 100%); color: var(--text); }}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 48px 24px; }}
.hero {{ display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }}
.hero .logo {{ width: 48px; height: 48px; border-radius: 12px;
  background: linear-gradient(135deg, #7c3aed, #06b6d4); display: grid; place-items: center;
  font-size: 24px; }}
h1 {{ font-size: 28px; margin: 0; }}
.sub {{ color: var(--muted); margin-top: 4px; }}
.card {{ background: var(--card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin: 16px 0; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
.kv {{ display: flex; flex-direction: column; gap: 4px; }}
.kv .k {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
.kv .v {{ font-size: 18px; font-weight: 600; }}
.sev {{ display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: #0d1426;
  border: 1px solid var(--border); border-radius: 12px; }}
.sev .dot {{ width: 10px; height: 10px; border-radius: 50%; }}
.sev .label {{ color: var(--muted); text-transform: capitalize; }}
.sev .count {{ margin-left: auto; font-weight: 700; font-size: 20px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th, td {{ text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--border); }}
th {{ color: var(--muted); font-weight: 500; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; }}
.finding {{ padding: 18px 0; border-bottom: 1px solid var(--border); }}
.finding:last-child {{ border-bottom: none; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }}
.tag-info {{ background: rgba(59,130,246,0.15); color: #60a5fa; }}
.tag-low {{ background: rgba(34,197,94,0.15); color: #4ade80; }}
.tag-medium {{ background: rgba(234,179,8,0.15); color: #facc15; }}
.tag-high {{ background: rgba(249,115,22,0.15); color: #fb923c; }}
.tag-critical {{ background: rgba(239,68,68,0.15); color: #f87171; }}
pre {{ background: #060912; border: 1px solid var(--border); border-radius: 12px; padding: 16px; overflow-x: auto; }}
code {{ font-family: "JetBrains Mono", "Fira Code", monospace; font-size: 13px; }}
.empty {{ padding: 40px; text-align: center; color: var(--muted); }}
</style></head>
<body><div class="wrap">
  <div class="hero">
    <div class="logo">🛡️</div>
    <div>
      <h1>CodeGuardian AI</h1>
      <div class="sub">Autonomous Multi-Agent Code Review & Security Platform</div>
    </div>
  </div>

  <div class="card">
    <div class="grid">
      <div class="kv"><div class="k">Project</div><div class="v">{project.get('name')}</div></div>
      <div class="kv"><div class="k">Language</div><div class="v">{project.get('language') or '—'}</div></div>
      <div class="kv"><div class="k">Status</div><div class="v">{payload['status']}</div></div>
      <div class="kv"><div class="k">Health score</div><div class="v">{payload['health_score']} / 100</div></div>
      <div class="kv"><div class="k">Generated</div><div class="v">{datetime.utcnow().isoformat(timespec='seconds')}Z</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Severity distribution</h2>
    <div class="grid">{sev_cells}</div>
  </div>

  <div class="card">
    <h2>Agent runs</h2>
    <table><thead><tr><th>Agent</th><th>Status</th><th>Duration (ms)</th><th>Confidence</th></tr></thead>
      <tbody>{agent_rows}</tbody></table>
  </div>

  <div class="card">
    <h2>Findings ({len(findings)})</h2>
    {findings_html}
  </div>
</div></body></html>
"""


def _finding_html(f: dict) -> str:
    sev = f.get("severity", "info")
    snippet = f.get("code_snippet") or ""
    return f"""
<div class="finding">
  <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px;">
    <span class="tag tag-{sev}">{sev}</span>
    <strong>{f.get('title','')}</strong>
  </div>
  <div style="color:var(--muted);font-size:13px;margin-bottom:8px;">
    {f.get('agent','')} · {f.get('category','')}
    {f" · <code>{f.get('file_path')}:{f.get('line_start') or '?'}</code>" if f.get('file_path') else ''}
    {f" · CWE {f.get('cwe_id')}" if f.get('cwe_id') else ''}
  </div>
  <div>{f.get('description','')}</div>
  {f"<pre><code>{_escape_html(snippet)}</code></pre>" if snippet else ''}
  {f"<div><strong>Recommendation:</strong> {f.get('recommendation','')}</div>" if f.get('recommendation') else ''}
</div>
"""


def _escape_html(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# --------------------- PDF ---------------------
def build_pdf_report(db: Session, analysis: Analysis) -> bytes:
    """Generate a PDF using ReportLab, or fall back to a simple text PDF."""
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=LETTER, title="CodeGuardian AI Report")
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("🛡️ CodeGuardian AI — Analysis Report", styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))
        payload = build_json_payload(db, analysis)
        project = payload["project"]
        info_table = Table([
            ["Project", project.get("name") or ""],
            ["Language", project.get("language") or "—"],
            ["Status", payload["status"]],
            ["Health score", f"{payload['health_score']} / 100"],
            ["Generated", datetime.utcnow().isoformat(timespec="seconds")],
        ], colWidths=[1.5 * inch, 4.5 * inch])
        info_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.3 * inch))

        story.append(Paragraph("Findings", styles["Heading2"]))
        for i, f in enumerate(payload["findings"], start=1):
            story.append(Paragraph(
                f"{i}. [{f['severity']}] {f['title']} <font color='grey'>— {f['agent']}</font>",
                styles["Heading3"],
            ))
            story.append(Paragraph(
                f"<b>Location:</b> <font face='Courier'>{f.get('file_path') or '—'}:"
                f"{f.get('line_start') or '?'}</font>", styles["Normal"]))
            story.append(Paragraph(f.get("description") or "", styles["BodyText"]))
            if f.get("recommendation"):
                story.append(Paragraph(
                    f"<b>Recommendation:</b> {f['recommendation']}", styles["BodyText"]))
            story.append(Spacer(1, 0.1 * inch))

        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        logger.warning(f"ReportLab PDF failed, falling back to text PDF: {e}")
        return _build_minimal_pdf(build_markdown_report(db, analysis))


def _build_minimal_pdf(text: str) -> bytes:
    """Tiny PDF generator that wraps plain text — used as a last-resort fallback."""
    lines = text.splitlines() or [""]
    escaped = "\n".join(lines).replace("(", r"\(").replace(")", r"\)")
    content_stream = f"BT /F1 10 Tf 50 780 Td 12 TL {escaped} Tj ET"
    # Not a full PDF, but valid bytes for download
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
        b"4 0 obj<< /Length " + str(len(content_stream)).encode() + b" >>stream\n"
        + content_stream.encode("latin-1", errors="ignore")
        + b"\nendstream endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )
    return pdf


# --------------------- Patch ---------------------
def build_patch(db: Session, analysis: Analysis) -> str:
    """Generate a unified diff that summarizes each finding's fix proposal."""
    findings = analysis.findings or []
    if not findings:
        return "# No fixes proposed by CodeGuardian AI.\n"
    out: List[str] = []
    for f in findings:
        path = f.file_path or "unknown"
        rec = f.recommendation or "No recommendation provided."
        snippet = (f.code_snippet or "").splitlines() or [""]
        out.append(f"diff --git a/{path} b/{path}")
        out.append(f"--- a/{path}\n+++ b/{path}")
        if snippet:
            out.append("@@ -1,%d +1,%d @@" % (len(snippet), len(snippet) + 1))
            for line in snippet:
                out.append(f"-{line}")
            out.append(f"+# CodeGuardian: {rec}")
        out.append("")  # blank line
    return "\n".join(out)
