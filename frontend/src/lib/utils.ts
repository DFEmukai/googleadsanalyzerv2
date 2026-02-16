import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "-";
  return `\u00a5${Math.round(value).toLocaleString("ja-JP")}`;
}

export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value == null) return "-";
  return `${value.toFixed(decimals)}%`;
}

export function formatNumber(value: number | null | undefined, decimals = 0): string {
  if (value == null) return "-";
  return value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function getSignalColor(signal: string): string {
  switch (signal) {
    case "green":
      return "text-signal-green";
    case "yellow":
      return "text-signal-yellow";
    case "red":
      return "text-signal-red";
    case "blue":
    default:
      return "text-signal-blue";
  }
}

export function getSignalBgColor(signal: string): string {
  switch (signal) {
    case "green":
      return "bg-signal-green";
    case "yellow":
      return "bg-signal-yellow";
    case "red":
      return "bg-signal-red";
    case "blue":
    default:
      return "bg-signal-blue";
  }
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case "high":
      return "text-signal-red bg-signal-red/10 border-signal-red/30";
    case "medium":
      return "text-signal-yellow bg-signal-yellow/10 border-signal-yellow/30";
    case "low":
      return "text-signal-blue bg-signal-blue/10 border-signal-blue/30";
    default:
      return "text-muted-foreground bg-card border-border";
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case "pending":
      return "text-signal-yellow bg-signal-yellow/10";
    case "approved":
      return "text-signal-blue bg-signal-blue/10";
    case "executed":
      return "text-signal-green bg-signal-green/10";
    case "rejected":
      return "text-signal-red bg-signal-red/10";
    case "skipped":
      return "text-muted-foreground bg-card";
    default:
      return "text-muted-foreground bg-card";
  }
}
