import type { FreshnessInfo } from "@/lib/api/types";
import { formatDateTime } from "@/lib/utils";

export function FreshnessBadge({
  freshness,
  lastUpdatedAt,
  label
}: {
  freshness?: FreshnessInfo | null;
  lastUpdatedAt?: string | null;
  label?: string;
}) {
  const tone =
    freshness?.isStale === true
      ? "border-caution/20 bg-caution/10 text-caution"
      : freshness?.dataSource === "cached"
        ? "border-slate-300 bg-slate-100 text-slate-700"
        : "border-secondary/20 bg-secondary/10 text-secondary";

  const resolvedLabel =
    label ||
    (freshness?.isStale
      ? "Stale cache"
      : freshness?.dataSource === "cached"
        ? "Cached"
        : "Fresh");

  const updatedAt = freshness?.lastUpdatedAt ?? lastUpdatedAt ?? null;

  return (
    <div className={`inline-flex flex-wrap items-center gap-2 rounded-full border px-3 py-2 ${tone}`}>
      <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em]">
        {resolvedLabel}
      </span>
      {updatedAt ? <span className="text-xs">Updated {formatDateTime(updatedAt)}</span> : null}
      {freshness?.refreshScheduled ? (
        <span className="text-xs opacity-75">Refresh scheduled</span>
      ) : null}
    </div>
  );
}
