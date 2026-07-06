"use client";
import * as React from "react";
import { cn } from "@/lib/utils";

export const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "outline" | "ghost" | "destructive" | "gradient" | "secondary";
  size?: "sm" | "md" | "lg" | "icon";
}>(({ className, variant = "default", size = "md", ...rest }, ref) => {
  const base = "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/40 disabled:opacity-50 disabled:pointer-events-none whitespace-nowrap";
  const sizes = {
    sm: "h-8 px-3 text-sm",
    md: "h-10 px-4 text-sm",
    lg: "h-12 px-6 text-base",
    icon: "h-10 w-10",
  };
  const variants = {
    default: "bg-violet-600 text-white hover:bg-violet-500 shadow-lg shadow-violet-900/40",
    secondary: "bg-white/5 border border-white/10 hover:bg-white/10",
    outline: "border border-white/15 hover:bg-white/5",
    ghost: "hover:bg-white/5",
    gradient: "bg-gradient-to-r from-violet-600 to-cyan-500 text-white shadow-lg shadow-violet-900/40 hover:opacity-90",
    destructive: "bg-red-600 hover:bg-red-500 text-white",
  };
  return (
    <button
      ref={ref}
      className={cn(base, sizes[size], variants[variant], className)}
      {...rest}
    />
  );
});
Button.displayName = "Button";

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...rest }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full rounded-xl bg-black/30 border border-white/10 px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500/40",
        className
      )}
      {...rest}
    />
  )
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...rest }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "w-full rounded-xl bg-black/30 border border-white/10 px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-violet-500/40",
        className
      )}
      {...rest}
    />
  )
);
Textarea.displayName = "Textarea";

export function Label({ children, className }: { children: React.ReactNode; className?: string }) {
  return <label className={cn("text-xs uppercase tracking-wider text-white/60", className)}>{children}</label>;
}

export const Badge = ({ children, color = "violet", className }: { children: React.ReactNode; color?: "violet" | "cyan" | "pink" | "amber" | "green" | "red" | "blue" | "muted"; className?: string }) => {
  const map = {
    violet: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    cyan: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    pink: "bg-pink-500/15 text-pink-300 border-pink-500/30",
    amber: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    green: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    red: "bg-red-500/15 text-red-300 border-red-500/30",
    blue: "bg-blue-500/15 text-blue-300 border-blue-500/30",
    muted: "bg-white/5 text-white/60 border-white/10",
  };
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium", map[color], className)}>{children}</span>;
}
