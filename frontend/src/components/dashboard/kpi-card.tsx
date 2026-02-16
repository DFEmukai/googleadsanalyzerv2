"use client";

import { cn, formatCurrency, formatPercent, formatNumber, getSignalBgColor } from "@/lib/utils";
import { ArrowUp, ArrowDown, Minus } from "lucide-react";
import type { KPIMetric } from "@/lib/types";

interface KPICardProps {
  title: string;
  metric: KPIMetric;
  format?: "currency" | "percent" | "number" | "decimal";
  target?: number;
}

function formatValue(value: number, format: string): string {
  switch (format) {
    case "currency":
      return formatCurrency(value);
    case "percent":
      return formatPercent(value);
    case "decimal":
      return value.toFixed(2);
    case "number":
    default:
      return formatNumber(value);
  }
}

export function KPICard({ title, metric, format = "number", target }: KPICardProps) {
  const changePct = metric.change_pct;
  const isPositive = changePct != null && changePct > 0;
  const isNegative = changePct != null && changePct < 0;

  return (
    <div className="rounded-xl border border-border bg-card p-5 transition-colors hover:bg-card-hover">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{title}</span>
        <span
          className={cn(
            "h-2.5 w-2.5 rounded-full",
            getSignalBgColor(metric.signal)
          )}
        />
      </div>
      <div className="mt-2 text-2xl font-bold text-white">
        {formatValue(metric.value, format)}
      </div>
      <div className="mt-1 flex items-center gap-1">
        {changePct != null && (
          <>
            {isPositive && (
              <ArrowUp className="h-3.5 w-3.5 text-signal-green" />
            )}
            {isNegative && (
              <ArrowDown className="h-3.5 w-3.5 text-signal-red" />
            )}
            {!isPositive && !isNegative && (
              <Minus className="h-3.5 w-3.5 text-muted-foreground" />
            )}
            <span
              className={cn(
                "text-xs",
                isPositive && "text-signal-green",
                isNegative && "text-signal-red",
                !isPositive && !isNegative && "text-muted-foreground"
              )}
            >
              {isPositive ? "+" : ""}
              {changePct.toFixed(1)}% vs 先週
            </span>
          </>
        )}
      </div>
      {target != null && (
        <div className="mt-1 text-xs text-muted-foreground">
          目標: {formatValue(target, format)}
        </div>
      )}
    </div>
  );
}
