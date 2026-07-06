"use client";
import * as React from "react";
import { useRouter } from "next/navigation";
import { useAnalysis } from "@/hooks/useAnalysis";
import { api, APIError } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button, Input, Label } from "@/components/ui/primitives";
import { Progress } from "@/components/ui/progress";
import {
  UploadCloud, Github, FolderInput, FileUp, Sparkles,
  File as FileIcon, CheckCircle2, Clock, Loader2,
  Shield, Bug, Code, Wand2, BookOpen, TestTube, Network, Package, GitBranch,
} from "lucide-react";
import { cn } from "@/lib/utils";

type SourceType = "github" | "zip" | "folder" | "file";

const AGENT_META: Record<string, { label: string; icon: any; color: string }> = {
  code_review:   { label: "Code Review",    icon: Code,      color: "text-cyan-300" },
  security:      { label: "Security",       icon: Shield,    color: "text-red-300" },
  bug:           { label: "Bug Detection",  icon: Bug,       color: "text-amber-300" },
  dependency:    { label: "Dependencies",   icon: Package,   color: "text-orange-300" },
  refactor:      { label: "Refactoring",    icon: GitBranch, color: "text-purple-300" },
  documentation: { label: "Documentation", icon: BookOpen,  color: "text-blue-300" },
  test:          { label: "Test Generator", icon: TestTube,  color: "text-green-300" },
  uml:           { label: "UML Diagrams",   icon: Network,   color: "text-indigo-300" },
  auto_fix:      { label: "Auto Fix",       icon: Wand2,     color: "text-pink-300" },
};

const ALL_AGENTS = Object.keys(AGENT_META);

interface AgentStatus {
  name: string;
  status: "pending" | "running" | "completed" | "failed";
}

