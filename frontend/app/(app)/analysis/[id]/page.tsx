"use client";
import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { AgentCard, HealthRing, SeverityChip } from "@/components/ui/status";
import { Button, Badge } from "@/components/ui/primitives";
import { Progress, Skeleton } from "@/components/ui/progress";
import { api } from "@/lib/api";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  Sparkles, Shield, Bug, Wand2, Cpu, Package, BookOpen,
  RefreshCw, FileBarChart, MessagesSquare,
} from "lucide-react";
import { formatDate } from "@/lib/utils";

const SEV_COLORS: Record<string, string> = {
  critical: "#ef4444", high: "#f97316", medium: "#eab308", low: "#22c55e", info: "#3b82f6",
};

const AGENT_META: Record<string, { name: string; icon: any; accent: any }> = {
  coordinator:   { name: "Coordinator",    icon: Sparkles, accent: "violet" },
  code_review:   { name: "Code Review",    icon: Shield,   accent: "cyan" },
  security:      { name: "Security",       icon: Shield,   accent: "red" },
  bug:           { name: "Bug Detection",  icon: Bug,      accent: "amber" },
  auto_fix:      { name: "Auto Fix",       icon: Wand2,    accent: "green" },
  documentation: { name: "Documentation", icon: BookOpen,  accent: "blue" },
  refactor:      { name: "Refactoring",   icon: Cpu,      accent: "pink" },
  test:          { name: "Test Generator", icon: Cpu,      accent: "violet" },
  uml:           { name: "UML",           icon: Sparkles, accent: "cyan" },
  dependency:    { name: "Dependency",    icon: Package,  accent: "amber" },
};

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = React.useState<any>(null);
  const [status, setStatus] = React.useState<any>(null);
  const [findings, setFindings] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  const refresh = React.useCallback(async () => {
    if (!id) return;
    try {
      const [a, s, f] = await Promise.all([
        api.getAnalysis(id),
        api.getStatus(id),
        api.listFindings(id),
      ]);
      setAnalysis(a);
      setStatus(s);
      setFindings(Array.isArray(f) ? f : []);
    } catch (e) {
      // silently fail on poll errors
    } finally {
      setLoading(false);
    }
  }, [id]);

  React.useEffect(() => {
    refresh();
    // Auto-refresh while running
    const t = setInterval(() => {
      if (status?.status === "running" || status?.status === "pending") refresh();
    }, 3000);
    return () => clearInterval(t);
  }, [refresh, status?.status]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="text-center py-20 text-white/60">
        Analysis not found.{" "}
        <Link href="/analysis" className="text-violet-300 hover:underline">Go back</Link>
      </div>
    );
  }

  const sevCounts = findings.reduce<Record<string, number>>((acc, f) => {
    const s = (f.severity || "info").toLowerCase();
    acc[s] = (acc[s] || 0) + 1;
    return acc;
  }, {});
  const sevData = ["critical", "high", "medium", "low", "info"].map((s) => ({
    severity: s, count: sevCounts[s] || 0,
  }));

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-white/40">Analysis</div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight font-mono">
            {id?.slice(0, 8)}…
            <span className="text-white/40 text-sm ml-2 font-sans">
              {formatDate(analysis.created_at)}
            </span>
          </h1>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <Badge
              color={
                status?.status === "completed" ? "green"
                  : status?.status === "failed" ? "red"
                  : "cyan"
              }
            >
              {status?.status || "—"}
            </Badge>
            <span className="text-white/40">
              {analysis.summary?.agents_run?.length || 0} agents ran
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={refresh}>
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
          <Link href={`/reports`}>
            <Button variant="gradient"><FileBarChart className="h-4 w-4" /> Reports</Button>
          </Link>
          <Link href={`/chat`}>
            <Button variant="outline"><MessagesSquare className="h-4 w-4" /> Chat</Button>
          </Link>
        </div>
      </header>

      <section className="grid gap-4 lg:grid-cols-4">
        <Card className="p-6 flex items-center gap-4">
          <HealthRing value={analysis.health_score || 0} />
          <div>
            <div className="text-sm text-white/50">Repository health</div>
            <div className="text-xs text-white/40 mt-1">0–100, weighted</div>
          </div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-white/50">Findings</div>
          <div className="text-3xl font-bold">{findings.length}</div>
          <div className="mt-2 text-xs text-white/40">
            across {Object.keys(sevCounts).length} severities
          </div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-white/50">Duration</div>
          <div className="text-3xl font-bold">
            {analysis.duration_ms ? `${Math.round(analysis.duration_ms / 1000)}s` : "—"}
          </div>
          <div className="mt-2 text-xs text-white/40">start to finish</div>
        </Card>
        <Card className="p-6">
          <div className="text-sm text-white/50">Progress</div>
          <div className="text-3xl font-bold capitalize">{status?.progress ?? 0}%</div>
          <Progress
            value={status?.progress || 0}
            color={status?.status === "completed" ? "cyan" : "violet"}
            className="mt-3"
          />
        </Card>
      </section>

      {/* Agent timeline */}
      {(status?.agent_runs || []).length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Agent timeline</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {(status.agent_runs || []).map((r: any) => {
              const meta = AGENT_META[r.agent_name] || { name: r.agent_name, icon: Cpu, accent: "violet" };
              const summary = analysis.summary?.agent_summaries?.[r.agent_name] || {};
              return (
                <AgentCard
                  key={r.id}
                  agent={r.agent_name}
                  status={r.status}
                  progress={r.status === "completed" ? 100 : 50}
                  summary={summary}
                  accent={meta.accent as any}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Charts */}
      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Findings by severity</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sevData}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="severity" stroke="rgba(255,255,255,0.4)" fontSize={11} />
                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(255,255,255,0.1)" }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {sevData.map((s) => <Cell key={s.severity} fill={SEV_COLORS[s.severity]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">By severity</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={sevData} dataKey="count" nameKey="severity" innerRadius={50} outerRadius={90} paddingAngle={4}>
                  {sevData.map((s) => <Cell key={s.severity} fill={SEV_COLORS[s.severity]} />)}
                </Pie>
                <Legend wrapperStyle={{ color: "white", fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(255,255,255,0.1)" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </section>

      {/* Findings list */}
      <section>
        <h2 className="text-lg font-semibold mb-3">
          Top findings
          <span className="ml-2 text-sm font-normal text-white/40">
            (showing {Math.min(findings.length, 20)} of {findings.length})
          </span>
        </h2>
        <div className="space-y-3">
          {findings.length === 0 && (
            <div className="text-sm text-white/50">
              No findings yet — agents are still running or no issues were detected.
            </div>
          )}
          {findings.slice(0, 20).map((f) => (
            <Card key={f.id} className="p-5">
              <div className="flex items-start gap-3 flex-wrap">
                <SeverityChip level={f.severity} />
                <div className="font-semibold flex-1">{f.title}</div>
                <Badge color="muted">{f.agent_name}</Badge>
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
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
