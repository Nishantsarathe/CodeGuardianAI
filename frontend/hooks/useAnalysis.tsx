"use client";
import * as React from "react";
import { api } from "@/lib/api";

interface AnalysisContextValue {
  projects: any[];
  analyses: Record<string, any[]>;
  refreshProjects: () => Promise<void>;
  refreshAnalyses: (projectId: string) => Promise<void>;
  currentAnalysis: any | null;
  setCurrentAnalysis: (a: any | null) => void;
  polling: boolean;
  setPolling: (b: boolean) => void;
}

const Ctx = React.createContext<AnalysisContextValue | undefined>(undefined);

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [projects, setProjects] = React.useState<any[]>([]);
  const [analyses, setAnalyses] = React.useState<Record<string, any[]>>({});
  const [currentAnalysis, setCurrentAnalysis] = React.useState<any | null>(null);
  const [polling, setPolling] = React.useState(false);

  const refreshProjects = React.useCallback(async () => {
    try {
      const list = await api.listProjects();
      setProjects(Array.isArray(list) ? list : []);
    } catch {
      // silently fail — user may not be authenticated yet
    }
  }, []);

  const refreshAnalyses = React.useCallback(async (projectId: string) => {
    try {
      const list = await api.listAnalyses(projectId);
      setAnalyses((prev) => ({ ...prev, [projectId]: Array.isArray(list) ? list : [] }));
    } catch {
      setAnalyses((prev) => ({ ...prev, [projectId]: [] }));
    }
  }, []);

  return (
    <Ctx.Provider value={{
      projects, analyses, refreshProjects, refreshAnalyses,
      currentAnalysis, setCurrentAnalysis, polling, setPolling,
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAnalysis() {
  const c = React.useContext(Ctx);
  if (!c) throw new Error("useAnalysis must be inside AnalysisProvider");
  return c;
}
