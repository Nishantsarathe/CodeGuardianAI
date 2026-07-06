"use client";
import * as React from "react";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button, Input, Badge } from "@/components/ui/primitives";
import { Send, Sparkles, Bot, User, MessagesSquare } from "lucide-react";
import { api } from "@/lib/api";

interface Message { id: string; role: "user" | "assistant"; content: string; }

const PROMPTS = [
  "Find SQL injection risks",
  "Suggest a refactor for this project",
  "Write pytest tests for the auth module",
];

export default function ChatPage() {
  const searchParams = useSearchParams();
  const prefillAnalysisId = searchParams.get("analysis");

  const [sessions, setSessions] = React.useState<any[]>([]);
  const [active, setActive] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [sessionsLoading, setSessLoading] = React.useState(true);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const loadSessions = React.useCallback(async () => {
    try {
      const s = await api.listSessions();
      const list = Array.isArray(s) ? s : [];
      setSessions(list);
      if (list.length && !active) setActive(list[0].id);
    } catch {}
    finally { setSessLoading(false); }
  }, [active]);

  React.useEffect(() => { loadSessions(); }, [loadSessions]);

  // Load messages when active session changes
  React.useEffect(() => {
    if (!active) { setMessages([]); return; }
    let cancelled = false;
    (async () => {
      try {
        const s = await api.getSession(active);
        if (!cancelled) setMessages(s.messages || []);
      } catch {}
    })();
    return () => { cancelled = true; };
  }, [active]);

  // Scroll to bottom on new messages
  React.useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || !active || busy) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { id: `local-${Date.now()}`, role: "user", content: text }]);
    setBusy(true);
    try {
      const r = await api.postMessage(active, text);
      // Keep the optimistic user message in place; r is the assistant reply.
      setMessages((m) => [...m, r]);
    } catch (e: any) {
      const detail = e?.message && typeof e.message === "string" ? e.message : null;
      setMessages((m) => [
        ...m,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: detail
            ? `Failed to reach the AI service: ${detail}`
            : "Failed to reach the AI service. Make sure Ollama is running.",
        },
      ]);
    } finally { setBusy(false); }
  };

  const newSession = async () => {
    try {
      const s = await api.createSession(prefillAnalysisId || undefined, "New chat");
      await loadSessions();
      setActive(s.id);
    } catch {}
  };

  return (
    <div className="grid lg:grid-cols-[300px,1fr] gap-6 h-[calc(100vh-8rem)]">
      {/* Sidebar */}
      <aside className="flex flex-col rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl overflow-hidden">
        <div className="p-4 border-b border-white/5 flex items-center justify-between flex-shrink-0">
          <div className="font-semibold flex items-center gap-2">
            <MessagesSquare className="h-4 w-4" /> Sessions
          </div>
          <Button size="sm" variant="gradient" onClick={newSession}>+ New</Button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessionsLoading && <div className="text-xs text-white/40 p-3">Loading…</div>}
          {!sessionsLoading && sessions.length === 0 && (
            <div className="text-xs text-white/40 p-3">
              No sessions yet.{" "}
              <button className="text-violet-300 hover:underline" onClick={newSession}>
                Create one
              </button>.
            </div>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActive(s.id)}
              className={`w-full text-left p-3 rounded-lg transition ${
                active === s.id
                  ? "bg-violet-500/10 border border-violet-500/30"
                  : "hover:bg-white/5"
              }`}
            >
              <div className="text-sm font-medium truncate">{s.title || "Untitled"}</div>
              <div className="text-xs text-white/40">
                {new Date(s.created_at).toLocaleString()}
              </div>
            </button>
          ))}
        </div>
      </aside>

      {/* Chat panel */}
      <Card className="flex flex-col p-0 overflow-hidden">
        <div className="p-4 border-b border-white/5 flex items-center justify-between flex-shrink-0">
          <div>
            <div className="font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-300" />
              CodeGuardian Assistant
            </div>
            <div className="text-xs text-white/40">Local LLM · grounded in your code</div>
          </div>
          <Badge color="violet">RAG-enabled</Badge>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
          {messages.length === 0 && !busy && (
            <div className="text-center text-white/50 mt-20">
              <Sparkles className="h-10 w-10 mx-auto text-violet-300 mb-3" />
              <p>Ask anything about your code, security, or architecture.</p>
              <div className="mt-4 flex flex-wrap gap-2 justify-center">
                {PROMPTS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setInput(s)}
                    className="text-xs rounded-full border border-white/10 px-3 py-1 hover:bg-white/5 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "assistant" && (
                <div className="grid place-items-center h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 flex-shrink-0 mt-1">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              <div
                className={`max-w-2xl rounded-2xl p-4 ${
                  m.role === "user"
                    ? "bg-gradient-to-br from-violet-600 to-cyan-600 text-white"
                    : "bg-white/[0.05] border border-white/10"
                }`}
              >
                <pre className="whitespace-pre-wrap text-sm font-sans leading-relaxed">{m.content}</pre>
              </div>
              {m.role === "user" && (
                <div className="grid place-items-center h-8 w-8 rounded-full bg-white/10 flex-shrink-0 mt-1">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          ))}
          {busy && (
            <div className="flex gap-3">
              <div className="grid place-items-center h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="rounded-2xl p-4 bg-white/[0.05] border border-white/10 text-white/60 text-sm animate-pulse">
                Thinking…
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-white/5 flex-shrink-0">
          <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={active ? "Ask about your code…" : "Create a session to start chatting"}
              disabled={!active || busy}
            />
            <Button type="submit" variant="gradient" disabled={!active || busy || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
