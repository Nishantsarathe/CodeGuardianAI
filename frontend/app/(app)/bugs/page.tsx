"use client";
import * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge, Button } from "@/components/ui/primitives";
import { SeverityChip } from "@/components/ui/status";
import { Bug, ArrowRight } from "lucide-react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";

export default function BugCenterPage() {
  const { projects, analyses, refreshProjects } = useAnalysis();
  const [findings, setFindings] = React.useState<any[]>([]);
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
            const f = await api.listFindings(a.id, { agent: "bug" });
            all.push(...(Array.isArray(f) ? f : []));
          } catch {}
        }
      }
      if (!cancelled) { setFindings(all); setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [projects, analyses]);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Bug className="h-7 w-7 text-amber-300" /> Bug Center
          </h1>
          <p className="text-white/60 mt-1">Logic, runtime, and performance bugs across all projects.</p>
        </div>
        <Badge color="muted">{findings.length} bugs</Badge>
      </header>

      <div className="space-y-3">
        {loading && (
          <Card className="p-10 text-center text-white/40">Loading…</Card>
        )}
        {!loading && findings.length === 0 && (
          <Card className="p-10 text-center text-white/50">
            <Bug className="h-10 w-10 mx-auto text-emerald-300 mb-2" />
            No bugs found yet. Run an analysis to populate this view.
          </Card>
        )}
        {!loading && findings.slice(0, 100).map((f) => (
          <Card key={f.id} className="p-5">
            <div className="flex items-start gap-3 flex-wrap">
              <SeverityChip level={f.severity} />
              <div className="font-semibold flex-1">{f.title}</div>
              {f.category && <Badge color="muted">{f.category}</Badge>}
            </div>
            {f.file_path && (
              <div className="mt-2 text-xs text-white/40 font-mono">
                {f.file_path}:{f.line_start || "?"}
              </div>
            )}
            <p className="mt-2 text-sm text-white/70">{f.description}</p>
            {f.recommendation && (
              <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-sm">
                <strong className="text-emerald-300">Recommendation:</strong> {f.recommendation}
              </div>
            )}
            <div className="mt-3 flex justify-end">
              <Link href={`/analysis/${f.analysis_id}`}>
                <Button variant="ghost" size="sm">
                  Open analysis <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
