"use client";

import { RetryButton } from "@/components/retry-button";

export function ErrorState({
  title,
  message,
  retryLabel = "Retry",
  onRetry
}: {
  title: string;
  message: string;
  retryLabel?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-xl border border-error/25 bg-error/5 p-5">
      <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-error">
        Error state
      </p>
      <h3 className="mt-3 font-display text-xl font-semibold text-slate-900">{title}</h3>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{message}</p>
      <div className="mt-4">
        <RetryButton label={retryLabel} onRetry={onRetry} />
      </div>
    </div>
  );
}
