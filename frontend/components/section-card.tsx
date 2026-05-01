import { cx } from "@/lib/utils";

export function SectionCard({
  title,
  eyebrow,
  trailing,
  className,
  children
}: {
  title?: string;
  eyebrow?: string;
  trailing?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={cx(
        "rounded-xl border border-outline-variant bg-surface-container-lowest p-5 sm:p-6",
        className
      )}
    >
      {title || eyebrow || trailing ? (
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            {eyebrow ? (
              <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                {eyebrow}
              </p>
            ) : null}
            {title ? <h2 className="font-display text-[20px] font-semibold text-slate-900">{title}</h2> : null}
          </div>
          {trailing ? <div>{trailing}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
