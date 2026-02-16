"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Campaign } from "@/lib/types";
import {
  cn,
  formatCurrency,
  formatPercent,
  formatNumber,
  getSignalBgColor,
} from "@/lib/utils";
import { CAMPAIGN_TYPE_LABELS } from "@/lib/types";
import { ArrowUpDown } from "lucide-react";

type SortKey = "campaign_name" | "cost" | "conversions" | "cpa" | "ctr" | "roas";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>("cost");
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await api.campaigns.list();
        setCampaigns(data);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const sorted = [...campaigns].sort((a, b) => {
    const aVal = a[sortKey] ?? 0;
    const bVal = b[sortKey] ?? 0;
    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortAsc
      ? (aVal as number) - (bVal as number)
      : (bVal as number) - (aVal as number);
  });

  const getCampaignSignal = (campaign: Campaign): string => {
    if (campaign.status !== "active") return "blue";
    if (campaign.cpa == null || campaign.cpa === 0) return "blue";
    // Simple signal logic based on CPA
    if (campaign.conversions != null && campaign.conversions > 0) return "green";
    if (campaign.cost != null && campaign.cost > 0 && (campaign.conversions ?? 0) === 0)
      return "red";
    return "yellow";
  };

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
        <h2 className="text-xl font-bold">キャンペーン一覧</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          全{campaigns.length}キャンペーン
        </p>
      </div>

      {campaigns.length === 0 ? (
        <div className="flex h-[40vh] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card">
          <h3 className="text-lg font-medium">キャンペーンデータがありません</h3>
          <p className="text-sm text-muted-foreground">
            分析を実行するとキャンペーンが表示されます。
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-card">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  ステータス
                </th>
                <SortHeader
                  label="キャンペーン名"
                  sortKey="campaign_name"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  タイプ
                </th>
                <SortHeader
                  label="費用"
                  sortKey="cost"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
                <SortHeader
                  label="CV数"
                  sortKey="conversions"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
                <SortHeader
                  label="CPA"
                  sortKey="cpa"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
                <SortHeader
                  label="CTR"
                  sortKey="ctr"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
                <SortHeader
                  label="ROAS"
                  sortKey="roas"
                  currentSort={sortKey}
                  asc={sortAsc}
                  onClick={handleSort}
                />
              </tr>
            </thead>
            <tbody>
              {sorted.map((campaign) => (
                <tr
                  key={campaign.id}
                  className="border-b border-border transition-colors hover:bg-card-hover"
                >
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-block h-2.5 w-2.5 rounded-full",
                        getSignalBgColor(getCampaignSignal(campaign))
                      )}
                    />
                  </td>
                  <td className="px-4 py-3 font-medium text-white">
                    {campaign.campaign_name}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {CAMPAIGN_TYPE_LABELS[campaign.campaign_type] ||
                      campaign.campaign_type}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatCurrency(campaign.cost)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatNumber(campaign.conversions)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatCurrency(campaign.cpa)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {formatPercent(
                      campaign.ctr != null ? campaign.ctr * 100 : null
                    )}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">
                    {campaign.roas != null ? campaign.roas.toFixed(2) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SortHeader({
  label,
  sortKey,
  currentSort,
  asc,
  onClick,
}: {
  label: string;
  sortKey: SortKey;
  currentSort: SortKey;
  asc: boolean;
  onClick: (key: SortKey) => void;
}) {
  return (
    <th
      className="cursor-pointer px-4 py-3 text-right font-medium text-muted-foreground transition-colors hover:text-white"
      onClick={() => onClick(sortKey)}
    >
      <div className="flex items-center justify-end gap-1">
        {label}
        <ArrowUpDown
          className={cn(
            "h-3.5 w-3.5",
            currentSort === sortKey ? "text-signal-blue" : "text-muted-foreground/50"
          )}
        />
      </div>
    </th>
  );
}
