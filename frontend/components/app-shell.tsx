"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { MaterialIcon } from "@/components/material-icon";
import type { HealthResponse } from "@/lib/api/types";
import { getRouteMeta, NAV_ITEMS } from "@/lib/navigation";
import { cx, formatClockTime, toDisplayLabel } from "@/lib/utils";

function getHeartbeatState(health: HealthResponse | null) {
  if (!health) {
    return { label: "Unavailable", dotClass: "bg-error" };
  }

  if (health.status === "ok" && health.database.status === "connected") {
    return { label: "Fresh", dotClass: "bg-secondary" };
  }

  return { label: "Degraded", dotClass: "bg-caution" };
}

function DesktopSidebar({ pathname }: { pathname: string }) {
  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-64 flex-col border-r border-slate-800 bg-slate-900 lg:flex">
      <div className="px-6 py-8">
        <h1 className="text-xl font-black tracking-tight text-white">ChainWatch</h1>
        <p className="mt-1 font-label text-[11px] uppercase tracking-[0.24em] text-teal-400">
          Risk Intelligence
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || (item.key === "products" && pathname.startsWith("/products/"));

          return (
            <Link
              key={item.key}
              href={item.href}
              className={cx(
                "flex items-center gap-3 px-4 py-3 font-body text-sm transition-colors",
                active
                  ? "border-l-4 border-teal-500 bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              )}
            >
              <MaterialIcon icon={item.icon} filled={active} className="text-[20px]" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-slate-800 p-4">
        <div className="rounded-lg bg-slate-800/40 p-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-500 text-xs font-bold text-slate-950">
              CW
            </div>
            <div>
              <p className="text-xs font-semibold text-white">Local Workspace</p>
              <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500">
                Phase 1 preview
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function DesktopTopbar({
  pathname,
  health,
  checkedAt
}: {
  pathname: string;
  health: HealthResponse | null;
  checkedAt: string;
}) {
  const routeMeta = getRouteMeta(pathname);
  const heartbeat = getHeartbeatState(health);
  const productLabel = routeMeta.productContext ? toDisplayLabel(routeMeta.productContext) : null;

  return (
    <header className="fixed left-64 right-0 top-0 z-30 hidden h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-8 backdrop-blur-md lg:flex">
      <div className="flex flex-1 items-center gap-6">
        <div className="flex items-center gap-4">
          <h2 className="font-display text-[20px] font-semibold tracking-[-0.01em] text-slate-900">
            {routeMeta.desktopTitle}
          </h2>
          {productLabel ? (
            <>
              <div className="h-4 w-px bg-slate-200" />
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>SKU:</span>
                <span className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-slate-700">
                  {productLabel}
                </span>
              </div>
            </>
          ) : null}
        </div>

        {routeMeta.desktopSearchPlaceholder ? (
          <div className="hidden max-w-lg flex-1 xl:block">
            <div className="relative">
              <MaterialIcon
                icon="search"
                className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-slate-400"
              />
              <input
                type="text"
                readOnly
                value=""
                placeholder={routeMeta.desktopSearchPlaceholder}
                className="w-full rounded-full border-none bg-slate-100 py-2 pl-10 pr-4 text-xs text-slate-600 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-teal-500/40"
              />
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
          <span className={cx("h-2 w-2 rounded-full", heartbeat.dotClass)} />
          <span>
            {routeMeta.desktopStatusLabel}: {heartbeat.label} | {formatClockTime(checkedAt)}
          </span>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <MaterialIcon icon="monitor_heart" className="cursor-pointer text-[22px] hover:text-teal-600" />
          <div className="relative">
            <MaterialIcon icon="notifications" className="cursor-pointer text-[22px] hover:text-teal-600" />
            <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-error" />
          </div>
          <MaterialIcon icon="account_circle" className="cursor-pointer text-[22px] hover:text-teal-600" />
        </div>
      </div>
    </header>
  );
}

function MobileTopbar({ health }: { health: HealthResponse | null }) {
  const heartbeat = getHeartbeatState(health);

  return (
    <header className="fixed left-0 right-0 top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/85 px-4 backdrop-blur-md lg:hidden">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-container">
          <MaterialIcon icon="shield" className="text-[22px] text-secondary-container" />
        </div>
        <span className="font-display text-[18px] font-semibold tracking-[-0.02em] text-slate-900">
          ChainWatch
        </span>
      </div>

      <div className="flex items-center gap-3">
        <div
          className={cx(
            "inline-flex items-center gap-2 rounded-full border px-3 py-1.5",
            heartbeat.label === "Fresh"
              ? "border-secondary/20 bg-secondary/10 text-secondary"
              : heartbeat.label === "Degraded"
                ? "border-caution/20 bg-caution/10 text-caution"
                : "border-error/20 bg-error/10 text-error"
          )}
        >
          <span className={cx("h-2 w-2 rounded-full", heartbeat.dotClass)} />
          <span className="font-label text-[10px] font-semibold uppercase tracking-[0.14em]">
            {heartbeat.label}
          </span>
        </div>
        <MaterialIcon icon="notifications" className="text-[22px] text-slate-600" />
      </div>
    </header>
  );
}

function MobileBottomNav({ pathname }: { pathname: string }) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 flex h-16 items-center justify-around border-t border-slate-200 bg-white lg:hidden">
      {NAV_ITEMS.filter((item) => item.mobileVisible).map((item) => {
        const active = pathname === item.href;

        return (
          <Link
            key={item.key}
            href={item.href}
            className={cx(
              "flex flex-col items-center justify-center gap-1 text-xs",
              active ? "text-secondary" : "text-slate-600"
            )}
          >
            <MaterialIcon icon={item.icon} filled={active} className="text-[22px]" />
            <span className="font-label text-[10px] uppercase tracking-[0.08em]">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({
  children,
  initialHealth,
  healthCheckedAt
}: {
  children: React.ReactNode;
  initialHealth: HealthResponse | null;
  healthCheckedAt: string;
}) {
  const pathname = usePathname();
  const routeMeta = getRouteMeta(pathname);
  const chatFocusMobile = routeMeta.shellVariant === "chat-mobile-focus";

  return (
    <div className="min-h-screen bg-background text-on-background">
      <DesktopSidebar pathname={pathname} />
      <DesktopTopbar pathname={pathname} health={initialHealth} checkedAt={healthCheckedAt} />
      {!chatFocusMobile ? <MobileTopbar health={initialHealth} /> : null}
      {!chatFocusMobile ? <MobileBottomNav pathname={pathname} /> : null}

      <main
        className={cx(
          "min-h-screen bg-background",
          chatFocusMobile ? "lg:pl-64 lg:pt-16" : "pb-16 pt-16 lg:pb-0 lg:pl-64 lg:pt-16"
        )}
      >
        {children}
      </main>
    </div>
  );
}
