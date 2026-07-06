"use client";
import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  Shield, LayoutDashboard, Upload, FileSearch, Lock, Bug, FileText,
  Network, Package, MessagesSquare, Settings, LogOut, Sparkles, BookOpen,
  FileBarChart,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard",    label: "Dashboard",    icon: LayoutDashboard },
  { href: "/upload",       label: "Upload",       icon: Upload },
  { href: "/analysis",     label: "Analysis",     icon: FileSearch },
  { href: "/security",     label: "Security",     icon: Lock },
  { href: "/bugs",         label: "Bugs",         icon: Bug },
  { href: "/docs",         label: "Docs",         icon: BookOpen },
  { href: "/architecture", label: "Architecture", icon: Network },
  { href: "/dependencies", label: "Dependencies", icon: Package },
  { href: "/reports",      label: "Reports",      icon: FileBarChart },
  { href: "/chat",         label: "AI Chat",      icon: MessagesSquare },
  { href: "/settings",     label: "Settings",     icon: Settings },
];

function NavRail() {
  const pathname = usePathname();
  return (
    <nav className="mt-6 space-y-0.5 flex-1 overflow-y-auto pr-1">
      {NAV.map((n) => {
        const active =
          pathname === n.href || (n.href !== "/dashboard" && pathname?.startsWith(n.href + "/"));
        return (
          <Link
            key={n.href}
            href={n.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
              active
                ? "bg-gradient-to-r from-violet-500/20 to-cyan-500/10 text-white shadow-sm ring-1 ring-white/10"
                : "text-white/55 hover:text-white hover:bg-white/[0.06]"
            )}
          >
            <n.icon
              className={cn("h-4 w-4 flex-shrink-0 transition-colors", active ? "text-violet-300" : "text-current")}
            />
            <span className="flex-1">{n.label}</span>
            {active && (
              <span className="h-1.5 w-1.5 rounded-full bg-violet-400 flex-shrink-0" />
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = React.useState(false);

  // Close mobile sidebar on route change
  React.useEffect(() => { setOpen(false); }, [pathname]);

  // Redirect to login if unauthenticated
  React.useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center text-white/60">
        <div className="flex items-center gap-3">
          <Sparkles className="h-5 w-5 animate-pulse text-violet-300" />
          Loading CodeGuardian…
        </div>
      </div>
    );
  }

  if (!user) return null;

  const SidebarContent = (
    <div className="h-full p-4 flex flex-col">
      {/* Logo */}
      <Link href="/dashboard" className="flex items-center gap-2.5 px-3 py-2">
        <div className="grid place-items-center h-9 w-9 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-900/50 flex-shrink-0">
          <Shield className="h-4 w-4 text-white" />
        </div>
        <div>
          <div className="font-bold tracking-tight text-sm leading-none">CodeGuardian</div>
          <div className="text-[9px] uppercase tracking-[0.2em] text-white/35 mt-0.5">AI · v1.0</div>
        </div>
      </Link>

      <NavRail />

      {/* User footer */}
      <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.04] p-3.5">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 grid place-items-center text-sm font-semibold flex-shrink-0 select-none">
            {(user.username?.[0] || "U").toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold truncate leading-none">
              {user.full_name || user.username}
            </div>
            <div className="text-[11px] text-white/40 truncate mt-0.5">{user.email}</div>
          </div>
          <button
            onClick={() => { logout(); router.push("/login"); }}
            className="h-7 w-7 grid place-items-center rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="mt-2.5 text-[9px] uppercase tracking-widest text-white/25">
          Role: {user.role || "viewer"}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-72 flex-col flex-shrink-0 border-r border-white/5">
        {SidebarContent}
      </aside>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {open && (
          <>
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
              onClick={() => setOpen(false)}
            />
            <motion.aside
              key="sidebar"
              initial={{ x: -288 }}
              animate={{ x: 0 }}
              exit={{ x: -288 }}
              transition={{ type: "spring", damping: 30, stiffness: 350 }}
              className="fixed inset-y-0 left-0 z-40 w-72 border-r border-white/10 bg-[#0b0f1a]/95 backdrop-blur-2xl lg:hidden"
            >
              {SidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col">
        {/* Mobile topbar */}
        <header className="sticky top-0 z-20 backdrop-blur-xl bg-black/30 border-b border-white/5 lg:hidden flex-shrink-0">
          <div className="flex items-center justify-between px-4 py-3">
            <button
              onClick={() => setOpen(true)}
              className="h-9 w-9 grid place-items-center rounded-lg text-white/70 hover:bg-white/10 transition"
              aria-label="Open sidebar"
            >
              <span className="text-lg leading-none">☰</span>
            </button>
            <div className="font-semibold text-sm">CodeGuardian</div>
            <div className="w-9" />
          </div>
        </header>

        <div className="flex-1 p-4 md:p-8 max-w-[1400px] mx-auto w-full">
          {children}
        </div>
      </main>
    </div>
  );
}
