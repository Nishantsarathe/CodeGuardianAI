"use client";
import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function Card({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl shadow-2xl shadow-black/20",
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("p-6 border-b border-white/5", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn("text-lg font-semibold tracking-tight", className)}>{children}</h3>;
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("p-6", className)}>{children}</div>;
}

export function Glass({ className, children, ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={cn(
        "rounded-2xl bg-white/[0.04] backdrop-blur-xl border border-white/10 shadow-2xl shadow-black/20",
        className
      )}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

export function StatCard({
  title, value, hint, icon, color = "violet",
}: { title: string; value: string | number; hint?: string; icon?: React.ReactNode; color?: "violet" | "cyan" | "pink" | "green" | "amber" }) {
  const accent = {
    violet: "from-violet-500/30 to-violet-500/0",
    cyan: "from-cyan-500/30 to-cyan-500/0",
    pink: "from-pink-500/30 to-pink-500/0",
    green: "from-emerald-500/30 to-emerald-500/0",
    amber: "from-amber-500/30 to-amber-500/0",
  }[color];
  return (
    <Card className="relative overflow-hidden">
      <div className={cn("absolute inset-0 bg-gradient-to-br", accent)} />
      <div className="relative p-6">
        <div className="flex items-center justify-between">
          <div className="text-sm text-white/60 font-medium">{title}</div>
          {icon && <div className="text-white/40">{icon}</div>}
        </div>
        <div className="mt-3 text-3xl font-bold tracking-tight">{value}</div>
        {hint && <div className="mt-1 text-xs text-white/40">{hint}</div>}
      </div>
    </Card>
  );
}
