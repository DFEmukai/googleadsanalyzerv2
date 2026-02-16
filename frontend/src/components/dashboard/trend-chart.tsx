"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TrendPoint } from "@/lib/types";

interface TrendChartProps {
  data: TrendPoint[];
  dataKey: keyof TrendPoint;
  title: string;
  color?: string;
  formatValue?: (value: number) => string;
}

export function TrendChart({
  data,
  dataKey,
  title,
  color = "#3B82F6",
  formatValue = (v) => v.toLocaleString(),
}: TrendChartProps) {
  const chartData = data.map((point) => ({
    ...point,
    label: point.week_start.slice(5), // MM-DD format
  }));

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-sm font-medium text-muted-foreground">
        {title}
      </h3>
      <div className="h-[200px]">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#333333"
                vertical={false}
              />
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
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
            データがありません
          </div>
        )}
      </div>
    </div>
  );
}
