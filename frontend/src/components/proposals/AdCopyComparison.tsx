"use client";

import { useState } from "react";
import type { AdCopyActionSteps } from "@/lib/types";
import { Plus, Trash2, ArrowRight } from "lucide-react";

const HEADLINE_MAX = 30;
const DESCRIPTION_MAX = 90;

interface AdCopyComparisonProps {
  actionSteps: AdCopyActionSteps;
  editable?: boolean;
  onValuesChange?: (values: {
    ad_group_id: string;
    headlines: string[];
    descriptions: string[];
    final_url: string;
    old_ad_id?: string;
  }) => void;
}

function CharCount({
  current,
  max,
}: {
  current: number;
  max: number;
}) {
  const isOver = current > max;
  const isNear = current > max - 3 && !isOver;
  return (
    <span
      className={`ml-1 text-xs tabular-nums ${
        isOver
          ? "text-signal-red font-medium"
          : isNear
          ? "text-signal-yellow"
          : "text-muted-foreground"
      }`}
    >
      {current}/{max}
    </span>
  );
}

function CopyList({
  label,
  items,
  maxLen,
  color,
}: {
  label: string;
  items: string[];
  maxLen: number;
  color: "current" | "proposed";
}) {
  const borderClass =
    color === "current" ? "border-muted-foreground/30" : "border-signal-blue/30";
  const bgClass =
    color === "current" ? "bg-[#0D0D0D]" : "bg-signal-blue/5";

  return (
    <div>
      <h5 className="mb-2 text-xs font-medium text-muted-foreground">
        {label}
      </h5>
      <div className="space-y-1.5">
        {items.map((item, idx) => (
          <div
            key={idx}
            className={`flex items-center justify-between rounded-md border px-3 py-1.5 text-sm ${borderClass} ${bgClass}`}
          >
            <span className="truncate text-white">{item}</span>
            <CharCount current={item.length} max={maxLen} />
          </div>
        ))}
      </div>
    </div>
  );
}

function EditableCopyList({
  label,
  items,
  maxLen,
  maxItems,
  onChange,
}: {
  label: string;
  items: string[];
  maxLen: number;
  maxItems: number;
  onChange: (items: string[]) => void;
}) {
  const handleChange = (idx: number, value: string) => {
    const updated = [...items];
    updated[idx] = value;
    onChange(updated);
  };

  const handleAdd = () => {
    if (items.length < maxItems) {
      onChange([...items, ""]);
    }
  };

  const handleRemove = (idx: number) => {
    if (items.length > 1) {
      onChange(items.filter((_, i) => i !== idx));
    }
  };

  return (
    <div>
      <h5 className="mb-2 text-xs font-medium text-muted-foreground">
        {label}
      </h5>
      <div className="space-y-1.5">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => handleChange(idx, e.target.value)}
              className={`flex-1 rounded-md border px-3 py-1.5 text-sm text-white ${
                item.length > maxLen
                  ? "border-signal-red/50 bg-signal-red/5"
                  : "border-signal-blue/30 bg-signal-blue/5"
              }`}
              placeholder={`${label} ${idx + 1}`}
            />
            <CharCount current={item.length} max={maxLen} />
            <button
              onClick={() => handleRemove(idx)}
              disabled={items.length <= 1}
              className="rounded p-1 text-muted-foreground transition-colors hover:text-signal-red disabled:opacity-30"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
      {items.length < maxItems && (
        <button
          onClick={handleAdd}
          className="mt-2 flex items-center gap-1 text-xs text-signal-blue hover:underline"
        >
          <Plus className="h-3 w-3" />
          追加
        </button>
      )}
    </div>
  );
}

