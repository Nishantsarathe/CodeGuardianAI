import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(d: string | Date | null | undefined, fallback = "—"): string {
  if (!d) return fallback;
  const date = typeof d === "string" ? new Date(d) : d;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function formatNumber(n: number | null | undefined, fallback = "—"): string {
  if (n === null || n === undefined || isNaN(Number(n))) return fallback;
  return new Intl.NumberFormat().format(Number(n));
}

export function severityColor(level: string): string {
  switch ((level || "").toLowerCase()) {
    case "critical": return "#ef4444";
    case "high": return "#f97316";
    case "medium": return "#eab308";
    case "low": return "#22c55e";
    case "info": return "#3b82f6";
    default: return "#8a93a6";
  }
}

export function truncate(s: string, n = 200): string {
  if (!s) return "";
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

export function downloadFile(url: string, name: string) {
  if (typeof window === "undefined") return;
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
