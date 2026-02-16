"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { Proposal, AdCopyActionSteps } from "@/lib/types";
import { getPriorityColor, getStatusColor } from "@/lib/utils";
import {
  CATEGORY_LABELS,
  PRIORITY_LABELS,
  STATUS_LABELS,
} from "@/lib/types";
import AdCopyComparison from "@/components/proposals/AdCopyComparison";
import {
  Check,
  X,
  Clock,
  ChevronDown,
  ChevronUp,
  Play,
  RotateCcw,
  Edit3,
  AlertTriangle,
  Send,
} from "lucide-react";

type FilterStatus =
  | ""
  | "pending"
  | "approved"
  | "executed"
  | "rejected"
  | "skipped";
type FilterCategory =
  | ""
  | "keyword"
  | "ad_copy"
  | "creative"
  | "manual_creative"
  | "targeting"
  | "budget"
  | "bidding"
  | "competitive_response";
type FilterPriority = "" | "high" | "medium" | "low";

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("");
  const [categoryFilter, setCategoryFilter] = useState<FilterCategory>("");
  const [priorityFilter, setPriorityFilter] = useState<FilterPriority>("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  // Approval modal state
  const [approveModalId, setApproveModalId] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [editReason, setEditReason] = useState("");

  // Reject modal state
  const [rejectModalId, setRejectModalId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  // Rollback modal state
  const [rollbackModalId, setRollbackModalId] = useState<string | null>(null);
  const [rollbackReason, setRollbackReason] = useState("");

  // Feedback
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const loadData = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (priorityFilter) params.priority = priorityFilter;
      const data = await api.proposals.list(params);
      setProposals(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [statusFilter, categoryFilter, priorityFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (feedback) {
      const timer = setTimeout(() => setFeedback(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [feedback]);

  const handleApprove = async (proposalId: string, immediate: boolean) => {
    setUpdating(proposalId);
    try {
      const result = await api.proposals.approve(proposalId, {
        schedule_at: immediate ? null : undefined,
        edited_values: editMode ? editedValues : null,
        edit_reason: editMode ? editReason : null,
      });
      setFeedback({
        type: "success",
        message: immediate
          ? `承認・反映完了: ${result.status}`
          : `承認しました（予約反映）`,
      });
      setApproveModalId(null);
      setEditMode(false);
      setEditedValues({});
      setEditReason("");
      await loadData();
    } catch (e: any) {
      setFeedback({
        type: "error",
        message: `エラー: ${e.message}`,
      });
    } finally {
      setUpdating(null);
    }
  };

  const handleReject = async (proposalId: string) => {
    setUpdating(proposalId);
    try {
      await api.proposals.reject(proposalId, {
        reason: rejectReason || null,
      });
      setFeedback({ type: "success", message: "却下しました" });
      setRejectModalId(null);
      setRejectReason("");
      await loadData();
    } catch (e: any) {
      setFeedback({ type: "error", message: `エラー: ${e.message}` });
    } finally {
      setUpdating(null);
    }
  };

  const handleSkip = async (proposalId: string) => {
    setUpdating(proposalId);
    try {
      await api.proposals.updateStatus(proposalId, "skipped");
      setFeedback({ type: "success", message: "保留しました" });
      await loadData();
    } catch (e: any) {
      setFeedback({ type: "error", message: `エラー: ${e.message}` });
    } finally {
      setUpdating(null);
    }
  };

  const handleRollback = async (proposalId: string) => {
    setUpdating(proposalId);
    try {
      await api.proposals.rollback(proposalId, {
        reason: rollbackReason,
      });
      setFeedback({
        type: "success",
        message: "ロールバックを実行しました",
      });
      setRollbackModalId(null);
      setRollbackReason("");
      await loadData();
    } catch (e: any) {
      setFeedback({ type: "error", message: `エラー: ${e.message}` });
    } finally {
      setUpdating(null);
    }
  };

  const handleExecute = async (proposalId: string) => {
    setUpdating(proposalId);
    try {
      await api.proposals.execute(proposalId, {});
      setFeedback({
        type: "success",
        message: "Google Adsへの反映を実行しました",
      });
      await loadData();
    } catch (e: any) {
      setFeedback({ type: "error", message: `エラー: ${e.message}` });
    } finally {
      setUpdating(null);
    }
  };

  const isAdCopyActionSteps = (steps: any): steps is AdCopyActionSteps => {
    return (
      steps &&
      typeof steps === "object" &&
      !Array.isArray(steps) &&
      steps.type === "ad_copy_change"
    );
  };

  const renderActionSteps = (proposal: Proposal) => {
    const steps = proposal.action_steps;
    if (!steps) return null;

    // Render ad copy comparison for ad_copy_change type
    if (isAdCopyActionSteps(steps)) {
      return (
        <div className="mb-4">
          <h4 className="mb-3 text-xs font-medium text-muted-foreground">
            広告文の比較
          </h4>
          <AdCopyComparison actionSteps={steps} />
        </div>
      );
    }

    const stepsList = Array.isArray(steps) ? steps : steps.steps || [];
    if (!Array.isArray(stepsList) || stepsList.length === 0) return null;

    return (
      <div className="mb-4">
        <h4 className="text-xs font-medium text-muted-foreground">
          実行手順
        </h4>
        <ol className="mt-2 space-y-1.5">
          {stepsList.map((step: any, idx: number) => (
            <li key={idx} className="flex gap-2 text-sm">
              <span className="font-medium text-signal-blue">
                {step.step || idx + 1}.
              </span>
              <span className="text-white">
                {step.description || String(step)}
              </span>
            </li>
          ))}
        </ol>
      </div>
    );
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
      {/* Feedback toast */}
      {feedback && (
        <div
          className={`fixed right-6 top-6 z-50 rounded-lg px-5 py-3 text-sm font-medium shadow-lg ${
            feedback.type === "success"
              ? "bg-signal-green/20 text-signal-green border border-signal-green/30"
              : "bg-signal-red/20 text-signal-red border border-signal-red/30"
          }`}
        >
          {feedback.message}
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold">改善提案</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          全{proposals.length}件の提案
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as FilterStatus)}
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
        >
          <option value="">全ステータス</option>
          <option value="pending">承認待ち</option>
          <option value="approved">承認済み</option>
          <option value="executed">実行済み</option>
          <option value="rejected">却下</option>
          <option value="skipped">スキップ</option>
        </select>

        <select
          value={categoryFilter}
          onChange={(e) =>
            setCategoryFilter(e.target.value as FilterCategory)
          }
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
        >
          <option value="">全カテゴリ</option>
          <option value="keyword">キーワード</option>
          <option value="creative">広告コピー</option>
          <option value="manual_creative">画像/動画</option>
          <option value="targeting">ターゲティング</option>
          <option value="budget">予算</option>
          <option value="bidding">入札</option>
          <option value="competitive_response">競合対応</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) =>
            setPriorityFilter(e.target.value as FilterPriority)
          }
          className="rounded-lg border border-border bg-card px-3 py-2 text-sm text-white"
        >
          <option value="">全優先度</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>

      {/* Proposals list */}
      {proposals.length === 0 ? (
        <div className="flex h-[40vh] flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card">
          <h3 className="text-lg font-medium">提案がありません</h3>
          <p className="text-sm text-muted-foreground">
            フィルタを変更するか、分析を実行してください。
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {proposals.map((proposal) => {
            const isExpanded = expandedId === proposal.id;
            return (
              <div
                key={proposal.id}
                className="rounded-xl border border-border bg-card transition-colors"
              >
                {/* Header */}
                <div
                  className="flex cursor-pointer items-start justify-between p-5"
                  onClick={() =>
                    setExpandedId(isExpanded ? null : proposal.id)
                  }
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded border px-2 py-0.5 text-xs font-medium ${getPriorityColor(
                          proposal.priority
                        )}`}
                      >
                        {PRIORITY_LABELS[proposal.priority]}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {CATEGORY_LABELS[proposal.category] || proposal.category}
                      </span>
                      {proposal.category === "manual_creative" && (
                        <span className="rounded border border-signal-yellow/30 bg-signal-yellow/10 px-2 py-0.5 text-xs font-medium text-signal-yellow">
                          手動対応
                        </span>
                      )}
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusColor(
                          proposal.status
                        )}`}
                      >
                        {STATUS_LABELS[proposal.status]}
                      </span>
                    </div>
                    <h3 className="mt-2 font-medium text-white">
                      {proposal.title}
                    </h3>
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
                  <div className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                </div>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="border-t border-border px-5 pb-5 pt-4">
                    {proposal.description && (
                      <div className="mb-4">
                        <h4 className="text-xs font-medium text-muted-foreground">
                          詳細
                        </h4>
                        <p className="mt-1 whitespace-pre-wrap text-sm text-white">
                          {proposal.description}
                        </p>
                      </div>
                    )}

                    {renderActionSteps(proposal)}

                    {/* Action buttons for pending proposals */}
                    {proposal.status === "pending" && (
                      <div className="flex flex-wrap gap-2">
                        {proposal.category !== "manual_creative" ? (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setApproveModalId(proposal.id);
                            }}
                            disabled={updating === proposal.id}
                            className="flex items-center gap-1.5 rounded-lg bg-signal-green/10 px-4 py-2 text-sm font-medium text-signal-green transition-colors hover:bg-signal-green/20 disabled:opacity-50"
                          >
                            <Check className="h-4 w-4" />
                            承認して反映
                          </button>
                        ) : (
                          <span className="flex items-center gap-1.5 rounded-lg bg-signal-yellow/10 px-4 py-2 text-sm text-signal-yellow">
                            <AlertTriangle className="h-4 w-4" />
                            Chatworkタスク登録済み・手動対応が必要
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRejectModalId(proposal.id);
                          }}
                          disabled={updating === proposal.id}
                          className="flex items-center gap-1.5 rounded-lg bg-signal-red/10 px-4 py-2 text-sm font-medium text-signal-red transition-colors hover:bg-signal-red/20 disabled:opacity-50"
                        >
                          <X className="h-4 w-4" />
                          却下
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSkip(proposal.id);
                          }}
                          disabled={updating === proposal.id}
                          className="flex items-center gap-1.5 rounded-lg bg-card px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-card-hover disabled:opacity-50"
                        >
                          <Clock className="h-4 w-4" />
                          保留
                        </button>
                      </div>
                    )}

                    {/* Action buttons for approved proposals */}
                    {proposal.status === "approved" && proposal.category !== "manual_creative" && (
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExecute(proposal.id);
                          }}
                          disabled={updating === proposal.id}
                          className="flex items-center gap-1.5 rounded-lg bg-signal-blue/10 px-4 py-2 text-sm font-medium text-signal-blue transition-colors hover:bg-signal-blue/20 disabled:opacity-50"
                        >
                          <Play className="h-4 w-4" />
                          Google Adsに反映
                        </button>
                      </div>
                    )}

                    {/* Rollback for executed proposals */}
                    {proposal.status === "executed" && (
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRollbackModalId(proposal.id);
                          }}
                          disabled={updating === proposal.id}
                          className="flex items-center gap-1.5 rounded-lg bg-signal-yellow/10 px-4 py-2 text-sm font-medium text-signal-yellow transition-colors hover:bg-signal-yellow/20 disabled:opacity-50"
                        >
                          <RotateCcw className="h-4 w-4" />
                          ロールバック
                        </button>
                        <span className="flex items-center gap-1 text-xs text-muted-foreground">
                          <AlertTriangle className="h-3 w-3" />
                          反映後24時間以内のみ
                        </span>
                      </div>
                    )}

                    <div className="mt-3 text-xs text-muted-foreground">
                      作成日:{" "}
                      {new Date(proposal.created_at).toLocaleDateString(
                        "ja-JP"
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Approve Modal */}
      {approveModalId && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/60"
          onClick={() => {
            setApproveModalId(null);
            setEditMode(false);
          }}
        >
          <div
            className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-white">提案の承認</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {proposals.find((p) => p.id === approveModalId)?.title}
            </p>

            {/* Edit toggle */}
            <button
              onClick={() => setEditMode(!editMode)}
              className="mt-4 flex items-center gap-1.5 text-sm text-signal-blue hover:underline"
            >
              <Edit3 className="h-4 w-4" />
              {editMode ? "編集をやめる" : "内容を編集して承認"}
            </button>

            {editMode && (() => {
              const modalProposal = proposals.find(
                (p) => p.id === approveModalId
              );
              const isAdCopy =
                modalProposal &&
                isAdCopyActionSteps(modalProposal.action_steps);

              return (
                <div className="mt-4 space-y-3">
                  {isAdCopy ? (
                    <div>
                      <label className="mb-2 block text-xs text-muted-foreground">
                        広告文の編集
                      </label>
                      <AdCopyComparison
                        actionSteps={
                          modalProposal.action_steps as AdCopyActionSteps
                        }
                        editable
                        onValuesChange={(values) =>
                          setEditedValues(values)
                        }
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="text-xs text-muted-foreground">
                        カテゴリ別 編集値（JSON）
                      </label>
                      <textarea
                        value={JSON.stringify(editedValues, null, 2)}
                        onChange={(e) => {
                          try {
                            setEditedValues(JSON.parse(e.target.value));
                          } catch {
                            // partial edit
                          }
                        }}
                        rows={4}
                        placeholder='例: {"new_value": 12000}'
                        className="mt-1 w-full rounded-lg border border-border bg-[#0D0D0D] px-3 py-2 text-sm text-white placeholder:text-muted-foreground"
                      />
                    </div>
                  )}
                  <div>
                    <label className="text-xs text-muted-foreground">
                      編集理由（任意）
                    </label>
                    <input
                      type="text"
                      value={editReason}
                      onChange={(e) => setEditReason(e.target.value)}
                      placeholder="例: AI提案額を控えめに調整"
                      className="mt-1 w-full rounded-lg border border-border bg-[#0D0D0D] px-3 py-2 text-sm text-white placeholder:text-muted-foreground"
                    />
                  </div>
                </div>
              );
            })()}

            <div className="mt-6 flex gap-2">
              <button
                onClick={() => handleApprove(approveModalId, true)}
                disabled={updating === approveModalId}
                className="flex items-center gap-1.5 rounded-lg bg-signal-green px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-signal-green/80 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                承認（即時反映）
              </button>
              <button
                onClick={() => handleApprove(approveModalId, false)}
                disabled={updating === approveModalId}
                className="flex items-center gap-1.5 rounded-lg border border-signal-green/30 px-4 py-2 text-sm font-medium text-signal-green transition-colors hover:bg-signal-green/10 disabled:opacity-50"
              >
                <Clock className="h-4 w-4" />
                承認のみ
              </button>
              <button
                onClick={() => {
                  setApproveModalId(null);
                  setEditMode(false);
                }}
                className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:text-white"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModalId && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/60"
          onClick={() => setRejectModalId(null)}
        >
          <div
            className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-white">提案の却下</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {proposals.find((p) => p.id === rejectModalId)?.title}
            </p>
            <div className="mt-4">
              <label className="text-xs text-muted-foreground">
                却下理由（任意）
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                placeholder="却下の理由を入力"
                className="mt-1 w-full rounded-lg border border-border bg-[#0D0D0D] px-3 py-2 text-sm text-white placeholder:text-muted-foreground"
              />
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => handleReject(rejectModalId)}
                disabled={updating === rejectModalId}
                className="rounded-lg bg-signal-red px-4 py-2 text-sm font-medium text-white hover:bg-signal-red/80 disabled:opacity-50"
              >
                却下する
              </button>
              <button
                onClick={() => setRejectModalId(null)}
                className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:text-white"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rollback Modal */}
      {rollbackModalId && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/60"
          onClick={() => setRollbackModalId(null)}
        >
          <div
            className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-bold text-white">
              ロールバック確認
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {proposals.find((p) => p.id === rollbackModalId)?.title}
            </p>
            <div className="mt-3 rounded-lg bg-signal-yellow/10 px-4 py-3 text-sm text-signal-yellow">
              <AlertTriangle className="mb-1 inline h-4 w-4" />{" "}
              この操作は反映された変更を元に戻します。
            </div>
            <div className="mt-4">
              <label className="text-xs text-muted-foreground">
                ロールバック理由
              </label>
              <textarea
                value={rollbackReason}
                onChange={(e) => setRollbackReason(e.target.value)}
                rows={2}
                placeholder="理由を入力"
                className="mt-1 w-full rounded-lg border border-border bg-[#0D0D0D] px-3 py-2 text-sm text-white placeholder:text-muted-foreground"
              />
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => handleRollback(rollbackModalId)}
                disabled={updating === rollbackModalId}
                className="rounded-lg bg-signal-yellow px-4 py-2 text-sm font-medium text-black hover:bg-signal-yellow/80 disabled:opacity-50"
              >
                ロールバック実行
              </button>
              <button
                onClick={() => setRollbackModalId(null)}
                className="rounded-lg px-4 py-2 text-sm text-muted-foreground hover:text-white"
              >
                キャンセル
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
