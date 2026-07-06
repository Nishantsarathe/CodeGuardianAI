"use client";
import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Cpu, Lock, AlertTriangle, CheckCircle2, Clock, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function SeverityChip({ level, className }: { level: string; className?: string }) {
  const map: Record<string, { bg: string; text: string; ring: string; icon: any }> = {
    critical: { bg: "bg-red-500/10", text: "text-red-300", ring: "ring-red-500/30", icon: AlertTriangle },
    high: { bg: "bg-orange-500/10", text: "text-orange-300", ring: "ring-orange-500/30", icon: AlertTriangle },
    medium: { bg: "bg-amber-500/10", text: "text-amber-300", ring: "ring-amber-500/30", icon: AlertTriangle },
    low: { bg: "bg-emerald-500/10", text: "text-emerald-300", ring: "ring-emerald-500/30", icon: CheckCircle2 },
    info: { bg: "bg-blue-500/10", text: "text-blue-300", ring: "ring-blue-500/30", icon: CheckCircle2 },
  };
  const conf = map[level?.toLowerCase()] || map.info;
  const Icon = conf.icon;
  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1",
      conf.bg, conf.text, conf.ring, className
    )}>
      <Icon className="h-3 w-3" />
      {level}
    </span>
  );
}

export function HealthRing({ value, size = 96 }: { value: number; size?: number }) {
  const v = Math.max(0, Math.min(100, value || 0));
  const r = (size - 12) / 2;
  const c = 2 * Math.PI * r;
  const off = c - (v / 100) * c;
  const color = v >= 80 ? "#22c55e" : v >= 60 ? "#eab308" : v >= 40 ? "#f97316" : "#ef4444";
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="none" />
        <motion.circle
          cx={size/2} cy={size/2} r={r}
          stroke={color} strokeWidth="8" strokeLinecap="round" fill="none"
          strokeDasharray={c} initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: off }} transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className="text-2xl font-bold" style={{ color }}>{Math.round(v)}</div>
          <div className="text-[10px] uppercase tracking-wider text-white/50">Health</div>
        </div>
      </div>
    </div>
  );
}

export function AgentStatusIcon({ status, className }: { status: string; className?: string }) {
  const map: Record<string, { icon: any; color: string; pulse: boolean }> = {
    pending: { icon: Clock, color: "text-white/40", pulse: false },
    running: { icon: Cpu, color: "text-cyan-300", pulse: true },
    completed: { icon: CheckCircle2, color: "text-emerald-300", pulse: false },
    failed: { icon: X, color: "text-red-300", pulse: false },
    cancelled: { icon: X, color: "text-white/40", pulse: false },
  };
  const conf = map[status?.toLowerCase()] || map.pending;
  const Icon = conf.icon;
  return (
    <span className={cn("relative inline-flex", className)}>
      <Icon className={cn("h-4 w-4", conf.color)} />
      {conf.pulse && (
        <span className="absolute inset-0 rounded-full animate-ping bg-cyan-400/30" />
      )}
    </span>
  );
}

export function AgentCard({ agent, status, progress = 0, summary, accent = "violet" }: {
  agent: string; status: string; progress?: number; summary?: any; accent?: "violet" | "cyan" | "pink" | "green" | "amber" | "blue";
}) {
  const map: Record<string, { name: string; icon: any; desc: string }> = {
    coordinator: { name: "Coordinator", icon: Sparkles, desc: "Orchestrates every agent." },
    code_review: { name: "Code Review", icon: Shield, desc: "Quality, complexity, smells." },
    security: { name: "Security", icon: Lock, desc: "Vulnerabilities + CVSS scoring." },
    bug: { name: "Bug Detection", icon: AlertTriangle, desc: "Runtime, logic, performance." },
    auto_fix: { name: "Auto Fix", icon: Cpu, desc: "Generates patches + diffs." },
    documentation: { name: "Documentation", icon: Sparkles, desc: "README, API, architecture." },
    refactor: { name: "Refactoring", icon: Cpu, desc: "SOLID, design patterns." },
    test: { name: "Test Generator", icon: CheckCircle2, desc: "Pytest unit + integration." },
    uml: { name: "UML", icon: Sparkles, desc: "Class, sequence, component." },
    dependency: { name: "Dependency", icon: Shield, desc: "Vulnerabilities + upgrades." },
  };
  const conf = map[agent] || { name: agent, icon: Cpu, desc: "" };
  const Icon = conf.icon;
  const accentGrad = {
    violet: "from-violet-500/15",
    cyan: "from-cyan-500/15",
    pink: "from-pink-500/15",
    green: "from-emerald-500/15",
    amber: "from-amber-500/15",
    blue: "from-blue-500/15",
  }[accent];
  return (
    <div className={cn("relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-5")}>
      <div className={cn("absolute -top-12 -right-12 h-32 w-32 rounded-full bg-gradient-to-br to-transparent blur-2xl", accentGrad)} />
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid place-items-center h-10 w-10 rounded-xl bg-white/5 ring-1 ring-white/10">
            <Icon className="h-5 w-5 text-white/80" />
          </div>
          <div>
            <div className="font-semibold tracking-tight">{conf.name}</div>
            <div className="text-xs text-white/50">{conf.desc}</div>
          </div>
        </div>
        <AgentStatusIcon status={status} />
      </div>
      {status === "running" && (
        <div className="mt-4">
          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-violet-500 to-cyan-400"
              initial={{ width: 0 }} animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6 }}
            />
          </div>
          <div className="mt-1 text-[11px] text-white/40">{progress}% complete</div>
        </div>
      )}
      {summary && (
        <div className="mt-4 grid grid-cols-2 gap-2 text-xs text-white/60">
          {Object.entries(summary).slice(0, 4).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="text-white/40">{k}</span>
              <span className="font-medium text-white/80">{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
