"use client";
import * as React from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge, Button } from "@/components/ui/primitives";
import { FileBarChart, FileText, FileCode, FileType, Archive } from "lucide-react";
import { useAnalysis } from "@/hooks/useAnalysis";
import { getAccessToken } from "@/lib/storage";

const FORMATS = ["markdown", "html", "pdf", "patch", "bundle"] as const;
type Format = typeof FORMATS[number];

const ICONS: Record<Format, React.ComponentType<any>> = {
  markdown: FileText, html: FileCode, pdf: FileType, patch: FileCode, bundle: Archive,
};

/**
 * Downloads a report format, injecting the auth bearer token.
 * Using a dynamic link with the token avoids exposing it in a GET query-string cache.
 */
async function downloadReport(analysisId: string, format: Format) {
  const token = getAccessToken();
  const res = await fetch(`/api/backend/reports/${analysisId}/${format}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) {
    alert(`Failed to download ${format} report: ${res.statusText}`);
    return;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report_${analysisId}.${format === "bundle" ? "zip" : format === "patch" ? "patch" : format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { projects, analyses, refreshProjects } = useAnalysis();
  const [downloading, setDownloading] = React.useState<string | null>(null);

  React.useEffect(() => { refreshProjects(); }, [refreshProjects]);

  const latestByProject = React.useMemo(
    () =>
      projects
        .map((p) => ({ project: p, analysis: (analyses[p.id] || [])[0] }))
        .filter((x) => x.analysis?.status === "completed"),
    [projects, analyses]
  );

  const handleDownload = async (analysisId: string, format: Format) => {
    const key = `${analysisId}:${format}`;
    setDownloading(key);
    try {
      await downloadReport(analysisId, format);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileBarChart className="h-7 w-7 text-violet-300" /> Reports
          </h1>
          <p className="text-white/60 mt-1">
            Download Markdown, HTML, PDF, patch or a complete bundle.
          </p>
        </div>
        <Badge color="muted">{latestByProject.length} completed analyses</Badge>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {latestByProject.length === 0 && (
          <Card className="p-10 text-center text-white/50 md:col-span-2">
            No completed analyses yet. Upload a repo and run an analysis first.
          </Card>
        )}
        {latestByProject.map(({ project, analysis }) => (
          <Card key={analysis.id} className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">{project.name}</div>
                <div className="text-xs text-white/40 font-mono truncate">{analysis.id}</div>
              </div>
              <Badge color="muted">
                Health {analysis.health_score != null ? Math.round(analysis.health_score) : "—"}
              </Badge>
            </div>
            <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-2">
              {FORMATS.map((format) => {
                const Icon = ICONS[format];
                const key = `${analysis.id}:${format}`;
                return (
                  <Button
                    key={format}
                    variant="outline"
                    className="w-full"
                    disabled={downloading === key}
                    onClick={() => handleDownload(analysis.id, format)}
                  >
                    <Icon className="h-4 w-4" />
                    {downloading === key ? "…" : format.toUpperCase()}
                  </Button>
                );
              })}
            </div>
            <div className="mt-3 flex justify-end">
              <Link href={`/analysis/${analysis.id}`}>
                <Button variant="ghost" size="sm">Open analysis</Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
