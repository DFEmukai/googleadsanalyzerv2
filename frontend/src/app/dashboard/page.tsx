"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DashboardSummary, TrendData } from "@/lib/types";
import { KPICard } from "@/components/dashboard/kpi-card";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { formatCurrency, formatPercent } from "@/lib/utils";

const KPI_CONFIG = [
  { key: "total_cost", title: "費用", format: "currency" as const },
  { key: "total_conversions", title: "CV数", format: "number" as const },
  { key: "cpa", title: "CPA", format: "currency" as const },
  { key: "ctr", title: "CTR", format: "percent" as const },
  { key: "roas", title: "ROAS", format: "decimal" as const },
  { key: "impression_share", title: "インプレッションシェア", format: "percent" as const },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [summaryData, trendData] = await Promise.all([
          api.dashboard.getSummary(),
          api.dashboard.getTrends(),
        ]);
        setSummary(summaryData);
        setTrends(trendData);
      } catch (err) {
        setError("データの取得に失敗しました。バックエンドが起動しているか確認してください。");
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

  if (error) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-signal-red">{error}</div>
        <p className="text-sm text-muted-foreground">
          ヘッダーの「分析実行」ボタンから最初の分析を実行してください。
        </p>
      </div>
    );
  }

  const hasData =
    summary &&
    summary.current_week_start &&
    Object.keys(summary.kpis).length > 0;

  return (
    <div className="space-y-6">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">ダッシュボード</h2>
          {summary?.current_week_start && (
            <p className="mt-1 text-sm text-muted-foreground">
              {summary.current_week_start} 〜 {summary.current_week_end}
            </p>
          )}
        </div>
        {summary && summary.pending_proposals_count > 0 && (
          <div className="rounded-lg bg-signal-yellow/10 px-4 py-2 text-sm text-signal-yellow">
            未承認の提案: {summary.pending_proposals_count}件
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="flex h-[40vh] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card">
          <h3 className="text-lg font-medium">データがありません</h3>
          <p className="text-sm text-muted-foreground">
            ヘッダーの「分析実行」ボタンをクリックして最初の分析を実行してください。
          </p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
            {KPI_CONFIG.map(({ key, title, format }) => {
              const metric = summary.kpis[key];
              if (!metric) return null;
              return (
                <KPICard
                  key={key}
                  title={title}
                  metric={metric}
                  format={format}
                />
              );
            })}
          </div>

          {/* Trend Charts */}
          {trends && trends.trends.length > 0 && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <TrendChart
                data={trends.trends}
                dataKey="cpa"
                title="CPA推移"
                color="#EF4444"
                formatValue={(v) => formatCurrency(v)}
              />
              <TrendChart
                data={trends.trends}
                dataKey="total_conversions"
                title="CV数推移"
                color="#22C55E"
              />
              <TrendChart
                data={trends.trends}
                dataKey="total_cost"
                title="費用推移"
                color="#3B82F6"
                formatValue={(v) => formatCurrency(v)}
              />
              <TrendChart
                data={trends.trends}
                dataKey="roas"
                title="ROAS推移"
                color="#8B5CF6"
                formatValue={(v) => v.toFixed(2)}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}
