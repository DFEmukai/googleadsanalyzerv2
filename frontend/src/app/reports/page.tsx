"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ReportSummary } from "@/lib/types";
import { formatCurrency, formatNumber } from "@/lib/utils";
import { FileText, ChevronRight } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.reports.list(20);
        setReports(data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">週次レポート</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          全{reports.length}件のレポート
        </p>
      </div>

      {reports.length === 0 ? (
        <div className="flex h-[40vh] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card">
          <h3 className="text-lg font-medium">レポートがありません</h3>
          <p className="text-sm text-muted-foreground">
            分析を実行するとレポートが生成されます。
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => {
            const kpi = report.kpi_snapshot;
            return (
              <Link
                key={report.id}
                href={`/reports/${report.id}`}
                className="block rounded-xl border border-border bg-card p-5 transition-colors hover:bg-card-hover"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-signal-blue" />
                    <div>
                      <div className="font-medium text-white">
                        {report.week_start_date} 〜 {report.week_end_date}
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        作成日: {new Date(report.created_at).toLocaleDateString("ja-JP")}
                        {" | "}
                        提案: {report.proposals_count}件
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    {kpi && (
                      <div className="flex gap-6 text-sm">
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">費用</div>
                          <div className="tabular-nums">
                            {formatCurrency(kpi.total_cost)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">CV</div>
                          <div className="tabular-nums">
                            {formatNumber(kpi.total_conversions)}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs text-muted-foreground">CPA</div>
                          <div className="tabular-nums">
                            {formatCurrency(kpi.cpa)}
                          </div>
                        </div>
                      </div>
                    )}
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
