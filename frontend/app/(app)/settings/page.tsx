"use client";
import * as React from "react";
import { Card } from "@/components/ui/card";
import { Button, Input, Label, Badge } from "@/components/ui/primitives";
import { Settings as SettingsIcon, Save, Cpu, Sparkles } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { getSettings, saveSettings } from "@/lib/storage";

export default function SettingsPage() {
  const { user } = useAuth();
  const [ollamaUrl, setOllamaUrl] = React.useState("http://localhost:11434");
  const [model, setModel] = React.useState("gemma2:2b");
  const [saved, setSaved] = React.useState(false);

  const isAdmin = user?.role === "admin";
  const [users, setUsers] = React.useState<any[]>([]);
  const [usersLoading, setUsersLoading] = React.useState(false);
  const [usersError, setUsersError] = React.useState<string | null>(null);
  const [updatingId, setUpdatingId] = React.useState<string | null>(null);

  const loadUsers = React.useCallback(async () => {
    if (!isAdmin) return;
    setUsersLoading(true);
    setUsersError(null);
    try {
      const list = await api.listUsers();
      setUsers(list);
    } catch (e: any) {
      setUsersError(e?.message || "Failed to load users");
    } finally {
      setUsersLoading(false);
    }
  }, [isAdmin]);

  React.useEffect(() => { loadUsers(); }, [loadUsers]);

  const changeRole = async (userId: string, role: "admin" | "reviewer" | "viewer") => {
    setUpdatingId(userId);
    try {
      const updated = await api.updateUserRole(userId, role);
      setUsers((list) => list.map((u) => (u.id === userId ? updated : u)));
    } catch (e: any) {
      setUsersError(e?.message || "Failed to update role");
    } finally {
      setUpdatingId(null);
    }
  };

  React.useEffect(() => {
    const s = getSettings();
    setOllamaUrl(s.ollamaUrl);
    setModel(s.model);
  }, []);

  const save = () => {
    saveSettings({ ollamaUrl, model });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <header>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <SettingsIcon className="h-7 w-7 text-white/70" /> Settings
        </h1>
        <p className="text-white/60 mt-1">
          Configure your local AI backend and account preferences.
        </p>
      </header>

      <Card className="p-6 space-y-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Cpu className="h-4 w-4" /> Local LLM
        </h2>
        <div>
          <Label>Ollama base URL</Label>
          <Input value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} className="mt-1" />
        </div>
        <div>
          <Label>Default model</Label>
          <Input value={model} onChange={(e) => setModel(e.target.value)} className="mt-1" />
          <p className="text-xs text-white/40 mt-1">
            Pull a model first: <code>ollama pull {model}</code>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="gradient" onClick={save}>
            <Save className="h-4 w-4" /> Save
          </Button>
          {saved && <Badge color="green">Saved ✓</Badge>}
        </div>
      </Card>

      <Card className="p-6 space-y-3">
        <h2 className="text-lg font-semibold">Account</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <Label>Username</Label>
            <div className="mt-1 text-white/80">{user?.username}</div>
          </div>
          <div>
            <Label>Email</Label>
            <div className="mt-1 text-white/80">{user?.email}</div>
          </div>
          <div>
            <Label>Role</Label>
            <div className="mt-1"><Badge>{user?.role}</Badge></div>
          </div>
          <div>
            <Label>Member since</Label>
            <div className="mt-1 text-white/80">
              {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
            </div>
          </div>
        </div>
      </Card>

      {isAdmin && (
        <Card className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Team &amp; roles</h2>
            <Button variant="ghost" onClick={loadUsers}>Refresh</Button>
          </div>
          <p className="text-xs text-white/50 -mt-2">
            New accounts start as <code>viewer</code> (read-only) and can&apos;t
            upload or analyze projects until promoted to <code>reviewer</code>.
          </p>
          {usersError && (
            <div className="text-sm text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg px-3 py-2">
              {usersError}
            </div>
          )}
          {usersLoading ? (
            <div className="text-sm text-white/50">Loading users…</div>
          ) : (
            <div className="divide-y divide-white/10">
              {users.map((u) => (
                <div key={u.id} className="flex items-center justify-between py-3 gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white/90 truncate">
                      {u.full_name || u.username}{" "}
                      {u.id === user?.id && <span className="text-white/40">(you)</span>}
                    </div>
                    <div className="text-xs text-white/50 truncate">{u.email}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge color={u.role === "admin" ? "amber" : u.role === "reviewer" ? "cyan" : "muted"}>
                      {u.role}
                    </Badge>
                    <select
                      className="bg-white/5 border border-white/10 rounded-md text-sm px-2 py-1 text-white/80 disabled:opacity-50"
                      value={u.role}
                      disabled={updatingId === u.id}
                      onChange={(e) => changeRole(u.id, e.target.value as any)}
                    >
                      <option value="viewer">viewer</option>
                      <option value="reviewer">reviewer</option>
                      <option value="admin">admin</option>
                    </select>
                  </div>
                </div>
              ))}
              {users.length === 0 && !usersError && (
                <div className="text-sm text-white/50 py-2">No users found.</div>
              )}
            </div>
          )}
        </Card>
      )}

      <Card className="p-6">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-300" /> Tips
        </h2>
        <ul className="mt-3 text-sm text-white/60 space-y-2">
          <li>• Use larger models (7B+) for higher-quality analysis results.</li>
          <li>• Enable GPU acceleration in Ollama for 5–10× speedup.</li>
          <li>• Combine CodeGuardian with git hooks to scan on every push.</li>
          <li>• Set <code>OLLAMA_NUM_PARALLEL=2</code> to run multiple agents concurrently.</li>
        </ul>
      </Card>
    </div>
  );
}
