"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { RefreshCw } from "lucide-react";

export function Header() {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleRunAnalysis = async () => {
    setIsRunning(true);
    setMessage(null);
    try {
      const result = await api.analysis.run();
      setMessage(
        `分析完了: ${result.proposals_generated}件の提案を生成しました`
      );
      // Reload the page to show new data
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (err) {
      setMessage("分析の実行に失敗しました");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur">
      <div className="text-sm text-muted-foreground">
        Google Ads AI Agent Dashboard
      </div>
      <div className="flex items-center gap-4">
        {message && (
          <span className="text-sm text-signal-green">{message}</span>
        )}
        <button
          onClick={handleRunAnalysis}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-signal-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-signal-blue/80 disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 ${isRunning ? "animate-spin" : ""}`}
          />
          {isRunning ? "分析中..." : "分析実行"}
        </button>
      </div>
    </header>
  );
}
