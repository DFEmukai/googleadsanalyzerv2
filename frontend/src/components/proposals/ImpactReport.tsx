"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { ImpactReport as ImpactReportType, KPISnapshot, KPIChange } from "@/lib/types";
import { TrendingUp, TrendingDown, Minus, Clock, BarChart3 } from "lucide-react";

interface ImpactReportProps {
  proposalId: string;
}

const KPI_LABELS: Record<string, string> = {
  cost: "費用",
  conversions: "CV数",
  cpa: "CPA",
  ctr: "CTR",
  roas: "ROAS",
  impressions: "表示回数",
  clicks: "クリック数",
  conversion_value: "CV価値",
};

const KPI_FORMATS: Record<string, (v: number) => string> = {
  cost: (v) => `¥${v.toLocaleString()}`,
  conversions: (v) => v.toFixed(1),
  cpa: (v) => `¥${v.toLocaleString()}`,
  ctr: (v) => `${(v * 100).toFixed(2)}%`,
  roas: (v) => `${v.toFixed(2)}`,
  impressions: (v) => v.toLocaleString(),
  clicks: (v) => v.toLocaleString(),
  conversion_value: (v) => `¥${v.toLocaleString()}`,
};

// For CPA, lower is better (negative change is good)
const LOWER_IS_BETTER = ["cost", "cpa"];

function formatChange(key: string, value: number | null): { text: string; isPositive: boolean | null } {
  if (value === null) {
    return { text: "-", isPositive: null };
  }

  const sign = value > 0 ? "+" : "";
  const text = `${sign}${value.toFixed(1)}%`;

  // Determine if this change is positive (good)
  const isLowerBetter = LOWER_IS_BETTER.includes(key);
  const isPositive = isLowerBetter ? value < 0 : value > 0;

  return { text, isPositive };
}

function ChangeIndicator({ value, isPositive }: { value: string; isPositive: boolean | null }) {
  if (isPositive === null) {
    return <span className="text-gray-400">{value}</span>;
  }

  return (
    <span className={`flex items-center gap-1 font-medium ${isPositive ? "text-signal-green" : "text-signal-red"}`}>
      {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
      {value}
    </span>
  );
}

export function ImpactReport({ proposalId }: ImpactReportProps) {
  const [report, setReport] = useState<ImpactReportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (isOpen && !report) {
      loadReport();
    }
  }, [isOpen]);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.proposals.getImpact(proposalId);
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  const renderKPIRow = (
    key: string,
    before: KPISnapshot | null | undefined,
    after: KPISnapshot | null | undefined,
    change: KPIChange | null | undefined
  ) => {
    const beforeVal = before?.[key as keyof KPISnapshot];
    const afterVal = after?.[key as keyof KPISnapshot];
    const changeVal = change?.[key as keyof KPIChange];

    const format = KPI_FORMATS[key] || ((v: number) => v.toFixed(2));
    const { text: changeText, isPositive } = formatChange(key, changeVal ?? null);

    return (
      <tr key={key} className="border-b border-border last:border-0">
        <td className="py-2 text-sm text-muted-foreground">{KPI_LABELS[key]}</td>
        <td className="py-2 text-sm text-white text-right">
          {beforeVal !== null && beforeVal !== undefined ? format(beforeVal) : "-"}
        </td>
        <td className="py-2 text-sm text-white text-right">
          {afterVal !== null && afterVal !== undefined ? format(afterVal) : "-"}
        </td>
        <td className="py-2 text-sm text-right">
          <ChangeIndicator value={changeText} isPositive={isPositive} />
        </td>
      </tr>
    );
  };

  return (
    <div className="border-t border-border mt-4 pt-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm font-medium text-signal-blue hover:text-signal-blue/80"
      >
        <BarChart3 className={`h-4 w-4 transform transition-transform ${isOpen ? "rotate-90" : ""}`} />
        効果レポート
      </button>

      {isOpen && (
        <div className="mt-4 border border-border rounded-lg bg-card-hover p-4">
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground py-4">
              <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-signal-blue rounded-full"></div>
              <span className="text-sm">読み込み中...</span>
            </div>
          ) : error ? (
            <div className="text-signal-red text-sm py-2">{error}</div>
          ) : report?.status === "no_data" || report?.status === "no_before" ? (
            <div className="text-muted-foreground text-sm py-2">
              {report.message || "データがありません"}
            </div>
          ) : report?.status === "pending" ? (
            <div className="flex items-center gap-2 text-signal-yellow py-2">
              <Clock className="h-4 w-4" />
              <span className="text-sm">{report.message || "効果測定中..."}</span>
            </div>
          ) : report?.status === "available" ? (
            <>
              {/* Period info */}
              {report.period && (
                <div className="mb-4 text-xs text-muted-foreground">
                  <div>実行前: {report.period.before}</div>
                  {report.period.after && <div>実行後: {report.period.after}</div>}
                </div>
              )}

              {/* KPI comparison table */}
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 text-left text-xs font-medium text-muted-foreground">指標</th>
                    <th className="py-2 text-right text-xs font-medium text-muted-foreground">実行前</th>
                    <th className="py-2 text-right text-xs font-medium text-muted-foreground">実行後</th>
                    <th className="py-2 text-right text-xs font-medium text-muted-foreground">変化</th>
                  </tr>
                </thead>
                <tbody>
                  {["cost", "conversions", "cpa", "ctr", "roas", "clicks"].map((key) =>
                    renderKPIRow(key, report.before, report.after, report.change)
                  )}
                </tbody>
              </table>

              {/* Summary */}
              {report.change && (
                <div className="mt-4 pt-4 border-t border-border">
                  <div className="text-sm">
                    {report.change.cpa !== null && report.change.cpa < 0 && (
                      <span className="text-signal-green">
                        CPA が {Math.abs(report.change.cpa).toFixed(1)}% 改善しました
                      </span>
                    )}
                    {report.change.cpa !== null && report.change.cpa > 0 && (
                      <span className="text-signal-red">
                        CPA が {report.change.cpa.toFixed(1)}% 悪化しました
                      </span>
                    )}
                    {report.change.conversions !== null && report.change.conversions > 0 && (
                      <span className="text-signal-green ml-2">
                        (CV数 +{report.change.conversions.toFixed(1)}%)
                      </span>
                    )}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
