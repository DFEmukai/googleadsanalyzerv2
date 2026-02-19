export type Signal = "green" | "yellow" | "red" | "blue";

export interface KPIMetric {
  value: number;
  previous: number | null;
  change_pct: number | null;
  signal: Signal;
  target?: number | null;
}

export interface DashboardSummary {
  current_week_start: string | null;
  current_week_end: string | null;
  kpis: Record<string, KPIMetric>;
  pending_proposals_count: number;
  alerts: string[];
}

export interface TrendPoint {
  week_start: string;
  total_cost: number | null;
  total_conversions: number | null;
  cpa: number | null;
  ctr: number | null;
  roas: number | null;
  impression_share: number | null;
}

export interface TrendData {
  trends: TrendPoint[];
}

export interface Campaign {
  id: string;
  campaign_id: string;
  campaign_name: string;
  campaign_type: string;
  status: string;
  first_seen_at: string;
  last_seen_at: string;
  ended_at: string | null;
  created_at: string;
  cost: number | null;
  conversions: number | null;
  cpa: number | null;
  ctr: number | null;
  clicks: number | null;
  impressions: number | null;
  roas: number | null;
}

export interface ReportSummary {
  id: string;
  week_start_date: string;
  week_end_date: string;
  created_at: string;
  kpi_snapshot: Record<string, any> | null;
  proposals_count: number;
}

export interface ProposalInReport {
  id: string;
  category: string;
  priority: string;
  title: string;
  expected_effect: string | null;
  status: string;
  target_campaign: string | null;
}

export interface ReportDetail {
  id: string;
  week_start_date: string;
  week_end_date: string;
  created_at: string;
  raw_data: Record<string, any> | null;
  analysis_summary: string | null;
  kpi_snapshot: Record<string, any> | null;
  proposals: ProposalInReport[];
}

export interface Proposal {
  id: string;
  report_id: string;
  category: string;
  priority: string;
  title: string;
  description: string | null;
  expected_effect: string | null;
  action_steps: Record<string, any> | Array<{ step: number; description: string }> | null;
  target_campaign: string | null;
  target_ad_group: string | null;
  status: string;
  created_at: string;
}

export interface AnalysisResult {
  report_id: string;
  week_start: string;
  week_end: string;
  analysis_summary: string;
  proposals_generated: number;
  status: string;
  chatwork?: {
    message_sent: boolean;
    tasks_created: number;
    errors: string[];
  } | null;
}

// Ad copy structured action_steps
export interface AdCopyCurrentAd {
  ad_id: string;
  headlines: string[];
  descriptions: string[];
  final_url: string;
}

export interface AdCopyProposedAd {
  headlines: string[];
  descriptions: string[];
  final_url: string;
}

export interface AdCopyActionSteps {
  type: "ad_copy_change";
  ad_group_id: string;
  current_ad: AdCopyCurrentAd;
  proposed_ad: AdCopyProposedAd;
  change_rationale: string[];
}

// Phase 2: Approval workflow types
export interface ApproveRequest {
  schedule_at?: string | null;
  edited_values?: Record<string, any> | null;
  edit_reason?: string | null;
  executed_by?: string;
}

export interface ApproveResponse {
  id: string;
  status: string;
  execution?: Record<string, any>;
  execution_error?: string;
  note?: string;
  scheduled_at?: string;
}

export interface RejectRequest {
  reason?: string | null;
}

export interface ExecuteRequest {
  edited_values?: Record<string, any> | null;
  execution_notes?: string;
  executed_by?: string;
}

export interface RollbackRequest {
  reason?: string;
}

export interface SafeguardCheckResponse {
  can_execute: boolean;
  warnings: string[];
  error?: string | null;
}

export interface ChatworkStatus {
  configured: boolean;
  room_id: string | null;
  has_assignee: boolean;
}

// Chat (Wall-bouncing) types
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  created_at?: string | null;
}

export interface ChatResponse {
  reply: string;
  conversation_history: ChatMessage[];
}

// Impact Report types
export interface KPISnapshot {
  cost: number | null;
  conversions: number | null;
  cpa: number | null;
  ctr: number | null;
  roas: number | null;
  impressions: number | null;
  clicks: number | null;
  conversion_value: number | null;
}

export interface KPIChange {
  cost: number | null;
  conversions: number | null;
  cpa: number | null;
  ctr: number | null;
  roas: number | null;
  impressions: number | null;
  clicks: number | null;
  conversion_value: number | null;
}

export interface ImpactPeriod {
  before: string;
  after?: string | null;
}

export interface ImpactReport {
  status: "available" | "pending" | "no_data" | "no_before";
  before?: KPISnapshot | null;
  after?: KPISnapshot | null;
  change?: KPIChange | null;
  period?: ImpactPeriod | null;
  message?: string | null;
}

// Labels
export const CATEGORY_LABELS: Record<string, string> = {
  keyword: "キーワード",
  ad_copy: "広告コピー",
  creative: "広告コピー",
  manual_creative: "画像/動画",
  targeting: "ターゲティング",
  budget: "予算",
  bidding: "入札",
  competitive_response: "競合対応",
};

export const PRIORITY_LABELS: Record<string, string> = {
  high: "高",
  medium: "中",
  low: "低",
};

export const STATUS_LABELS: Record<string, string> = {
  pending: "承認待ち",
  approved: "承認済み",
  executed: "実行済み",
  rejected: "却下",
  skipped: "スキップ",
};

export const CAMPAIGN_TYPE_LABELS: Record<string, string> = {
  search: "検索",
  display: "ディスプレイ",
  pmax: "P-MAX",
  video: "動画",
};
