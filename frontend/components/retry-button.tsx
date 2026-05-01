"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function RetryButton({
  label = "Retry",
  onRetry
}: {
  label?: string;
  onRetry?: () => void;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() =>
        startTransition(() => {
          if (onRetry) {
            onRetry();
            return;
          }

          router.refresh();
        })
      }
      className="inline-flex rounded-lg border border-outline-variant bg-white px-4 py-2 font-label text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-700 transition hover:border-secondary hover:text-secondary disabled:cursor-not-allowed disabled:opacity-60"
      disabled={isPending}
    >
      {isPending ? "Refreshing..." : label}
    </button>
  );
}
