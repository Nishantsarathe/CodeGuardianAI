"use client";
import * as React from "react";
import Link from "next/link";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Badge, Button } from "@/components/ui/primitives";
import { SeverityChip } from "@/components/ui/status";
import { ExternalLink } from "lucide-react";
import { formatDate, severityColor } from "@/lib/utils";

const ALL_AGENTS = ["security", "bug", "code_review", "auto_fix", "refactor", "documentation", "test", "uml", "dependency"];

export default function AnalysisListPage() {
  const { projects, analyses, refreshProjects, refreshAnalyses } = useAnalysis();
  const [selected, setSelected] = React.useState<string | null>(null);
  const [findings, setFindings] = React.useState<any[]>([]);
  const [filter, setFilter] = React.useState<{ severity?: string; agent?: string }>({});
  const [findingsLoading, setFindingsLoading] = React.useState(false);

  React.useEffect(() => { refreshProjects(); }, [refreshProjects]);

  React.useEffect(() => {
    if (projects[0] && !selected) setSelected(projects[0].id);
  }, [projects, selected]);

  React.useEffect(() => {
    if (selected) refreshAnalyses(selected);
  }, [selected, refreshAnalyses]);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = analyses[selected || ""] || [];
      const latest = list[0];
      if (!latest) { setFindings([]); return; }
      setFindingsLoading(true);
      try {
        const f = await api.listFindings(latest.id, {
          agent: filter.agent,
          severity: filter.severity,
        });
        if (!cancelled) setFindings(Array.isArray(f) ? f : []);
      } catch {
        if (!cancelled) setFindings([]);
      } finally {
        if (!cancelled) setFindingsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [analyses, selected, filter]);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analyses</h1>
          <p className="text-white/60 mt-1">Browse every project and its findings.</p>
        </div>
        <Link href="/upload">
          <Button variant="gradient">New analysis</Button>
        </Link>
      </header>

      <div className="grid lg:grid-cols-[280px,1fr] gap-6">
        {/* Project sidebar */}
        <aside className="space-y-3">
          <div className="text-xs uppercase tracking-widest text-white/40 px-2">Projects</div>
          {projects.length === 0 && (
            <div className="text-sm text-white/50">
              No projects yet. <Link href="/upload" className="text-violet-300 hover:underline">Upload one</Link>.
            </div>
          )}
          {projects.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p.id)}
              className={`w-full text-left p-4 rounded-2xl border transition-colors ${
                selected === p.id
                  ? "border-violet-500/40 bg-violet-500/10"
                  : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
              }`}
            >
              <div className="font-semibold truncate">{p.name}</div>
              <div className="text-xs text-white/50 mt-1">
                {p.file_count} files · {p.language || "—"}
              </div>
              {p.health_score != null && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="h-1.5 flex-1 bg-white/10 rounded-full overflow-hidden">
                    <span
                      className="block h-full bg-gradient-to-r from-violet-500 to-cyan-400"
                      style={{ width: `${p.health_score}%` }}
                    />
                  </span>
                  <span className="text-xs">{Math.round(p.health_score)}</span>
                </div>
              )}
            </button>
          ))}
        </aside>

        {/* Analysis list */}
        <section className="space-y-4">
          {selected && (analyses[selected] || []).length === 0 && (
            <Card className="p-8 text-center text-white/50">
              No analyses for this project yet.{" "}
              <Link href="/upload" className="text-violet-300 hover:underline">Run one</Link>.
            </Card>
          )}

          {(analyses[selected || ""] || []).map((a) => (
            <Card key={a.id} className="p-5">
              <div className="flex items-start justify-between flex-wrap gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge
                      color={a.status === "completed" ? "green" : a.status === "failed" ? "red" : "cyan"}
                    >
                      {a.status}
                    </Badge>
                    <span className="text-xs text-white/40">{formatDate(a.created_at)}</span>
                  </div>
                  <div className="mt-1 font-mono text-sm text-white/70 truncate max-w-xs">{a.id}</div>
                </div>
                <Link href={`/analysis/${a.id}`}>
                  <Button variant="outline" size="sm">
                    Open <ExternalLink className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>

              {/* Agent filter chips */}
              <div className="mt-4 flex flex-wrap gap-2">
                {ALL_AGENTS.map((ag) => (
                  <button
                    key={ag}
                    onClick={() => setFilter((f) => ({ ...f, agent: f.agent === ag ? undefined : ag }))}
                    className={`text-xs rounded-full border px-2.5 py-1 transition ${
                      filter.agent === ag
                        ? "border-violet-500/50 bg-violet-500/10 text-white"
                        : "border-white/10 text-white/60 hover:bg-white/5"
                    }`}
                  >
                    {ag}
                  </button>
                ))}
              </div>

              {/* Severity filter chips */}
              <div className="mt-2 flex flex-wrap gap-2">
                {["critical", "high", "medium", "low", "info"].map((s) => (
                  <button
                    key={s}
                    onClick={() => setFilter((f) => ({ ...f, severity: f.severity === s ? undefined : s }))}
                    className={`text-xs rounded-full border px-2.5 py-1 transition ${
                      filter.severity === s ? "border-current bg-current/10" : "border-white/10 text-white/60 hover:bg-white/5"
                    }`}
                    style={filter.severity === s ? { color: severityColor(s) } : {}}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Findings */}
              <div className="mt-4 space-y-2">
                {findingsLoading && (
                  <div className="text-sm text-white/40">Loading findings…</div>
                )}
                {!findingsLoading && findings.length === 0 && (
                  <div className="text-sm text-white/50">No findings match the current filter.</div>
                )}
                {!findingsLoading && findings.slice(0, 20).map((f) => (
                  <div
                    key={f.id}
                    className="rounded-lg border border-white/5 bg-white/[0.02] p-3 flex items-start gap-3"
                  >
                    <SeverityChip level={f.severity} />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{f.title}</div>
                      <div className="text-xs text-white/40 font-mono truncate">
                        {f.file_path || "—"}:{f.line_start || "?"}
                      </div>
                    </div>
                    <Badge color="muted">{f.agent_name}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </section>
      </div>
    </div>
  );
}
