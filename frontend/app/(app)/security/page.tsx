"use client";
import * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge, Button } from "@/components/ui/primitives";
import { SeverityChip } from "@/components/ui/status";
import { Lock, Shield, ArrowRight } from "lucide-react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";

const SECURITY_RULES = [
  "SQL Injection (CWE-89)", "Cross-Site Scripting (CWE-79)", "Command Injection (CWE-78)",
  "Path Traversal (CWE-22)", "Hardcoded Secrets (CWE-798)", "Weak Authentication (CWE-287)",
  "Unsafe File Uploads (CWE-434)", "Insecure Deserialization (CWE-502)", "Open Redirect (CWE-601)",
  "Weak Hash (CWE-327)", "SSRF (CWE-918)", "XXE (CWE-611)",
];

export default function SecurityCenterPage() {
  const { projects, analyses, refreshProjects } = useAnalysis();
  const [findings, setFindings] = React.useState<any[]>([]);
  const [filter, setFilter] = React.useState<string | undefined>(undefined);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => { refreshProjects(); }, [refreshProjects]);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const all: any[] = [];
      for (const p of projects) {
        for (const a of (analyses[p.id] || [])) {
          if (a.status !== "completed") continue;
          try {
            const f = await api.listFindings(a.id, { agent: "security" });
            all.push(...(Array.isArray(f) ? f : []));
          } catch {}
        }
      }
      if (!cancelled) { setFindings(all); setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [projects, analyses]);

  const visible = filter ? findings.filter((f) => (f.severity || "").toLowerCase() === filter) : findings;
  const counts = findings.reduce<Record<string, number>>((acc, f) => {
    const s = (f.severity || "info").toLowerCase();
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Lock className="h-7 w-7 text-red-300" /> Security Center
          </h1>
          <p className="text-white/60 mt-1">OWASP-aligned security findings across all your projects.</p>
        </div>
        <Badge color="muted">{findings.length} findings</Badge>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {["critical", "high", "medium", "low", "info"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(filter === s ? undefined : s)}
            className={`rounded-2xl border p-5 text-left transition ${
              filter === s
                ? "border-violet-500/40 bg-violet-500/10"
                : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
            }`}
          >
            <div className="flex items-center gap-2 text-xs text-white/50 uppercase">
              <SeverityChip level={s} /> {s}
            </div>
            <div className="mt-3 text-3xl font-bold">{counts[s] || 0}</div>
          </button>
        ))}
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Shield className="h-5 w-5" /> Security rules covered
        </h2>
        <div className="flex flex-wrap gap-2">
          {SECURITY_RULES.map((r) => (
            <Badge key={r} color="muted">{r}</Badge>
          ))}
        </div>
      </Card>

      <Card className="p-0 overflow-hidden">
        <div className="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Findings</h2>
          <Badge color="muted">{visible.length} of {findings.length}</Badge>
        </div>
        <div className="divide-y divide-white/5">
          {loading && (
            <div className="p-10 text-center text-white/40 text-sm">Loading findings…</div>
          )}
          {!loading && visible.length === 0 && (
            <div className="p-10 text-center text-white/50">
              <Shield className="h-10 w-10 mx-auto text-emerald-300 mb-2" />
              {findings.length === 0
                ? "No security findings yet. Run an analysis to populate this view."
                : "No findings for the current filter."}
            </div>
          )}
          {!loading && visible.slice(0, 100).map((f) => (
            <div key={f.id} className="p-4 hover:bg-white/5 flex items-start gap-3">
              <SeverityChip level={f.severity} />
              <div className="flex-1 min-w-0">
                <div className="font-medium">{f.title}</div>
                <div className="text-xs text-white/40 font-mono truncate">
                  {f.file_path}:{f.line_start || "?"}
                </div>
                {f.cwe_id && (
                  <div className="text-xs text-white/50 mt-1">
                    CWE: {f.cwe_id}{f.cvss_score != null && ` · CVSS ${f.cvss_score}`}
                  </div>
                )}
                <p className="text-sm text-white/60 mt-2">{f.description}</p>
                {f.recommendation && (
                  <div className="mt-2 text-xs text-emerald-300">→ {f.recommendation}</div>
                )}
              </div>
              <Link href={`/analysis/${f.analysis_id}`}>
                <Button variant="ghost" size="sm"><ArrowRight className="h-3.5 w-3.5" /></Button>
              </Link>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
