"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { MaterialIcon } from "@/components/material-icon";
import { cx } from "@/lib/utils";

type MobileNavItem = {
  href: string;
  label: string;
  description: string;
};

export function MobileNav({ items }: { items: readonly MobileNavItem[] }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-outline-variant bg-white text-slate-700 transition hover:border-secondary hover:text-secondary"
        aria-label="Open navigation"
      >
        <MaterialIcon icon="menu" className="text-[20px]" />
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 bg-slate-950/35 backdrop-blur-sm xl:hidden">
          <div className="ml-auto flex h-full w-full max-w-sm flex-col border-l border-slate-800 bg-slate-900 p-5 shadow-overlay">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-teal-400">
                  ChainWatch
                </p>
                <p className="mt-1 text-sm text-slate-400">Navigation</p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-700 bg-slate-800 text-slate-200 transition hover:border-teal-500 hover:text-teal-300"
                aria-label="Close navigation"
              >
                <MaterialIcon icon="close" className="text-[18px]" />
              </button>
            </div>

            <nav className="mt-6 space-y-2">
              {items.map((item) => {
                const activePrefix = item.href.startsWith("/products/") ? "/products/" : `${item.href}/`;
                const active = pathname === item.href || pathname.startsWith(activePrefix);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={cx(
                      "block rounded-lg border p-4 transition",
                      active
                        ? "border-teal-500 bg-slate-800 text-white"
                        : "border-slate-800 bg-slate-950/40 text-slate-200 hover:border-slate-700 hover:bg-slate-800/70"
                    )}
                  >
                    <p className="text-sm font-semibold">{item.label}</p>
                    <p className="mt-1 text-sm text-slate-400">{item.description}</p>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      ) : null}
    </>
  );
}
