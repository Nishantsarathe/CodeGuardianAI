"use client";
import * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge, Button } from "@/components/ui/primitives";
import { Package, ArrowUpRight, AlertTriangle, Sparkles } from "lucide-react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";

export default function DependenciesPage() {
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
            const f = await api.listFindings(a.id, { agent: "dependency" });
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
            <Package className="h-7 w-7 text-amber-300" /> Dependencies
          </h1>
          <p className="text-white/60 mt-1">Outdated, unused and vulnerable packages.</p>
        </div>
        <Badge color="muted">{findings.length} findings</Badge>
      </header>

      <div className="grid gap-3 md:grid-cols-2">
        {loading && <Card className="p-10 text-center text-white/40 md:col-span-2">Loading…</Card>}
        {!loading && findings.length === 0 && (
          <Card className="p-10 text-center text-white/50 md:col-span-2">
            <Sparkles className="h-10 w-10 mx-auto text-amber-300 mb-2" />
            Run an analysis to see dependency findings.
          </Card>
        )}
        {!loading && findings.map((f) => (
          <Card key={f.id} className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-semibold flex items-center gap-2">
                  {f.severity === "critical"
                    ? <AlertTriangle className="h-4 w-4 text-red-300" />
                    : <Package className="h-4 w-4 text-amber-300" />}
                  {f.title}
                </div>
                {f.file_path && (
                  <div className="text-xs text-white/50 mt-1 font-mono">{f.file_path}</div>
                )}
              </div>
              <Badge color={f.severity === "critical" ? "red" : "amber"}>{f.severity}</Badge>
            </div>
            <p className="mt-2 text-sm text-white/70">{f.description}</p>
            {f.extras?.latest && (
              <div className="mt-2 text-xs text-white/50">
                Current: <code className="text-white/70">{f.extras.current}</code> · Latest:{" "}
                <code className="text-emerald-300">{f.extras.latest}</code>
              </div>
            )}
            {f.recommendation && (
              <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-sm text-emerald-200">
                → {f.recommendation}
              </div>
            )}
            <div className="mt-3 flex justify-end">
              <Link href={`/analysis/${f.analysis_id}`}>
                <Button variant="ghost" size="sm">
                  Open <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
