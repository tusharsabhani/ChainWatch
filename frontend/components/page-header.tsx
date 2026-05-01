import Link from "next/link";

import { MaterialIcon } from "@/components/material-icon";
import { cx } from "@/lib/utils";

type Breadcrumb = {
  label: string;
  href?: string;
};

export function PageHeader({
  title,
  description,
  breadcrumbs,
  badge,
  actions
}: {
  title: string;
  description: string;
  breadcrumbs: Breadcrumb[];
  badge?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3 font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
        {breadcrumbs.map((crumb, index) => (
          <div key={`${crumb.label}-${index}`} className="flex items-center gap-3">
            {crumb.href ? (
              <Link href={crumb.href} className="transition hover:text-secondary">
                {crumb.label}
              </Link>
            ) : (
              <span>{crumb.label}</span>
            )}
            {index < breadcrumbs.length - 1 ? (
              <MaterialIcon icon="chevron_right" className="text-[14px] text-slate-400" />
            ) : null}
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-3xl space-y-3">
          {badge ? (
            <span className="inline-flex items-center gap-2 rounded-full border border-secondary/15 bg-secondary/10 px-3 py-1 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary">
              <span className="h-2 w-2 rounded-full bg-secondary" />
              {badge}
            </span>
          ) : null}
          <h1 className="font-display text-3xl font-semibold leading-tight text-balance tracking-[-0.02em] text-slate-950 sm:text-4xl">
            {title}
          </h1>
          <p className={cx("max-w-3xl text-sm leading-7 text-slate-600 sm:text-base")}>
            {description}
          </p>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </div>
    </div>
  );
}
