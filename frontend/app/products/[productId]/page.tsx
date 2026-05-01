import Link from "next/link";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { FreshnessBadge } from "@/components/freshness-badge";
import { MaterialIcon } from "@/components/material-icon";
import { PlaceholderMedia } from "@/components/placeholder-media";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { StatusTile } from "@/components/status-tile";
import { getProductDetail, getProducts } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";
import {
  cx,
  formatCompactNumber,
  formatPercent,
  formatRiskScore,
  severityTone
} from "@/lib/utils";

type SearchParams = Record<string, string | string[] | undefined>;

const DATE_RANGE_OPTIONS = ["30d", "90d", "365d"] as const;

function readSearchParam(searchParams: SearchParams, key: string) {
  const value = searchParams[key];
  return Array.isArray(value) ? value[0] : value;
}

function buildProductHref(
  productId: number | string,
  searchParams: SearchParams,
  updates: Record<string, string | null | undefined>
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
      nextParams.set(key, value);
    }
  }

  const queryString = nextParams.toString();
  return queryString ? `/products/${productId}?${queryString}` : `/products/${productId}`;
}

function parseDateRange(searchParams: SearchParams) {
  const dateRange = readSearchParam(searchParams, "dateRange");
  return dateRange === "30d" || dateRange === "90d" || dateRange === "365d"
    ? dateRange
    : "90d";
}

