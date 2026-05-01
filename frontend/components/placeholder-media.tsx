import { MaterialIcon } from "@/components/material-icon";
import { cx } from "@/lib/utils";

export function PlaceholderMedia({
  label,
  subtitle,
  icon = "data_object",
  className,
  align = "center"
}: {
  label: string;
  subtitle?: string;
  icon?: string;
  className?: string;
  align?: "center" | "left";
}) {
  return (
    <div
      className={cx(
        "relative overflow-hidden rounded-lg border border-outline-variant bg-slate-100",
        className
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(20,184,166,0.15),transparent_30%),linear-gradient(to_right,rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.12)_1px,transparent_1px)] bg-[size:auto,22px_22px,22px_22px]" />
      <div
        className={cx(
          "relative flex h-full w-full flex-col justify-end gap-2 p-5",
          align === "center" && "items-center justify-center text-center"
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-container text-white">
          <MaterialIcon icon={icon} className="text-[24px]" />
        </div>
        <div>
          <p className="font-data text-sm font-semibold text-slate-900">{label}</p>
          {subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
      </div>
    </div>
  );
}
