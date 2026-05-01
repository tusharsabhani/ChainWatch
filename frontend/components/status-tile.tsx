import { cx } from "@/lib/utils";

const toneClasses = {
  success: "border-secondary/20 bg-secondary/10",
  caution: "border-caution/20 bg-caution/10",
  danger: "border-error/20 bg-error/10",
  accent: "border-slate-300 bg-slate-100",
  "severity-1": "border-severity-1/20 bg-severity-1/10",
  "severity-2": "border-severity-2/20 bg-severity-2/10",
  "severity-3": "border-severity-3/20 bg-severity-3/10",
  "severity-4": "border-severity-4/20 bg-severity-4/10",
  "severity-5": "border-severity-5/20 bg-severity-5/10"
} as const;

export function StatusTile({
  label,
  value,
  detail,
  tone = "accent",
  compact = false
}: {
  label: string;
  value: string;
  detail?: string;
  tone?:
    | "success"
    | "caution"
    | "danger"
    | "accent"
    | "severity-1"
    | "severity-2"
    | "severity-3"
    | "severity-4"
    | "severity-5";
  compact?: boolean;
}) {
  return (
    <div
      className={cx(
        "rounded-lg border p-4",
        toneClasses[tone],
        compact ? "space-y-1" : "space-y-2"
      )}
    >
      <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className={cx("font-display font-semibold text-slate-900", compact ? "text-base" : "text-2xl")}>
        {value}
      </p>
      {detail ? <p className="text-sm leading-6 text-slate-600">{detail}</p> : null}
    </div>
  );
}
