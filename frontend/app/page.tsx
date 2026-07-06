"use client";
import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Shield, Cpu, Lock, Bug, FileText, GitBranch, Package, BookOpen,
         ArrowRight, CheckCircle2, Sparkles, Zap, Github, ServerCog, Network, Wand2,
         Code2, TestTube2, Boxes, MessagesSquare, FileBarChart } from "lucide-react";
import { Button, Badge } from "@/components/ui/primitives";
import { Card } from "@/components/ui/card";

const AGENTS = [
  { name: "Coordinator",   icon: Sparkles,  desc: "Plans, delegates, and merges agent results." },
  { name: "Code Review",   icon: Shield,    desc: "Quality, complexity, smells, duplication." },
  { name: "Security",      icon: Lock,      desc: "SQLi, XSS, CVSS scoring, secret scanning." },
  { name: "Bug Detection", icon: Bug,       desc: "Runtime, logic, async, performance issues." },
  { name: "Auto Fix",      icon: Wand2,     desc: "Patches and safe fixes with diff view." },
  { name: "Documentation", icon: BookOpen,  desc: "README, API, architecture, dev guides." },
  { name: "Refactoring",   icon: Cpu,       desc: "SOLID, design patterns, modularization." },
  { name: "Test Generator",icon: TestTube2, desc: "Pytest unit + integration + edge cases." },
  { name: "UML",           icon: Boxes,     desc: "Class, sequence, component diagrams." },
  { name: "Dependency",    icon: Package,   desc: "Vulnerable & outdated packages." },
];

