"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ReportDetail } from "@/lib/types";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  getPriorityColor,
  getStatusColor,
} from "@/lib/utils";
import {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
} from "@/lib/types";
import { ArrowLeft } from "lucide-react";

export default function ReportDetailPage() {
  const params = useParams();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.reports.get(params.id as string);
        setReport(data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    if (params.id) loadData();
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">読み込み中...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-signal-red">レポートが見つかりません</div>
      </div>
    );
  }

  const kpi = report.kpi_snapshot;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/reports"
          className="rounded-lg p-2 transition-colors hover:bg-card-hover"
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </Link>
        <div>
          <h2 className="text-xl font-bold">
            週次レポート: {report.week_start_date} 〜 {report.week_end_date}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            作成日: {new Date(report.created_at).toLocaleDateString("ja-JP")}
          </p>
        </div>
      </div>

      {/* KPI Summary */}
      {kpi && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <KPIBox label="費用" value={formatCurrency(kpi.total_cost)} />
          <KPIBox label="CV数" value={formatNumber(kpi.total_conversions)} />
          <KPIBox label="CPA" value={formatCurrency(kpi.cpa)} />
          <KPIBox label="CTR" value={formatPercent(kpi.ctr)} />
          <KPIBox label="ROAS" value={kpi.roas?.toFixed(2) || "-"} />
          <KPIBox
            label="IS"
            value={formatPercent(kpi.impression_share ? kpi.impression_share * 100 : null)}
          />
        </div>
      )}

      {/* Analysis Summary */}
      {report.analysis_summary && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="mb-3 text-sm font-medium text-muted-foreground">
            分析サマリー
          </h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-white">
            {report.analysis_summary}
          </div>
        </div>
      )}

      {/* Proposals */}
      {report.proposals.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="mb-4 text-sm font-medium text-muted-foreground">
            改善提案 ({report.proposals.length}件)
          </h3>
          <div className="space-y-3">
            {report.proposals.map((proposal) => (
              <div
                key={proposal.id}
                className="rounded-lg border border-border bg-background p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 text-xs font-medium border ${getPriorityColor(
                          proposal.priority
                        )}`}
                      >
                        {PRIORITY_LABELS[proposal.priority] || proposal.priority}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {CATEGORY_LABELS[proposal.category] || proposal.category}
                      </span>
                    </div>
                    <h4 className="mt-2 font-medium text-white">
                      {proposal.title}
                    </h4>
                    {proposal.expected_effect && (
                      <p className="mt-1 text-sm text-signal-green">
                        期待効果: {proposal.expected_effect}
                      </p>
                    )}
                    {proposal.target_campaign && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        対象: {proposal.target_campaign}
                      </p>
                    )}
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(
                      proposal.status
                    )}`}
                  >
                    {STATUS_LABELS[proposal.status] || proposal.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KPIBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-bold tabular-nums">{value}</div>
    </div>
  );
}
