import type {
  DashboardSummary,
  TrendData,
  Campaign,
  CampaignDashboard,
  ReportSummary,
  ReportDetail,
  Proposal,
  AnalysisResult,
  ApproveRequest,
  ApproveResponse,
  RejectRequest,
  ExecuteRequest,
  RollbackRequest,
  SafeguardCheckResponse,
  ChatworkStatus,
  ChatMessage,
  ChatResponse,
  ImpactReport,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const errorBody = await res.text().catch(() => "");
    throw new Error(
      `API Error: ${res.status} ${res.statusText}${errorBody ? ` - ${errorBody}` : ""}`
    );
  }
  return res.json();
}

export const api = {
  dashboard: {
    getSummary: () => fetchAPI<DashboardSummary>("/dashboard/summary"),
    getTrends: (weeks = 8) =>
      fetchAPI<TrendData>(`/dashboard/trends?weeks=${weeks}`),
  },
  campaigns: {
    list: (params?: { status?: string; sort_by?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set("status", params.status);
      if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
      const qs = searchParams.toString();
      return fetchAPI<Campaign[]>(`/campaigns${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => fetchAPI<Campaign>(`/campaigns/${id}`),
    getDashboard: (id: string, days = 7) =>
      fetchAPI<CampaignDashboard>(`/campaigns/${id}/dashboard?days=${days}`),
  },
  reports: {
    list: (limit = 10) =>
      fetchAPI<ReportSummary[]>(`/reports?limit=${limit}`),
    get: (id: string) => fetchAPI<ReportDetail>(`/reports/${id}`),
    latest: () => fetchAPI<ReportDetail>("/reports/latest"),
  },
  proposals: {
    list: (params?: {
      status?: string;
      category?: string;
      priority?: string;
    }) => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.set("status", params.status);
      if (params?.category) searchParams.set("category", params.category);
      if (params?.priority) searchParams.set("priority", params.priority);
      const qs = searchParams.toString();
      return fetchAPI<Proposal[]>(`/proposals${qs ? `?${qs}` : ""}`);
    },
    get: (id: string) => fetchAPI<Proposal>(`/proposals/${id}`),
    updateStatus: (id: string, status: string) =>
      fetchAPI<{ id: string; status: string }>(`/proposals/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    approve: (id: string, data: ApproveRequest) =>
      fetchAPI<ApproveResponse>(`/proposals/${id}/approve`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    reject: (id: string, data: RejectRequest) =>
      fetchAPI<{ id: string; status: string; reason?: string }>(
        `/proposals/${id}/reject`,
        {
          method: "POST",
          body: JSON.stringify(data),
        }
      ),
    execute: (id: string, data: ExecuteRequest) =>
      fetchAPI<Record<string, unknown>>(`/proposals/${id}/execute`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    rollback: (id: string, data: RollbackRequest) =>
      fetchAPI<Record<string, unknown>>(`/proposals/${id}/rollback`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    checkSafeguards: (id: string, editedValues?: Record<string, unknown>) =>
      fetchAPI<SafeguardCheckResponse>(
        `/proposals/${id}/safeguard-check`,
        {
          method: "POST",
          body: JSON.stringify(editedValues || {}),
        }
      ),
    chat: (id: string, message: string) =>
      fetchAPI<ChatResponse>(`/proposals/${id}/chat`, {
        method: "POST",
        body: JSON.stringify({ message }),
      }),
    getChatHistory: (id: string) =>
      fetchAPI<{ conversation_history: ChatMessage[] }>(
        `/proposals/${id}/chat/history`
      ),
    getImpact: (id: string) =>
      fetchAPI<ImpactReport>(`/proposals/${id}/impact`),
  },
  analysis: {
    run: () =>
      fetchAPI<AnalysisResult>("/analysis/run", { method: "POST" }),
  },
  chatwork: {
    status: () => fetchAPI<ChatworkStatus>("/chatwork/status"),
    test: (message?: string) =>
      fetchAPI<{ status: string }>("/chatwork/test", {
        method: "POST",
        body: JSON.stringify({ message: message || undefined }),
      }),
    notifyReport: (reportId: string) =>
      fetchAPI<Record<string, unknown>>(`/chatwork/notify/${reportId}`, {
        method: "POST",
      }),
  },
  health: () =>
    fetchAPI<{ status: string; version: string; next_scheduled_analysis?: string }>(
      "/health"
    ),
};
