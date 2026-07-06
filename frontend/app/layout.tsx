import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/hooks/useAuth";
import { AnalysisProvider } from "@/hooks/useAnalysis";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "CodeGuardian AI — Autonomous Multi-Agent Code Review",
  description:
    "Next-gen multi-agent platform for code review, security, refactoring, testing, and architecture visualization.",
  authors: [{ name: "CodeGuardian AI" }],
  keywords: [
    "AI", "code review", "security", "multi-agent",
    "static analysis", "Ollama", "FastAPI", "Next.js",
  ],
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#0b0f1a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen antialiased font-sans">
        <AuthProvider>
          <AnalysisProvider>
            {children}
          </AnalysisProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
