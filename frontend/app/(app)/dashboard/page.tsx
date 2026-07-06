"use client";
import * as React from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api } from "@/lib/api";
import { Card, StatCard } from "@/components/ui/card";
import { AgentCard, HealthRing, SeverityChip } from "@/components/ui/status";
import { Progress, Skeleton } from "@/components/ui/progress";
import { Button, Badge } from "@/components/ui/primitives";
import {
  AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis,
  BarChart, Bar, CartesianGrid, PieChart, Pie, Cell, Legend,
} from "recharts";
import {
  FolderKanban, Activity, Shield, AlertTriangle, Upload,
  MessagesSquare, Network,
} from "lucide-react";
import { FileSearch } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";

const SEV_COLORS: Record<string, string> = {
  critical: "#ef4444", high: "#f97316", medium: "#eab308", low: "#22c55e", info: "#3b82f6",
};

export default function DashboardPage() {
  const { user } = useAuth();
  const { projects, refreshProjects } = useAnalysis();
  const [summary, setSummary] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => { refreshProjects(); }, [refreshProjects]);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await api.dashboard();
        if (!cancelled) setSummary(s);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-white/40">Welcome back</div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            {user?.full_name?.split(" ")[0] || user?.username}, your code is{" "}
            <span className="gradient-text">safe</span>.
          </h1>
        </div>
        <div className="flex gap-2">
          <Link href="/upload">
            <Button variant="gradient"><Upload className="h-4 w-4" /> New analysis</Button>
          </Link>
          <Link href="/chat">
            <Button variant="outline"><MessagesSquare className="h-4 w-4" /> Ask AI</Button>
          </Link>
        </div>
      </header>

      {error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          {error}
        </div>
      )}

      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Projects" value={loading ? "…" : (summary?.total_projects ?? 0)} hint="tracked" icon={<FolderKanban className="h-5 w-5" />} color="violet" />
        <StatCard title="Analyses" value={loading ? "…" : (summary?.total_analyses ?? 0)} hint={`${summary?.completed_analyses ?? 0} completed`} icon={<Activity className="h-5 w-5" />} color="cyan" />
        <StatCard title="Findings" value={loading ? "…" : (summary?.total_findings ?? 0)} hint="across all analyses" icon={<AlertTriangle className="h-5 w-5" />} color="amber" />
        <StatCard title="Avg health" value={loading ? "…" : (summary?.average_health_score != null ? `${summary.average_health_score}` : "—")} hint="0–100" icon={<Shield className="h-5 w-5" />} color="green" />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Analyses trend</h2>
            <Badge color="muted">Last 7 days</Badge>
          </div>
          <div className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : summary?.analyses_trend ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.analyses_trend}>
                  <defs>
                    <linearGradient id="trendG" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#7c3aed" stopOpacity={0.6} />
                      <stop offset="100%" stopColor="#7c3aed" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.4)" fontSize={11} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} allowDecimals={false} />
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <Tooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Area type="monotone" dataKey="count" stroke="#7c3aed" strokeWidth={2} fill="url(#trendG)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-white/40 text-sm">No data yet</div>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Severity distribution</h2>
          <div className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : summary?.severity_distribution ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={summary.severity_distribution} dataKey="count" nameKey="severity"
                    innerRadius={50} outerRadius={90} paddingAngle={4}>
                    {summary.severity_distribution.map((entry: any) => (
                      <Cell key={entry.severity} fill={SEV_COLORS[entry.severity] || "#8a93a6"} />
                    ))}
                  </Pie>
                  <Legend wrapperStyle={{ color: "white", fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(255,255,255,0.1)" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-white/40 text-sm">No data yet</div>
            )}
          </div>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Top projects</h2>
            <Link href="/upload">
              <Button variant="ghost" size="sm">All projects <ArrowRight className="h-4 w-4" /></Button>
            </Link>
          </div>
          {summary?.top_projects?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs uppercase tracking-wider text-white/40">
                  <tr>
                    <th className="text-left py-2">Name</th>
                    <th className="text-left">Language</th>
                    <th className="text-left">Files</th>
                    <th className="text-left">Health</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.top_projects.map((p: any) => (
                    <tr key={p.id} className="border-t border-white/5 hover:bg-white/5">
                      <td className="py-3 font-medium">{p.name}</td>
                      <td className="text-white/60">{p.language || "—"}</td>
                      <td className="text-white/60">{p.file_count}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Progress value={p.health_score || 0} className="w-24"
                            color={(p.health_score || 0) > 70 ? "cyan" : "amber"} />
                          <span className="text-white/60">
                            {p.health_score != null ? Math.round(p.health_score) : "—"}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-white/50">
              No projects yet.{" "}
              <Link href="/upload" className="text-violet-300 hover:underline">Upload a repository</Link>{" "}
              to get started.
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Agent activity</h2>
          <div className="h-72">
            {loading ? (
              <Skeleton className="h-full w-full" />
            ) : summary?.agent_counts?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.agent_counts}>
                  <XAxis dataKey="agent" stroke="rgba(255,255,255,0.4)" fontSize={10} angle={-20} textAnchor="end" height={50} />
                  <YAxis stroke="rgba(255,255,255,0.4)" fontSize={11} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: "#0b0f1a", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-white/40 text-sm">No data yet</div>
            )}
          </div>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-4">Quick actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/upload",       title: "Upload a repo",   desc: "GitHub URL, ZIP, folder or file.", icon: Upload },
            { href: "/analysis",     title: "Run an analysis", desc: "Spin up the 10-agent workflow.",   icon: FileSearch },
            { href: "/architecture", title: "Architecture",    desc: "Browse class, sequence & deps.",    icon: Network },
            { href: "/chat",         title: "AI Chat",         desc: "Ask anything about your code.",    icon: MessagesSquare },
          ].map((q) => (
            <Link key={q.href} href={q.href}>
              <Card className="p-5 hover:border-violet-500/30 transition-colors h-full cursor-pointer">
                <div className="grid place-items-center h-10 w-10 rounded-xl bg-white/5 ring-1 ring-white/10 mb-3">
                  <q.icon className="h-5 w-5 text-violet-300" />
                </div>
                <div className="font-semibold">{q.title}</div>
                <p className="text-sm text-white/50 mt-1">{q.desc}</p>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
