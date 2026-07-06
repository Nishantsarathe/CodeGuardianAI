"use client";
import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export function Progress({ value, className, color = "violet" }: { value: number; className?: string; color?: "violet" | "cyan" | "amber" | "red" }) {
  const fill = {
    violet: "from-violet-500 to-fuchsia-500",
    cyan: "from-cyan-500 to-sky-500",
    amber: "from-amber-500 to-orange-500",
    red: "from-red-500 to-rose-500",
  }[color];
  return (
    <div className={cn("relative w-full h-2 rounded-full bg-white/5 overflow-hidden", className)}>
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={cn("absolute inset-y-0 left-0 bg-gradient-to-r rounded-full", fill)}
      />
      <motion.div
        animate={{ x: ["-100%", "100%"] }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
        className="absolute inset-y-0 w-1/3 bg-white/10 mix-blend-overlay"
        style={{ left: 0 }}
      />
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span className={cn("inline-block h-4 w-4 rounded-full border-2 border-white/20 border-t-white animate-spin", className)} />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("rounded-lg bg-white/5 shimmer", className)} />;
}
