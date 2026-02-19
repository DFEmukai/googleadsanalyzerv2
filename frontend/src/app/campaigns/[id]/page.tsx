"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { CampaignDashboard, CampaignTrendPoint } from "@/lib/types";
import { CAMPAIGN_TYPE_LABELS, CATEGORY_LABELS, PRIORITY_LABELS, STATUS_LABELS } from "@/lib/types";
import {
  cn,
  formatCurrency,
  formatPercent,
  formatNumber,
  getSignalBgColor,
  getPriorityColor,
  getStatusColor,
} from "@/lib/utils";
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Target,
  MousePointer,
  Eye,
  BarChart3,
  Percent,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function CampaignDashboardPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params.id as string;

  const [dashboard, setDashboard] = useState<CampaignDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await api.campaigns.getDashboard(campaignId, days);
        setDashboard(data);
        setError(null);
      } catch (err) {
        setError("データの取得に失敗しました");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [campaignId, days]);

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">読み込み中...</div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="flex h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-red-500">{error || "キャンペーンが見つかりません"}</p>
        <button
          onClick={() => router.push("/campaigns")}
          className="flex items-center gap-2 text-signal-blue hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          キャンペーン一覧に戻る
        </button>
      </div>
    );
  }

  const { campaign, summary, trends, period, proposals } = dashboard;

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      active: "bg-signal-green/20 text-signal-green",
      paused: "bg-signal-yellow/20 text-signal-yellow",
      ended: "bg-muted text-muted-foreground",
    };
    const statusLabels: Record<string, string> = {
      active: "有効",
      paused: "停止中",
      ended: "終了",
    };
    return (
      <span className={cn("rounded-full px-2 py-0.5 text-xs", statusColors[status] || statusColors.ended)}>
        {statusLabels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => router.push("/campaigns")}
            className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            キャンペーン一覧
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{campaign.name}</h1>
            {getStatusBadge(campaign.status)}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            {CAMPAIGN_TYPE_LABELS[campaign.type] || campaign.type} | 期間: {period.start} 〜 {period.end}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
          >
            <option value={7}>過去7日</option>
            <option value={14}>過去14日</option>
            <option value={30}>過去30日</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <KPICard
          title="費用"
          value={summary.cost}
          format="currency"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <KPICard
          title="CV数"
          value={summary.conversions}
          format="number"
          icon={<Target className="h-4 w-4" />}
        />
        <KPICard
          title="CPA"
          value={summary.cpa}
          format="currency"
          icon={<BarChart3 className="h-4 w-4" />}
        />
        <KPICard
          title="CTR"
          value={summary.ctr * 100}
          format="percent"
          icon={<MousePointer className="h-4 w-4" />}
        />
        <KPICard
          title="ROAS"
          value={summary.roas}
          format="decimal"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <KPICard
          title="インプレッション"
          value={summary.impressions}
          format="number"
          icon={<Eye className="h-4 w-4" />}
        />
      </div>

      {/* Trend Charts */}
      {trends.length > 0 ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <TrendChartCard
            title="CPA推移"
            data={trends}
            dataKey="cpa"
            color="#F59E0B"
            formatValue={(v) => `¥${v.toLocaleString()}`}
          />
          <TrendChartCard
            title="CV数推移"
            data={trends}
            dataKey="conversions"
            color="#10B981"
            formatValue={(v) => v.toLocaleString()}
          />
          <TrendChartCard
            title="費用推移"
            data={trends}
            dataKey="cost"
            color="#3B82F6"
            formatValue={(v) => `¥${v.toLocaleString()}`}
          />
          <TrendChartCard
            title="ROAS推移"
            data={trends}
            dataKey="roas"
            color="#8B5CF6"
            formatValue={(v) => v.toFixed(2)}
          />
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-8 text-center">
          <p className="text-muted-foreground">トレンドデータがありません</p>
        </div>
      )}

      {/* Related Proposals */}
      <div className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-4">
          <h2 className="font-medium text-white">関連する改善提案</h2>
        </div>
        {proposals.length > 0 ? (
          <div className="divide-y divide-border">
            {proposals.map((proposal) => (
              <Link
                key={proposal.id}
                href={`/proposals?id=${proposal.id}`}
                className="flex items-center justify-between px-5 py-4 transition-colors hover:bg-card-hover"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.5 text-xs",
                        getPriorityColor(proposal.priority)
                      )}
                    >
                      {PRIORITY_LABELS[proposal.priority] || proposal.priority}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {CATEGORY_LABELS[proposal.category] || proposal.category}
                    </span>
                  </div>
                  <p className="mt-1 font-medium text-white">{proposal.title}</p>
                  {proposal.expected_effect && (
                    <p className="mt-0.5 text-sm text-muted-foreground">
                      期待効果: {proposal.expected_effect}
                    </p>
                  )}
                </div>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs",
                    getStatusColor(proposal.status)
                  )}
                >
                  {STATUS_LABELS[proposal.status] || proposal.status}
                </span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="px-5 py-8 text-center text-muted-foreground">
            このキャンペーンに関連する改善提案はありません
          </div>
        )}
      </div>
    </div>
  );
}

function KPICard({
  title,
  value,
  format,
  icon,
}: {
  title: string;
  value: number;
  format: "currency" | "percent" | "number" | "decimal";
  icon: React.ReactNode;
}) {
  const formatValue = (val: number) => {
    switch (format) {
      case "currency":
        return `¥${val.toLocaleString()}`;
      case "percent":
        return `${val.toFixed(2)}%`;
      case "decimal":
        return val.toFixed(2);
      default:
        return val.toLocaleString();
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card p-4 transition-colors hover:bg-card-hover">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span className="text-sm">{title}</span>
      </div>
      <div className="mt-2 text-xl font-bold text-white">{formatValue(value)}</div>
    </div>
  );
}

function TrendChartCard({
  title,
  data,
  dataKey,
  color,
  formatValue,
}: {
  title: string;
  data: CampaignTrendPoint[];
  dataKey: keyof CampaignTrendPoint;
  color: string;
  formatValue: (value: number) => string;
}) {
  const chartData = data.map((point) => ({
    ...point,
    label: point.date.slice(5), // MM-DD format
  }));

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333333" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#A0A0A0", fontSize: 12 }}
              axisLine={{ stroke: "#333333" }}
            />
            <YAxis
              tick={{ fill: "#A0A0A0", fontSize: 12 }}
              axisLine={{ stroke: "#333333" }}
              tickFormatter={formatValue}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1A1A1A",
                border: "1px solid #333333",
                borderRadius: "8px",
                color: "#FFFFFF",
              }}
              formatter={(value: number) => [formatValue(value), title]}
              labelStyle={{ color: "#A0A0A0" }}
            />
            <Line
              type="monotone"
              dataKey={dataKey as string}
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