export default function UploadPage() {
  const router = useRouter();
  const { refreshProjects, refreshAnalyses } = useAnalysis();
  const [source, setSource] = React.useState<SourceType>("github");
  const [url, setUrl] = React.useState("");
  const [name, setName] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Progress tracking
  const [analysisId, setAnalysisId] = React.useState<string | null>(null);
  const [progress, setProgress] = React.useState(0);
  const [statusMsg, setStatusMsg] = React.useState("Initialising…");
  const [agentStatuses, setAgentStatuses] = React.useState<AgentStatus[]>(
    ALL_AGENTS.map((n) => ({ name: n, status: "pending" }))
  );
  const pollRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Poll the status endpoint while analysis is running
  const pollStatus = React.useCallback(async (aid: string) => {
    try {
      const s = await api.getStatus(aid);
      setProgress(s.progress ?? 0);
      setStatusMsg(s.message || "Agents are running…");

      // Update per-agent statuses from agent_runs
      if (s.agent_runs?.length) {
        setAgentStatuses(ALL_AGENTS.map((name) => {
          const run = s.agent_runs.find((r: any) => r.agent_name === name);
          return {
            name,
            status: run
              ? (run.status as AgentStatus["status"])
              : (s.current_agents?.includes(name) ? "running" : "pending"),
          };
        }));
      } else if (s.current_agents?.length) {
        // Agents started but no DB rows yet — mark currently running ones
        setAgentStatuses((prev) =>
          prev.map((a) => ({
            ...a,
            status: s.current_agents.includes(a.name)
              ? "running"
              : a.status === "pending" ? "pending" : a.status,
          }))
        );
      }

      if (s.status === "completed" || s.status === "failed") {
        if (pollRef.current) clearTimeout(pollRef.current);
        setTimeout(() => router.push(`/analysis/${aid}`), 1200);
        return;
      }
    } catch {}
    pollRef.current = setTimeout(() => pollStatus(aid), 1000);
  }, [router]);

  React.useEffect(() => () => { if (pollRef.current) clearTimeout(pollRef.current); }, []);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      let workDir: string | undefined;
      let projectName = name;

      if (source === "github") {
        if (!url.trim()) throw new Error("GitHub URL is required");
        const proj = await api.createProject({
          name: name || url.split("/").pop() || "project",
          source_type: "github", source_ref: url.trim(),
        });
        await refreshProjects();
        const a = await api.createAnalysis(proj.id);
        setAnalysisId(a.id);
        await refreshAnalyses(proj.id);
        pollRef.current = setTimeout(() => pollStatus(a.id), 800);
        return;
      }

      if (source === "zip") {
        if (!file) throw new Error("Please choose a ZIP file");
        const up = await api.uploadZip(file, name || undefined);
        if (!up.work_dir) throw new Error(up.detail?.message || "ZIP upload failed");
        workDir = up.work_dir;
        projectName = name || up.project_name || "uploaded-project";
      } else if (source === "file") {
        if (!file) throw new Error("Please choose a file");
        const up = await api.uploadFile(file, name || undefined);
        if (!up.stored_at) throw new Error(up.detail?.message || "File upload failed");
        // Use stored_at (the file itself), not work_dir (its parent folder) —
        // source_type "file" is validated server-side with Path.is_file().
        workDir = up.stored_at;
        projectName = name || up.filename || "uploaded-file";
      } else if (source === "folder") {
        if (!url.trim()) throw new Error("Folder path is required");
        workDir = url.trim();
        projectName = name || url.split("/").pop() || "project";
      }

      const proj = await api.createProject({ name: projectName, source_type: source, source_ref: workDir });
      await refreshProjects();
      const a = await api.createAnalysis(proj.id);
      setAnalysisId(a.id);
      await refreshAnalyses(proj.id);
      pollRef.current = setTimeout(() => pollStatus(a.id), 800);
    } catch (e: any) {
      const msg = e instanceof APIError ? `${e.message} (${e.status})` : (e?.message || "Upload failed");
      setError(msg);
      setBusy(false);
    }
  };

  // ── Live progress screen ──────────────────────────────────────────────────
  if (analysisId) {
    return (
      <div className="max-w-2xl mx-auto space-y-6 py-8">
        <div className="text-center">
          <div className="inline-grid place-items-center h-20 w-20 rounded-3xl bg-gradient-to-br from-violet-500 to-cyan-500 mb-4 shadow-2xl shadow-violet-900/50">
            <Sparkles className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Agents are working…</h1>
          <p className="text-white/60 mt-1 text-sm">{statusMsg}</p>
        </div>

        {/* Overall progress bar */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-2 text-sm">
            <span className="text-white/60">Overall progress</span>
            <span className="font-mono font-semibold text-violet-300">{progress}%</span>
          </div>
          <div className="h-2.5 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400 transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
        </Card>

        {/* Agent grid */}
        <div className="grid grid-cols-3 gap-3">
          {agentStatuses.map(({ name, status }) => {
            const meta = AGENT_META[name];
            const Icon = meta.icon;
            return (
              <div
                key={name}
                className={cn(
                  "rounded-2xl border p-4 transition-all duration-300",
                  status === "completed" && "border-emerald-500/30 bg-emerald-500/5",
                  status === "running"   && "border-violet-500/50 bg-violet-500/10 shadow-lg shadow-violet-900/20",
                  status === "failed"    && "border-red-500/30 bg-red-500/5",
                  status === "pending"   && "border-white/5 bg-white/[0.03] opacity-50"
                )}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  {status === "running" ? (
                    <Loader2 className={cn("h-4 w-4 flex-shrink-0 animate-spin", meta.color)} />
                  ) : status === "completed" ? (
                    <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-400" />
                  ) : status === "failed" ? (
                    <span className="h-4 w-4 flex-shrink-0 text-red-400 text-xs">✗</span>
                  ) : (
                    <Clock className="h-4 w-4 flex-shrink-0 text-white/20" />
                  )}
                  <span className={cn(
                    "text-xs font-semibold",
                    status === "running" ? "text-white" : "text-white/60"
                  )}>
                    {meta.label}
                  </span>
                </div>
                <div className="text-[10px] uppercase tracking-widest text-white/30 capitalize">
                  {status}
                </div>
              </div>
            );
          })}
        </div>

        <p className="text-center text-xs text-white/30">
          You will be redirected automatically when complete. Wave 1 (static) → Wave 2 (generative)
        </p>
      </div>
    );
  }

  // ── Upload form ───────────────────────────────────────────────────────────
  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Upload &amp; analyze</h1>
        <p className="text-white/60 mt-1">Drop a project, kick off the agents, watch them collaborate.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {([
              { key: "github", label: "GitHub URL", icon: Github },
              { key: "zip",    label: "ZIP file",   icon: FileUp },
              { key: "folder", label: "Folder",     icon: FolderInput },
              { key: "file",   label: "Single file", icon: FileIcon },
            ] as { key: SourceType; label: string; icon: any }[]).map((o) => (
              <button key={o.key} onClick={() => { setSource(o.key); setError(null); }}
                className={cn(
                  "rounded-2xl border p-4 text-left transition-all",
                  source === o.key
                    ? "border-violet-500/40 bg-gradient-to-br from-violet-500/15 to-cyan-500/5"
                    : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
                )}>
                <o.icon className="h-5 w-5 text-violet-300" />
                <div className="mt-3 font-medium text-sm">{o.label}</div>
              </button>
            ))}
          </div>

          <div className="space-y-3">
            <div>
              <Label>Project name (optional)</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="my-awesome-app" className="mt-1" />
            </div>
            {source === "github" && (
              <div>
                <Label>Repository URL</Label>
                <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo" className="mt-1" />
              </div>
            )}
            {source === "folder" && (
              <div>
                <Label>Server-side folder path</Label>
                <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="/path/to/folder" className="mt-1" />
              </div>
            )}
            {(source === "zip" || source === "file") && (
              <div>
                <Label>Choose a {source === "zip" ? "ZIP archive" : "source file"}</Label>
                <input type="file" accept={source === "zip" ? ".zip" : undefined}
                  onChange={(e) => { setFile(e.target.files?.[0] || null); setError(null); }}
                  className="mt-1 block w-full text-sm text-white/60 file:mr-4 file:rounded-lg file:border-0 file:bg-violet-600/30 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-violet-600/40" />
                {file && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-white/60">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />
                    {file.name} ({Math.round(file.size / 1024)} KB)
                  </div>
                )}
              </div>
            )}
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</div>
          )}

          <Button variant="gradient" onClick={submit} disabled={busy}>
            {busy ? <><Loader2 className="h-4 w-4 animate-spin" /> Starting…</> : <><UploadCloud className="h-4 w-4" /> Analyze</>}
          </Button>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-violet-300" /> How it works
          </h3>
          <div className="space-y-3 text-sm text-white/70">
            {[
              { wave: "Wave 1", agents: "Code Review · Security · Bugs · Deps", color: "text-cyan-300" },
              { wave: "Wave 2", agents: "Refactor · Docs · Tests · UML", color: "text-violet-300" },
              { wave: "Wave 3", agents: "Auto Fix patches", color: "text-pink-300" },
            ].map((w) => (
              <div key={w.wave} className="flex gap-3">
                <span className={cn("font-bold flex-shrink-0 w-16", w.color)}>{w.wave}</span>
                <span>{w.agents}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-white/40">
            Waves 1 and 2 run in parallel — analysis is typically 3–5× faster than sequential mode.
          </div>
        </Card>
      </div>
    </div>
  );
}
