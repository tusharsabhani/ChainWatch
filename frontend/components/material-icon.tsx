import { cx } from "@/lib/utils";

export function MaterialIcon({
  icon,
  className,
  filled = false
}: {
  icon: string;
  className?: string;
  filled?: boolean;
}) {
  return (
    <span
      aria-hidden="true"
      className={cx("material-symbols-outlined", className)}
      style={{
        fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 400, 'GRAD' 0, 'opsz' 24`
      }}
    >
      {icon}
    </span>
  );
}
