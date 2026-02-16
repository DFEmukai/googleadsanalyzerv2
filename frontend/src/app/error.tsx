"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center">
      <div className="rounded-lg border border-red-500/20 bg-[#1A1A1A] p-8 text-center shadow-lg">
        <AlertTriangle className="mx-auto mb-4 h-12 w-12 text-red-500" />
        <h2 className="mb-2 text-xl font-bold text-white">
          エラーが発生しました
        </h2>
        <p className="mb-6 text-sm text-gray-400">
          {error?.message || "予期しないエラーが発生しました。"}
        </p>
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <RefreshCw className="h-4 w-4" />
          再試行
        </button>
      </div>
    </div>
  );
}
