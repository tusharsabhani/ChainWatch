"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MaterialIcon } from "@/components/material-icon";
import { cx } from "@/lib/utils";

export function NavLink({
  href,
  label,
  description
}: {
  href: string;
  label: string;
  description: string;
}) {
  const pathname = usePathname();
  const activePrefix = href.startsWith("/products/") ? "/products/" : `${href}/`;
  const active =
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(activePrefix);

  return (
    <Link
      href={href}
      className={cx(
        "block rounded-lg border p-4 transition",
        active
          ? "border-teal-500 bg-slate-800/95 text-white"
          : "border-slate-800/40 bg-transparent hover:border-slate-700 hover:bg-slate-800/60"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <p className="text-sm font-semibold text-inherit">{label}</p>
          <p className={cx("text-sm leading-6", active ? "text-slate-300" : "text-slate-400")}>
            {description}
          </p>
        </div>
        <MaterialIcon
          icon={active ? "arrow_forward" : "chevron_right"}
          className={cx("mt-1 text-[16px]", active ? "text-teal-300" : "text-slate-500")}
        />
      </div>
    </Link>
  );
}
