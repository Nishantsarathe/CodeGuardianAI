"use client";
import * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/primitives";
import { Network, Sparkles } from "lucide-react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";

export default function ArchitecturePage() {
  const { projects, analyses, refreshProjects } = useAnalysis();
  const [items, setItems] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => { refreshProjects(); }, [refreshProjects]);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const list: any[] = [];
      for (const p of projects) {
        for (const a of (analyses[p.id] || [])) {
          if (a.status !== "completed") continue;
          try {
            const findings = await api.listFindings(a.id, { agent: "uml" });
            for (const f of Array.isArray(findings) ? findings : []) {
              if (f.extras) list.push({ analysis: a, project: p, ...f.extras });
            }
          } catch {}
        }
      }
      if (!cancelled) { setItems(list); setLoading(false); }
    })();
    return () => { cancelled = true; };
  }, [projects, analyses]);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Network className="h-7 w-7 text-cyan-300" /> Architecture Viewer
          </h1>
          <p className="text-white/60 mt-1">Class, sequence, component and dependency diagrams.</p>
        </div>
      </header>

      <div className="space-y-6">
        {loading && <Card className="p-10 text-center text-white/40">Loading diagrams…</Card>}
        {!loading && items.length === 0 && (
          <Card className="p-10 text-center text-white/50">
            <Sparkles className="h-10 w-10 mx-auto text-cyan-300 mb-2" />
            UML diagrams are produced by the UML Agent. Run an analysis to see them here.
          </Card>
        )}
        {!loading && items.map((it, idx) => (
          <Card key={idx} className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-semibold">{it.project?.name}</div>
                <div className="text-xs text-white/40 font-mono">analysis {it.analysis?.id?.slice(0, 8)}…</div>
              </div>
              <Link href={`/analysis/${it.analysis?.id}`}>
                <Button variant="ghost" size="sm">View</Button>
              </Link>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {(["class", "component", "sequence", "dependency", "architecture"] as const).map((k) =>
                it[k] ? (
                  <div key={k} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                    <div className="text-xs uppercase tracking-widest text-white/40 mb-2">{k} diagram</div>
                    <pre className="text-xs font-mono whitespace-pre-wrap text-white/80 max-h-72 overflow-auto">
                      {it[k]}
                    </pre>
                  </div>
                ) : null
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
