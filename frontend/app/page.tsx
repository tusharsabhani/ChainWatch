import Link from "next/link";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { getDashboardAlerts, getDashboardSummary, getProducts } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";
import type {
  DashboardAlertsResponse,
  DashboardSummaryQuery
} from "@/lib/api/types";
import {
  cx,
  formatCompactNumber,
  formatDateTime,
  formatRiskScore,
  severityTone
} from "@/lib/utils";

type SearchParams = Record<string, string | string[] | undefined>;

const DATE_RANGE_OPTIONS = ["7d", "30d", "90d"] as const;
const SEVERITY_OPTIONS = [1, 2, 3, 4, 5] as const;
const REGION_OPTIONS = ["APAC", "NA"] as const;

function readSearchParam(searchParams: SearchParams, key: string) {
  const value = searchParams[key];
  return Array.isArray(value) ? value[0] : value;
}

function buildPageHref(
  searchParams: SearchParams,
  updates: Record<string, string | number | null | undefined>
) {
  const nextParams = new URLSearchParams();

  for (const [key, rawValue] of Object.entries(searchParams)) {
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
    if (value) {
      nextParams.set(key, value);
    }
  }

  for (const [key, value] of Object.entries(updates)) {
    if (value === null || value === undefined || value === "") {
      nextParams.delete(key);
    } else {
      nextParams.set(key, String(value));
    }
  }

  const queryString = nextParams.toString();
  return queryString ? `/?${queryString}` : "/";
}

function parseQuery(searchParams: SearchParams): DashboardSummaryQuery {
  const dateRange = readSearchParam(searchParams, "dateRange");
  const severityMin = Number(readSearchParam(searchParams, "severityMin") || "3");
  const category = readSearchParam(searchParams, "category") || undefined;
  const region = readSearchParam(searchParams, "region") || undefined;

  return {
    dateRange:
      dateRange === "7d" || dateRange === "30d" || dateRange === "90d" ? dateRange : "30d",
    severityMin:
      severityMin >= 1 && severityMin <= 5 ? (severityMin as 1 | 2 | 3 | 4 | 5) : 3,
    category,
    region
  };
}

function KpiCard({
  title,
  value,
  detail,
  icon,
  tone = "neutral"
}: {
  title: string;
  value: string;
  detail: string;
  icon: string;
  tone?: "success" | "caution" | "danger" | "neutral";
}) {
  const accentClass = {
    success: "bg-secondary",
    caution: "bg-caution",
    danger: "bg-error",
    neutral: "bg-slate-300"
  }[tone];

  return (
    <div className="relative overflow-hidden rounded-lg border border-slate-200 bg-white p-5">
      <div className={cx("absolute left-0 top-0 h-full w-1", accentClass)} />
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            {title}
          </p>
          <p className="mt-3 font-display text-[28px] font-bold tracking-[-0.02em] text-slate-950">
            {value}
          </p>
          <p className="mt-2 text-sm text-slate-600">{detail}</p>
        </div>
        <MaterialIcon icon={icon} className="text-[20px] text-slate-400" />
      </div>
    </div>
  );
}