export default function AdCopyComparison({
  actionSteps,
  editable = false,
  onValuesChange,
}: AdCopyComparisonProps) {
  const { current_ad, proposed_ad, change_rationale, ad_group_id } =
    actionSteps;

  const [editedHeadlines, setEditedHeadlines] = useState<string[]>(
    proposed_ad.headlines
  );
  const [editedDescriptions, setEditedDescriptions] = useState<string[]>(
    proposed_ad.descriptions
  );
  const [editedUrl, setEditedUrl] = useState(proposed_ad.final_url);

  const emitChange = (
    hl: string[],
    desc: string[],
    url: string
  ) => {
    onValuesChange?.({
      ad_group_id,
      headlines: hl,
      descriptions: desc,
      final_url: url,
      old_ad_id: current_ad?.ad_id,
    });
  };

  const handleHeadlinesChange = (hl: string[]) => {
    setEditedHeadlines(hl);
    emitChange(hl, editedDescriptions, editedUrl);
  };

  const handleDescriptionsChange = (desc: string[]) => {
    setEditedDescriptions(desc);
    emitChange(editedHeadlines, desc, editedUrl);
  };

  const handleUrlChange = (url: string) => {
    setEditedUrl(url);
    emitChange(editedHeadlines, editedDescriptions, url);
  };

  return (
    <div className="space-y-4">
      {/* Side by side comparison */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Current Ad */}
        {current_ad && (
          <div className="rounded-lg border border-border bg-[#0D0D0D] p-4">
            <div className="mb-3 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-muted-foreground" />
              <h4 className="text-sm font-medium text-muted-foreground">
                現在の広告
              </h4>
            </div>
            <CopyList
              label="ヘッドライン"
              items={current_ad.headlines}
              maxLen={HEADLINE_MAX}
              color="current"
            />
            <div className="mt-3">
              <CopyList
                label="説明文"
                items={current_ad.descriptions}
                maxLen={DESCRIPTION_MAX}
                color="current"
              />
            </div>
            {current_ad.final_url && (
              <div className="mt-3">
                <h5 className="mb-1 text-xs font-medium text-muted-foreground">
                  URL
                </h5>
                <p className="truncate text-xs text-muted-foreground">
                  {current_ad.final_url}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Proposed Ad */}
        <div className="rounded-lg border border-signal-blue/30 bg-signal-blue/5 p-4">
          <div className="mb-3 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-signal-blue" />
            <h4 className="text-sm font-medium text-signal-blue">
              提案する広告
            </h4>
            {current_ad && (
              <ArrowRight className="hidden h-4 w-4 text-signal-blue md:block" />
            )}
          </div>

          {editable ? (
            <>
              <EditableCopyList
                label="ヘッドライン"
                items={editedHeadlines}
                maxLen={HEADLINE_MAX}
                maxItems={15}
                onChange={handleHeadlinesChange}
              />
              <div className="mt-3">
                <EditableCopyList
                  label="説明文"
                  items={editedDescriptions}
                  maxLen={DESCRIPTION_MAX}
                  maxItems={4}
                  onChange={handleDescriptionsChange}
                />
              </div>
              <div className="mt-3">
                <h5 className="mb-1 text-xs font-medium text-muted-foreground">
                  URL
                </h5>
                <input
                  type="text"
                  value={editedUrl}
                  onChange={(e) => handleUrlChange(e.target.value)}
                  className="w-full rounded-md border border-signal-blue/30 bg-signal-blue/5 px-3 py-1.5 text-xs text-white"
                />
              </div>
            </>
          ) : (
            <>
              <CopyList
                label="ヘッドライン"
                items={proposed_ad.headlines}
                maxLen={HEADLINE_MAX}
                color="proposed"
              />
              <div className="mt-3">
                <CopyList
                  label="説明文"
                  items={proposed_ad.descriptions}
                  maxLen={DESCRIPTION_MAX}
                  color="proposed"
                />
              </div>
              {proposed_ad.final_url && (
                <div className="mt-3">
                  <h5 className="mb-1 text-xs font-medium text-muted-foreground">
                    URL
                  </h5>
                  <p className="truncate text-xs text-signal-blue">
                    {proposed_ad.final_url}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Change rationale */}
      {change_rationale && change_rationale.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-3">
          <h5 className="mb-2 text-xs font-medium text-muted-foreground">
            変更理由
          </h5>
          <ul className="space-y-1">
            {change_rationale.map((reason, idx) => (
              <li key={idx} className="flex gap-2 text-sm text-white">
                <span className="text-signal-blue">-</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
