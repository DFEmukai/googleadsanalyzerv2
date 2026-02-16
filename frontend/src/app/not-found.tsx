import Link from "next/link";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center">
      <div className="rounded-lg border border-gray-700 bg-[#1A1A1A] p-8 text-center shadow-lg">
        <FileQuestion className="mx-auto mb-4 h-12 w-12 text-gray-500" />
        <h2 className="mb-2 text-xl font-bold text-white">
          ページが見つかりません
        </h2>
        <p className="mb-6 text-sm text-gray-400">
          お探しのページは存在しないか、移動した可能性があります。
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          ダッシュボードに戻る
        </Link>
      </div>
    </div>
  );
}