function TrendBars({
  title,
  subtitle,
  points,
  tone = "secondary"
}: {
  title: string;
  subtitle: string;
  points: Array<{ label: string; value: number }>;
  tone?: "secondary" | "caution" | "danger";
}) {
  const maxValue = Math.max(...points.map((point) => point.value), 1);
  const barTone =
    tone === "danger" ? "bg-error" : tone === "caution" ? "bg-caution" : "bg-secondary";

  return (
    <SectionCard title={title} eyebrow={subtitle}>
      {points.length > 0 ? (
        <>
          <div className="flex h-44 items-stretch gap-2 rounded-lg border border-surface-container-high bg-surface-container-low p-4">
            {points.map((point) => (
              <div key={`${point.label}-${point.value}`} className="flex h-full flex-1 flex-col items-center gap-2">
                <div className="flex w-full flex-1 items-end">
                  <div
                    className={cx("w-full rounded-t-sm", barTone)}
                    style={{ height: `${Math.max((point.value / maxValue) * 100, 8)}%` }}
                  />
                </div>
                <span className="font-mono text-[10px] text-slate-500">
                  {point.label.slice(5, 7) === "01" ? point.label.slice(0, 7) : point.label}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>{points.length} points</span>
            <span>Peak {formatCompactNumber(maxValue)}</span>
          </div>
        </>
      ) : (
        <EmptyState
          title="No trend data yet"
          description="This section will populate once the matching backend signal is available."
        />
      )}
    </SectionCard>
  );
}

function AlertsSection({
  alerts
}: {
  alerts: DashboardAlertsResponse;
}) {
  return (
    <SectionCard title="Active Alerts" eyebrow="Live external events">
      {alerts.items.length > 0 ? (
        <div className="space-y-4">
          <div className="hidden grid-cols-[1.6fr,0.9fr,0.7fr,0.9fr,0.9fr] gap-4 border-b border-surface-container-high pb-3 font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500 lg:grid">
            <span>Event</span>
            <span>Risk Type</span>
            <span>Severity</span>
            <span>Country</span>
            <span>Status</span>
          </div>
          <div className="divide-y divide-surface-container-high">
            {alerts.items.map((alert) => (
              <div key={alert.eventId} className="grid gap-3 py-4 lg:grid-cols-[1.6fr,0.9fr,0.7fr,0.9fr,0.9fr] lg:items-center lg:gap-4">
                <div>
                  <p className="font-data text-base text-slate-950">{alert.title}</p>
                  <p className="mt-1 text-sm text-slate-500">
                    Detected {formatDateTime(alert.detectedAt)}
                  </p>
                </div>
                <p className="text-sm text-slate-700">{alert.riskType}</p>
                <div>
                  <StatusPill tone={severityTone(alert.severity)}>Level {alert.severity}</StatusPill>
                </div>
                <p className="text-sm text-slate-700">{alert.countryCode ?? "Global"}</p>
                <div>
                  <StatusPill tone={alert.status === "resolved" ? "success" : alert.status === "monitoring" ? "caution" : "danger"}>
                    {alert.status}
                  </StatusPill>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState
          title="No active external alerts"
          description="The local-first demo is running without live search results right now, so this section is intentionally quiet."
        />
      )}
    </SectionCard>
  );
}

export default async function DashboardPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const query = parseQuery(searchParams);
  const [summaryResult, alertsResult, productsResult] = await Promise.all([
    safeApiCall(() => getDashboardSummary(query)),
    safeApiCall(() =>
      getDashboardAlerts({
        severityMin: query.severityMin,
        limit: 8
      })
    ),
    safeApiCall(() => getProducts({ limit: 50 }))
  ]);

  const summary = summaryResult.data;
  const alerts = alertsResult.data;
  const categories = Array.from(
    new Set((productsResult.data?.items ?? []).map((item) => item.category))
  ).sort();

  if (!summary && !alerts) {
    return (
      <div className="p-4 lg:p-8">
        <ErrorState
          title="Dashboard data is unavailable"
          message={
            summaryResult.error?.message ||
            alertsResult.error?.message ||
            "The frontend could not load the dashboard summary or alert feed."
          }
        />
      </div>
    );
  }

  const activeSummary = summary;
  const topProducts = activeSummary?.topRiskProducts ?? [];
  const topSuppliers = activeSummary?.topRiskSuppliers ?? [];
  const countryExposure = activeSummary?.countryExposure ?? [];

  return (
    <div className="space-y-6 bg-background p-4 lg:p-8 lg:pt-6">
      <div className="space-y-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
              Dashboard
            </h1>
            <p className="mt-1 text-[15px] text-slate-700">
              Live operational overview across demand pressure, fulfillment stress, and external disruption readiness.
            </p>
          </div>
        </div>

        <SectionCard title="Filters" eyebrow="Dashboard query state">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {DATE_RANGE_OPTIONS.map((option) => (
                <Link
                  key={option}
                  href={buildPageHref(searchParams, { dateRange: option })}
                  className={cx(
                    "rounded-lg px-3 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                    query.dateRange === option
                      ? "bg-secondary text-white"
                      : "border border-outline-variant bg-white text-slate-600"
                  )}
                >
                  {option}
                </Link>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              {SEVERITY_OPTIONS.map((option) => (
                <Link
                  key={option}
                  href={buildPageHref(searchParams, { severityMin: option })}
                  className={cx(
                    "rounded-full border px-3 py-1.5 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                    query.severityMin === option
                      ? "border-secondary bg-secondary text-white"
                      : "border-outline-variant bg-white text-slate-600"
                  )}
                >
                  Severity {option}+
                </Link>
              ))}
            </div>

            <form className="grid gap-3 sm:grid-cols-3">
              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Category
                </span>
                <select
                  name="category"
                  defaultValue={query.category ?? ""}
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
                >
                  <option value="">All categories</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>

              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Region
                </span>
                <select
                  name="region"
                  defaultValue={query.region ?? ""}
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
                >
                  <option value="">All regions</option>
                  {REGION_OPTIONS.map((region) => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </select>
              </label>

              <div className="flex items-end gap-2">
                <input type="hidden" name="dateRange" value={query.dateRange} />
                <input type="hidden" name="severityMin" value={query.severityMin} />
                <button
                  type="submit"
                  className="rounded-lg bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white"
                >
                  Apply filters
                </button>
                <Link
                  href="/"
                  className="rounded-lg border border-outline-variant px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600"
                >
                  Reset
                </Link>
              </div>
            </form>
          </div>
        </SectionCard>
      </div>

      {activeSummary ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              title="Active Alerts"
              value={String(activeSummary.kpis.activeAlerts)}
              detail={`Minimum severity ${activeSummary.filters.severityMin} across the current feed.`}
              icon="warning"
              tone={activeSummary.kpis.activeAlerts > 0 ? "danger" : "success"}
            />
            <KpiCard
              title="Products At Risk"
              value={String(activeSummary.kpis.productsAtRisk)}
              detail="Derived from demand, inventory, fulfillment, and external signals."
              icon="inventory_2"
              tone={activeSummary.kpis.productsAtRisk > 0 ? "caution" : "success"}
            />
            <KpiCard
              title="Suppliers Exposed"
              value={String(activeSummary.kpis.suppliersExposed)}
              detail="Suppliers linked to countries with surfaced external issues."
              icon="factory"
              tone={activeSummary.kpis.suppliersExposed > 0 ? "danger" : "neutral"}
            />
            <KpiCard
              title="Countries With Issues"
              value={String(activeSummary.kpis.countriesWithIssues)}
              detail="Countries currently carrying active external disruption pressure."
              icon="public"
              tone={activeSummary.kpis.countriesWithIssues > 0 ? "danger" : "neutral"}
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.45fr,0.95fr]">
            <TrendBars
              title="Demand Pressure"
              subtitle={`Trailing ${activeSummary.filters.dateRange}`}
              points={activeSummary.trends.demandPressure}
              tone="secondary"
            />

            <SectionCard title="Country Exposure" eyebrow="External risk footprint">
              {countryExposure.length > 0 ? (
                <div className="space-y-3">
                  {countryExposure.map((country) => (
                    <Link
                      key={country.countryCode}
                      href={`/map?country=${country.countryCode}`}
                      className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-4 transition hover:border-secondary"
                    >
                      <div>
                        <p className="font-data text-base text-slate-900">{country.countryCode}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {country.activeEventCount} active event{country.activeEventCount === 1 ? "" : "s"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-display text-xl font-semibold text-slate-950">
                          {formatRiskScore(country.overallScore)}
                        </p>
                        <StatusPill tone={severityTone(Math.round(country.overallScore))}>
                          Risk
                        </StatusPill>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No country exposure yet"
                  description="The external-risk backend is running in local-first mode without live search results, so country scoring is currently empty."
                />
              )}
            </SectionCard>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <TrendBars
              title="SLA Risk"
              subtitle="Regional fulfillment stress"
              points={activeSummary.trends.slaRisk}
              tone="caution"
            />
            <TrendBars
              title="External Event Count"
              subtitle="Country-level event volume"
              points={activeSummary.trends.externalEventCount}
              tone="danger"
            />
            <SectionCard title="Top-Risk Products" eyebrow="Cross-agent ranking">
              {topProducts.length > 0 ? (
                <div className="space-y-3">
                  {topProducts.map((product) => (
                    <Link
                      key={product.productId}
                      href={`/products/${product.productId}`}
                      className="block rounded-lg border border-surface-container-high bg-surface-container-low p-4 transition hover:border-secondary"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-data text-sm text-slate-500">{product.sku}</p>
                          <p className="mt-1 font-data text-base text-slate-950">{product.name}</p>
                          <p className="mt-2 text-sm text-slate-600">
                            Primary driver: {product.primaryRiskDriver}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-display text-xl font-semibold text-slate-950">
                            {formatRiskScore(product.riskScore)}
                          </p>
                          <StatusPill tone={severityTone(Math.round(product.riskScore))}>
                            Risk
                          </StatusPill>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No product rankings yet"
                  description="The dashboard summary did not return any ranked products for the active filter set."
                />
              )}
            </SectionCard>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.35fr,0.95fr]">
            {alerts ? (
              <AlertsSection alerts={alerts} />
            ) : (
              <ErrorState
                title="Alert feed unavailable"
                message={alertsResult.error?.message || "The dashboard alerts feed could not be loaded."}
              />
            )}

            <SectionCard title="Top-Risk Suppliers" eyebrow="External exposure ranking">
              {topSuppliers.length > 0 ? (
                <div className="space-y-4">
                  {topSuppliers.map((supplier) => (
                    <div
                      key={supplier.supplierId}
                      className="rounded-lg border border-surface-container-high bg-surface-container-low p-4"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-data text-base text-slate-950">{supplier.name}</p>
                          <p className="mt-1 text-sm text-slate-600">
                            {supplier.countryCode} • {supplier.activeIssueCount} linked issue
                            {supplier.activeIssueCount === 1 ? "" : "s"}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-display text-xl font-semibold text-slate-950">
                            {formatRiskScore(supplier.riskScore)}
                          </p>
                          <StatusPill tone={severityTone(Math.round(supplier.riskScore))}>
                            Risk
                          </StatusPill>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No exposed suppliers yet"
                  description="Supplier exposure will appear here once external-risk results are cached or a live search provider is configured."
                />
              )}
            </SectionCard>
          </div>
        </>
      ) : (
        <ErrorState
          title="Dashboard summary unavailable"
          message={summaryResult.error?.message || "The dashboard summary could not be loaded."}
        />
      )}
    </div>
  );
}
