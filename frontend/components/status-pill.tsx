import { cx } from "@/lib/utils";

const toneStyles = {
  success: "border-secondary/15 bg-secondary/10 text-secondary",
  caution: "border-caution/15 bg-caution/10 text-caution",
  danger: "border-error/15 bg-error/10 text-error",
  neutral: "border-slate-300 bg-slate-200 text-slate-600"
} as const;

export function StatusPill({
  tone = "neutral",
  children,
  className
}: {
  tone?: keyof typeof toneStyles;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full border px-2 py-0.5 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
        toneStyles[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