function asNumber(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function severityTileTone(
  score: number
):
  | "severity-1"
  | "severity-2"
  | "severity-3"
  | "severity-4"
  | "severity-5" {
  const normalized = Math.max(1, Math.min(5, Math.round(score)));
  return `severity-${normalized}` as
    | "severity-1"
    | "severity-2"
    | "severity-3"
    | "severity-4"
    | "severity-5";
}

function DemandChart({
  points
}: {
  points: Array<Record<string, unknown>>;
}) {
  const normalized = points.map((point) => ({
    label: String(point.period_start ?? point.periodStart ?? ""),
    unitsSold: asNumber(point.units_sold ?? point.unitsSold)
  }));
  const maxValue = Math.max(...normalized.map((point) => point.unitsSold), 1);

  return normalized.length > 0 ? (
    <div className="relative h-64 overflow-hidden rounded-lg border border-surface-container-high bg-surface-container-low p-4">
      <div className="flex h-full items-end gap-3">
        {normalized.map((point) => (
          <div key={point.label} className="flex flex-1 flex-col items-center justify-end gap-2">
            <div
              className="w-full rounded-t-sm bg-secondary"
              style={{ height: `${Math.max((point.unitsSold / maxValue) * 100, 8)}%` }}
            />
            <span className="font-mono text-[10px] text-slate-500">
              {point.label.slice(0, 7)}
            </span>
          </div>
        ))}
      </div>
    </div>
  ) : (
    <EmptyState
      title="No demand history for this range"
      description="Try a wider date range to see more of the historical sales trend for this product."
    />
  );
}

export default async function ProductDetailPage({
  params,
  searchParams
}: {
  params: { productId: string };
  searchParams: SearchParams;
}) {
  const productId = Number(params.productId);
  const dateRange = parseDateRange(searchParams);
  const [productResult, productsResult] = await Promise.all([
    Number.isFinite(productId)
      ? safeApiCall(() => getProductDetail(productId, { dateRange }))
      : Promise.resolve({ data: null, error: null }),
    safeApiCall(() => getProducts({ limit: 12 }))
  ]);

  const suggestions = productsResult.data?.items ?? [];
  const product = productResult.data;

  if (!product) {
    return (
      <div className="space-y-6 p-4 lg:p-8 lg:pt-6">
        <ErrorState
          title="Product detail unavailable"
          message={
            productResult.error?.message ||
            "The requested product could not be loaded from the backend."
          }
        />

        {suggestions.length > 0 ? (
          <SectionCard title="Available products" eyebrow="Fallback navigation">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {suggestions.map((item) => (
                <Link
                  key={item.productId}
                  href={`/products/${item.productId}`}
                  className="rounded-lg border border-outline-variant bg-white p-4 transition hover:border-secondary"
                >
                  <p className="font-data text-sm text-slate-500">{item.sku}</p>
                  <p className="mt-1 font-data text-base text-slate-950">{item.name}</p>
                  <p className="mt-2 text-sm text-slate-600">{item.category}</p>
                </Link>
              ))}
            </div>
          </SectionCard>
        ) : null}
      </div>
    );
  }

  const seasonalWindows = product.demand.seasonalWindows.map((window) => ({
    label: String(window.label ?? "window"),
    startMonth: asNumber(window.start_month ?? window.startMonth),
    endMonth: asNumber(window.end_month ?? window.endMonth),
    avgUnits: asNumber(window.avg_units ?? window.avgUnits)
  }));
  const recentSpikes = product.demand.recentSpikes.map((spike) => ({
    periodStart: String(spike.period_start ?? spike.periodStart ?? ""),
    unitsSold: asNumber(spike.units_sold ?? spike.unitsSold),
    baselineUnits: asNumber(spike.baseline_units ?? spike.baselineUnits),
    spikeRatio: asNumber(spike.spike_ratio ?? spike.spikeRatio),
    reason: String(spike.reason ?? "")
  }));

  return (
    <div className="space-y-6 bg-background p-4 lg:p-8 lg:pt-6">
      <div className="space-y-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              {product.product.sku} • {product.product.category}
            </p>
            <h1 className="mt-2 font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
              {product.product.name}
            </h1>
            <p className="mt-2 text-[15px] text-slate-700">
              {product.product.brand ?? "ChainWatch catalog"} • Product-level demand, inventory, fulfillment, supplier, and external-risk intelligence.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <FreshnessBadge
              freshness={product.freshness}
              lastUpdatedAt={product.lastUpdatedAt}
            />
            <Link
              href={`/chat?contextScope=product&contextId=${product.product.id}`}
              className="rounded-lg bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white"
            >
              Ask in chat
            </Link>
            <Link
              href={`/reports?scopeType=product&scopeId=${product.product.id}`}
              className="rounded-lg border border-outline-variant bg-white px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700"
            >
              Generate report
            </Link>
          </div>
        </div>

        <SectionCard title="Demand window" eyebrow="Date range">
          <div className="flex flex-wrap gap-2">
            {DATE_RANGE_OPTIONS.map((option) => (
              <Link
                key={option}
                href={buildProductHref(product.product.id, searchParams, { dateRange: option })}
                className={cx(
                  "rounded-full px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                  dateRange === option
                    ? "bg-secondary text-white"
                    : "border border-outline-variant bg-white text-slate-600"
                )}
              >
                {option}
              </Link>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.95fr,1.45fr]">
        <SectionCard className="overflow-hidden">
          <div className="grid gap-5 lg:grid-cols-[0.75fr,1.25fr]">
            <PlaceholderMedia
              label={product.product.name}
              subtitle="Safe local placeholder for the catalog visual."
              icon="inventory_2"
              className="min-h-[220px]"
            />

            <div className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <StatusTile
                  label="Demand Risk"
                  value={formatRiskScore(product.demand.demandRiskScore)}
                  detail="Heuristic demand pressure score"
                  tone={severityTileTone(product.demand.demandRiskScore)}
                />
                <StatusTile
                  label="Stockout Risk"
                  value={formatRiskScore(product.inventory.stockoutRiskScore)}
                  detail="Inventory pressure score"
                  tone={severityTileTone(product.inventory.stockoutRiskScore)}
                />
                <StatusTile
                  label="Fulfillment Risk"
                  value={formatRiskScore(product.fulfillment.fulfillmentRiskScore)}
                  detail="Backlog and SLA stress"
                  tone={severityTileTone(product.fulfillment.fulfillmentRiskScore)}
                />
                <StatusTile
                  label="Days Of Cover"
                  value={product.inventory.daysOfCover ? `${product.inventory.daysOfCover.toFixed(1)} days` : "--"}
                  detail="Current stock runway"
                  tone="accent"
                />
              </div>

              <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Recommended action
                </p>
                <p className="mt-3 text-sm leading-7 text-slate-700">
                  {product.inventory.recommendedAction}
                </p>
              </div>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Demand Trend" eyebrow={`${dateRange} sales history`}>
          <DemandChart points={product.demand.historicalTrend} />
        </SectionCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr,0.8fr]">
        <SectionCard title="Inventory Position" eyebrow="Current stock health">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatusTile
              label="On Hand"
              value={formatCompactNumber(product.inventory.currentOnHand)}
              detail="Sellable stock"
              tone="accent"
            />
            <StatusTile
              label="Reserved"
              value={formatCompactNumber(product.inventory.reservedQty)}
              detail="Already allocated"
              tone="accent"
            />
            <StatusTile
              label="Inbound"
              value={formatCompactNumber(product.inventory.inboundQty)}
              detail="Expected replenishment"
              tone="success"
            />
          </div>
        </SectionCard>

        <SectionCard title="Fulfillment Pulse" eyebrow="Operational delivery health">
          <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
            <div className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-3">
              <span className="text-sm text-slate-600">Backlog orders</span>
              <span className="font-data text-sm text-slate-950">{formatCompactNumber(product.fulfillment.backlogOrders)}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-3">
              <span className="text-sm text-slate-600">Avg ship delay</span>
              <span className="font-data text-sm text-slate-950">{product.fulfillment.avgShipDelayHours.toFixed(1)}h</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-3">
              <span className="text-sm text-slate-600">On-time rate</span>
              <span className="font-data text-sm text-slate-950">
                {formatPercent(product.fulfillment.onTimeRate, { scale: "fraction", maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr,0.85fr]">
        <SectionCard title="Seasonality & Spikes" eyebrow="Demand interpretation">
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                Seasonal windows
              </p>
              {seasonalWindows.length > 0 ? (
                <div className="mt-3 space-y-3">
                  {seasonalWindows.map((window) => (
                    <div key={`${window.label}-${window.startMonth}`} className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-data text-base text-slate-950">{window.label}</p>
                        <StatusPill tone={window.label === "peak" ? "danger" : "neutral"}>
                          M{window.startMonth}-M{window.endMonth}
                        </StatusPill>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">
                        Average units {window.avgUnits.toFixed(0)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No seasonal windows detected"
                  description="This product does not currently show a strong seasonal pattern in the loaded data."
                />
              )}
            </div>

            <div>
              <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                Recent spikes
              </p>
              {recentSpikes.length > 0 ? (
                <div className="mt-3 space-y-3">
                  {recentSpikes.map((spike) => (
                    <div key={spike.periodStart} className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-data text-base text-slate-950">{spike.periodStart}</p>
                          <p className="mt-1 text-sm text-slate-600">
                            {spike.unitsSold} sold vs {spike.baselineUnits.toFixed(0)} baseline
                          </p>
                        </div>
                        <StatusPill tone="caution">{spike.spikeRatio.toFixed(2)}x</StatusPill>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{spike.reason}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  title="No recent spikes detected"
                  description="The current demand window does not include a standout spike event for this product."
                />
              )}
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Linked Risk Events" eyebrow="External context">
          {product.linkedRiskEvents.length > 0 ? (
            <div className="space-y-3">
              {product.linkedRiskEvents.map((event) => (
                <div key={event.eventId} className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-data text-base text-slate-950">{event.title}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {event.riskType} {event.countryCode ? `• ${event.countryCode}` : ""}
                      </p>
                    </div>
                    <StatusPill tone={severityTone(event.severity)}>Level {event.severity}</StatusPill>
                  </div>
                  {event.sourceUrl ? (
                    <a
                      href={event.sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-3 inline-flex items-center gap-2 text-xs text-secondary"
                    >
                      Open source
                      <MaterialIcon icon="open_in_new" className="text-[14px]" />
                    </a>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No linked risk events yet"
              description="The product detail endpoint is live, but no cited external-risk events are currently linked to this SKU."
            />
          )}
        </SectionCard>
      </div>

      <SectionCard title="Supplier Exposure" eyebrow="Sourcing relationships">
        {product.suppliers.length > 0 ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {product.suppliers.map((supplier) => (
              <div key={supplier.supplierId} className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-data text-base text-slate-950">{supplier.name}</p>
                    <p className="mt-1 text-sm text-slate-600">
                      {supplier.supplierCode} • {supplier.region ?? "Unknown region"}
                    </p>
                  </div>
                  <Link
                    href={`/map?country=${supplier.countryCode}`}
                    className="rounded-full border border-outline-variant px-3 py-1 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600"
                  >
                    {supplier.countryCode}
                  </Link>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded border border-white/60 bg-white/70 px-3 py-2">
                    <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Lead time
                    </p>
                    <p className="mt-2 text-sm text-slate-900">
                      {supplier.leadTimeDays ? `${supplier.leadTimeDays} days` : "Not available"}
                    </p>
                  </div>
                  <div className="rounded border border-white/60 bg-white/70 px-3 py-2">
                    <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Reliability
                    </p>
                    <p className="mt-2 text-sm text-slate-900">
                      {supplier.reliabilityScore ? formatPercent(supplier.reliabilityScore, { scale: "whole", maximumFractionDigits: 1 }) : "Not available"}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No supplier data returned"
            description="This product currently has no supplier relationships in the backend response."
          />
        )}
      </SectionCard>
    </div>
  );
}
