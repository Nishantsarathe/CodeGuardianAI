"use client";
import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button, Input, Label, Badge } from "@/components/ui/primitives";
import { Card } from "@/components/ui/card";
import { Shield, ArrowRight, Mail, Lock, User, LogIn, UserPlus, Sparkles } from "lucide-react";

export default function LoginPage() {
  const { login, register } = useAuth();
  const router = useRouter();
  const [mode, setMode] = React.useState<"login" | "register">("login");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [username, setUsername] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null); setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register({ email, username, password, full_name: fullName });
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Authentication failed");
    } finally { setBusy(false); }
  };

  return (
    <main className="min-h-screen grid lg:grid-cols-2">
      <div className="relative hidden lg:flex items-center justify-center p-12 overflow-hidden">
        <div className="absolute -top-40 -left-32 h-96 w-96 rounded-full bg-violet-600/30 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="relative max-w-md">
          <Link href="/" className="flex items-center gap-2 mb-10">
            <div className="grid place-items-center h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-900/50">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="font-bold tracking-tight">CodeGuardian</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-white/40">AI</div>
            </div>
          </Link>
          <h1 className="text-4xl font-bold tracking-tight">Welcome back.</h1>
          <p className="mt-3 text-white/60">Sign in to analyze repositories, chat with the AI assistant, and download reports.</p>
          <ul className="mt-8 space-y-3 text-sm text-white/70">
            <li className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-violet-300" /> 10 autonomous AI agents</li>
            <li className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-cyan-300" /> 100% local-first (Ollama)</li>
            <li className="flex items-center gap-2"><Sparkles className="h-4 w-4 text-pink-300" /> Production-grade reports</li>
          </ul>
        </div>
      </div>

      <div className="flex items-center justify-center p-6 lg:p-12">
        <Card className="w-full max-w-md p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold tracking-tight">
              {mode === "login" ? "Sign in" : "Create account"}
            </h2>
            <Badge color={mode === "login" ? "cyan" : "violet"}>
              {mode === "login" ? <LogIn className="h-3 w-3 mr-1" /> : <UserPlus className="h-3 w-3 mr-1" />}
              {mode === "login" ? "Login" : "Sign up"}
            </Badge>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <div className="space-y-1.5">
                <Label>Username</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
                  <Input className="pl-9" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
                </div>
              </div>
            )}
            <div className="space-y-1.5">
              <Label>Email or username</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
                <Input className="pl-9" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
                <Input type="password" className="pl-9" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete="current-password" />
              </div>
            </div>
            {mode === "register" && (
              <div className="space-y-1.5">
                <Label>Full name (optional)</Label>
                <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                {error}
              </div>
            )}

            <Button type="submit" variant="gradient" className="w-full" disabled={busy}>
              {busy ? "Working..." : (mode === "login" ? "Sign in" : "Create account")}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-white/50">
            {mode === "login" ? (
              <>New here? <button className="text-violet-300 hover:underline" onClick={() => setMode("register")}>Create an account</button></>
            ) : (
              <>Already have an account? <button className="text-violet-300 hover:underline" onClick={() => setMode("login")}>Sign in</button></>
            )}
          </div>

          {mode === "login" && (
            <div className="mt-4 rounded-lg border border-white/5 bg-white/5 p-3 text-xs text-white/50">
              <strong>Demo:</strong> Use the credentials printed to the server log on first startup,
              or set <code>DEMO_ADMIN_PASSWORD</code> in your <code>.env</code> file.
            </div>
          )}
        </Card>
      </div>
    </main>
  );
}
