"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="ja" className="dark">
      <body className="bg-[#0D0D0D] text-white antialiased">
        <div className="flex min-h-screen flex-col items-center justify-center">
          <div className="rounded-lg border border-red-500/20 bg-[#1A1A1A] p-8 text-center shadow-lg">
            <h2 className="mb-2 text-xl font-bold text-white">
              重大なエラーが発生しました
            </h2>
            <p className="mb-6 text-sm text-gray-400">
              {error?.message ||
                "アプリケーションで予期しないエラーが発生しました。"}
            </p>
            <button
              onClick={() => reset()}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
            >
              再試行
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