const FEATURES = [
  { icon: Network, title: "10 Autonomous AI Agents", desc: "A multi-agent runtime built for production, not toys." },
  { icon: Lock, title: "Local-First AI", desc: "Runs on Ollama. Your code never leaves your machine." },
  { icon: Shield, title: "OWASP-grade Security", desc: "CWE mapping, CVSS scores, secret detection, dep audit." },
  { icon: FileBarChart, title: "Audit-grade Reports", desc: "Markdown, HTML, PDF and machine-readable JSON." },
  { icon: ServerCog, title: "Production Backend", desc: "FastAPI, SQLAlchemy, ChromaDB, RBAC, rate limiting, audit log." },
  { icon: Github, title: "Repo Anywhere", desc: "GitHub URL, ZIP, folder or single file." },
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      {/* Decorative orbs */}
      <div className="pointer-events-none absolute -top-40 -left-32 h-96 w-96 rounded-full bg-violet-600/30 blur-3xl" />
      <div className="pointer-events-none absolute top-32 right-0 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 left-1/2 h-[28rem] w-[28rem] rounded-full bg-pink-500/10 blur-3xl -translate-x-1/2" />

      {/* Nav */}
      <header className="relative z-10 flex items-center justify-between px-8 py-6">
        <Link href="/" className="flex items-center gap-2">
          <div className="grid place-items-center h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-900/50">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-bold tracking-tight">CodeGuardian</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/40">AI</div>
          </div>
        </Link>
        <nav className="hidden md:flex items-center gap-1 text-sm">
          <Link href="#features" className="px-3 py-2 text-white/70 hover:text-white">Features</Link>
          <Link href="#agents" className="px-3 py-2 text-white/70 hover:text-white">Agents</Link>
          <Link href="#workflow" className="px-3 py-2 text-white/70 hover:text-white">Workflow</Link>
          <Link href="#stack" className="px-3 py-2 text-white/70 hover:text-white">Stack</Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link href="/login"><Button variant="ghost" size="sm">Sign in</Button></Link>
          <Link href="/dashboard"><Button size="sm" variant="gradient">Open Dashboard <ArrowRight className="h-4 w-4" /></Button></Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative z-10 px-8 py-20 text-center max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 mb-6"
        >
          <Badge color="violet"><Sparkles className="h-3 w-3 mr-1" /> KAGGLE AI AGENTS — CAPSTONE 2026</Badge>
        </motion.div>
        <motion.h1
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
          className="text-5xl md:text-7xl font-bold tracking-tight"
        >
          Autonomous code review,<br />
          <span className="gradient-text">staff-engineer grade.</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.2 }}
          className="mt-6 text-lg text-white/60 max-w-3xl mx-auto"
        >
          Ten AI agents collaborate through a Coordinator to find bugs, fix vulnerabilities, generate tests,
          refactor code, and document your project — running <span className="text-white">100% locally</span> on Ollama.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}
          className="mt-10 flex items-center justify-center gap-3"
        >
          <Link href="/dashboard"><Button size="lg" variant="gradient">Get started <ArrowRight className="h-5 w-5" /></Button></Link>
          <Link href="/upload"><Button size="lg" variant="outline">Upload a repo</Button></Link>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 1 }}
          className="mt-10 flex items-center justify-center gap-6 text-xs text-white/40"
        >
          <span className="flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Free, MIT licensed</span>
          <span className="flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Local Ollama</span>
          <span className="flex items-center gap-1"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Production-grade</span>
        </motion.div>
      </section>

      {/* Mock terminal */}
      <section className="relative z-10 px-6 pb-20">
        <div className="mx-auto max-w-5xl rounded-2xl border border-white/10 bg-black/40 backdrop-blur-2xl shadow-2xl overflow-hidden">
          <div className="flex items-center gap-2 border-b border-white/5 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-red-500/80" />
            <span className="h-3 w-3 rounded-full bg-amber-500/80" />
            <span className="h-3 w-3 rounded-full bg-emerald-500/80" />
            <span className="ml-3 text-xs text-white/40">codeguardian — analysis · main</span>
          </div>
          <pre className="p-6 text-sm leading-relaxed text-white/80 font-mono overflow-x-auto">
{`$ codeguardian analyze ./acme-saas
✔ Coordinator    plan: 9 agents, 4 in parallel
✔ Code Review    score 87/100  findings 12
✔ Security       score 92/100  critical 0 high 1
✔ Bug Detection  score 84/100  bugs 4
✔ Auto Fix       patches 3
✔ Documentation  README + API + ARCH generated
✔ Refactoring    6 SOLID-aligned suggestions
✔ Tests          pytest suite (32 tests)
✔ UML            class, sequence, component
✔ Dependency     2 outdated, 1 vulnerability
✔ Health score   88/100  (A+)`}
          </pre>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 px-8 py-20 max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-center">
          Built like a <span className="gradient-text">staff engineer</span>, scales like infrastructure.
        </h2>
        <p className="mt-4 text-center text-white/60 max-w-2xl mx-auto">
          Hardened for thousands of developers — JWT, RBAC, audit logs, rate limiting, and
          modular Clean Architecture on the inside.
        </p>
        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="p-6 hover:border-violet-500/30 transition-colors">
              <div className="grid place-items-center h-11 w-11 rounded-xl bg-gradient-to-br from-violet-500/20 to-cyan-500/10 mb-4">
                <f.icon className="h-5 w-5 text-violet-300" />
              </div>
              <h3 className="text-lg font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-white/60">{f.desc}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Agents */}
      <section id="agents" className="relative z-10 px-8 py-20 max-w-7xl mx-auto">
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-center">
          Meet the <span className="gradient-text">10 agents</span>.
        </h2>
        <p className="mt-4 text-center text-white/60 max-w-2xl mx-auto">
          Each agent is an independent module. The Coordinator composes their outputs into a single,
          validated analysis.
        </p>
        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {AGENTS.map((a, i) => (
            <motion.div
              key={a.name}
              initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.5 }}
              viewport={{ once: true }}
            >
              <Card className="p-5 h-full">
                <div className="flex items-center gap-3">
                  <div className="grid place-items-center h-10 w-10 rounded-xl bg-white/5 ring-1 ring-white/10">
                    <a.icon className="h-5 w-5 text-white/80" />
                  </div>
                  <div>
                    <div className="font-semibold">{a.name}</div>
                    <div className="text-xs text-white/50">Agent</div>
                  </div>
                </div>
                <p className="mt-3 text-sm text-white/60">{a.desc}</p>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Workflow */}
      <section id="workflow" className="relative z-10 px-8 py-20 max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-center">
          From upload to insight in <span className="gradient-text">minutes</span>.
        </h2>
        <div className="mt-12 grid gap-4 md:grid-cols-5">
          {[
            { t: "Upload", d: "GitHub, ZIP, folder or single file." },
            { t: "Plan",   d: "Coordinator creates an execution plan." },
            { t: "Analyze",d: "All agents run in sequence, validated continuously." },
            { t: "Merge",  d: "Findings are normalized, scored, deduped." },
            { t: "Report", d: "Download MD / HTML / PDF / patch." },
          ].map((s, i) => (
            <Card key={s.t} className="p-5 text-center">
              <div className="text-xs text-white/40">Step {i+1}</div>
              <div className="mt-1 font-semibold">{s.t}</div>
              <p className="mt-2 text-sm text-white/60">{s.d}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* Stack */}
      <section id="stack" className="relative z-10 px-8 py-20 max-w-6xl mx-auto">
        <h2 className="text-3xl md:text-5xl font-bold tracking-tight text-center">
          A <span className="gradient-text">production</span> stack.
        </h2>
        <div className="mt-12 grid gap-4 md:grid-cols-3">
          {[
            { t: "Frontend",  d: "Next.js 15, React, TypeScript, Tailwind, ShadCN, Framer Motion, Recharts, Monaco." },
            { t: "Backend",   d: "Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, ChromaDB, ReportLab, Ollama." },
            { t: "AI",        d: "Google ADK-compatible runtime, Ollama (Gemma 2 / Qwen 2.5 Coder), local-first." },
            { t: "Database",  d: "SQLite for relational data, ChromaDB for vector embeddings." },
            { t: "Security",  d: "JWT, RBAC, rate limiting, audit log, PII redaction, safe uploads." },
            { t: "Deploy",    d: "Docker + Docker Compose. One command, fully working." },
          ].map((s) => (
            <Card key={s.t} className="p-5">
              <div className="font-semibold">{s.t}</div>
              <p className="mt-2 text-sm text-white/60">{s.d}</p>
            </Card>
          ))}
        </div>
      </section>

      <footer className="relative z-10 px-8 py-10 text-center text-xs text-white/40 border-t border-white/5">
        © 2026 CodeGuardian AI — Built for the Kaggle AI Agents Intensive — MIT License
      </footer>
    </main>
  );
}
