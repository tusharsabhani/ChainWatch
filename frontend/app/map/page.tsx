import Link from "next/link";

import { WorldRiskMap } from "@/components/world-risk-map";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import { getCountryDetail, getMapCountries, getProductDetail, getProducts } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";
import { countryNameFromCode } from "@/lib/countries";
import type {
  CountryDetailResponse,
  MapCountriesQuery
} from "@/lib/api/types";
import { cx, formatDateTime, formatRiskScore, severityTone } from "@/lib/utils";

type SearchParams = Record<string, string | string[] | undefined>;

const RISK_TYPE_OPTIONS = [
  { label: "Overview", value: "" },
  { label: "Geopolitical", value: "geopolitical" },
  { label: "Tariff", value: "tariff" },
  { label: "Logistics", value: "logistics" },
  { label: "Weather", value: "weather" },
  { label: "Labor", value: "labor" }
] as const;

const SEVERITY_OPTIONS = [1, 2, 3, 4, 5] as const;

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
  return queryString ? `/map?${queryString}` : "/map";
}

function parseQuery(searchParams: SearchParams): MapCountriesQuery {
  const riskType = readSearchParam(searchParams, "riskType") || undefined;
  const severityMin = Number(readSearchParam(searchParams, "severityMin") || "1");

  return {
    riskType,
    severityMin:
      severityMin >= 1 && severityMin <= 5 ? (severityMin as 1 | 2 | 3 | 4 | 5) : 1
  };
}

async function buildFallbackCountriesFromProducts() {
  const productsResult = await safeApiCall(() => getProducts({ limit: 12 }));
  const products = productsResult.data?.items ?? [];

  if (products.length === 0) {
    return [];
  }

  const detailResults = await Promise.all(
    products.map((product) =>
      safeApiCall(() => getProductDetail(product.productId, { dateRange: "90d" }))
    )
  );

  const countryMap = new Map<string, { countryCode: string; countryName: string; productIds: Set<number> }>();

  for (const result of detailResults) {
    const detail = result.data;
    if (!detail) {
      continue;
    }

    for (const supplier of detail.suppliers) {
      const existing = countryMap.get(supplier.countryCode) ?? {
        countryCode: supplier.countryCode,
        countryName: countryNameFromCode(supplier.countryCode),
        productIds: new Set<number>()
      };
      existing.productIds.add(detail.product.id);
      countryMap.set(supplier.countryCode, existing);
    }
  }

  return Array.from(countryMap.values()).map((country) => ({
    countryCode: country.countryCode,
    countryName: country.countryName,
    overallScore: 1,
    highestSeverity: 1,
    activeEventCount: 0
  }));
}

function CountryDetailPanel({
  detail,
  productsLinkHref,
  reportsLinkHref
}: {
  detail: CountryDetailResponse;
  productsLinkHref: string;
  reportsLinkHref: string;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Overall score
            </p>
            <p className="mt-3 font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
              {formatRiskScore(detail.country.overallScore)}
            </p>
          </div>
          <StatusPill tone={severityTone(Math.round(detail.country.overallScore))}>
            Level {Math.max(1, Math.round(detail.country.overallScore))}
          </StatusPill>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-600">{detail.country.summary}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link
          href={productsLinkHref}
          className="rounded-lg bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white"
        >
          Open linked products
        </Link>
        <Link
          href={reportsLinkHref}
          className="rounded-lg border border-outline-variant bg-white px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700"
        >
          Generate report
        </Link>
      </div>

      <SectionCard title="Active Issues" eyebrow="Country-level signals">
        {detail.issues.length > 0 ? (
          <div className="space-y-3">
            {detail.issues.map((issue) => (
              <div key={issue.eventId} className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-data text-base text-slate-950">{issue.title}</p>
                    <p className="mt-1 text-sm text-slate-600">{issue.riskType}</p>
                  </div>
                  <StatusPill tone={severityTone(issue.severity)}>Level {issue.severity}</StatusPill>
                </div>
                {issue.sourceUrl ? (
                  <a
                    href={issue.sourceUrl}
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
            title="No active issues for this country"
            description="The country detail endpoint is live, but no cited risk events are currently surfaced for this location."
          />
        )}
      </SectionCard>

      <SectionCard title="Affected Suppliers" eyebrow="Local catalog exposure">
        {detail.affectedSuppliers.length > 0 ? (
          <div className="space-y-3">
            {detail.affectedSuppliers.map((supplier) => (
              <div key={supplier.supplierId} className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-3">
                <p className="font-data text-sm text-slate-950">{supplier.name}</p>
                <span className="font-mono text-xs text-slate-500">#{supplier.supplierId}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No supplier linkage returned"
            description="Supplier associations will appear here when external-risk results identify direct impact relationships."
          />
        )}
      </SectionCard>

      <SectionCard title="Affected Products" eyebrow="Product drilldown">
        {detail.affectedProducts.length > 0 ? (
          <div className="space-y-3">
            {detail.affectedProducts.map((product) => (
              <Link
                key={product.productId}
                href={`/products/${product.productId}`}
                className="flex items-center justify-between rounded-lg border border-surface-container-high bg-surface-container-low px-4 py-3 transition hover:border-secondary"
              >
                <div>
                  <p className="font-data text-sm text-slate-950">{product.name}</p>
                  <p className="mt-1 text-xs text-slate-500">{product.sku}</p>
                </div>
                <MaterialIcon icon="arrow_forward" className="text-[18px] text-slate-500" />
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No product impacts returned"
            description="Product associations will appear here once country-level risk items are linked to specific SKUs."
          />
        )}
      </SectionCard>
    </div>
  );
}

export default async function MapPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const query = parseQuery(searchParams);
  const selectedCountryFromQuery = readSearchParam(searchParams, "country")?.toUpperCase() ?? null;
  const countriesResult = await safeApiCall(() => getMapCountries(query));

  const fallbackCountries =
    !countriesResult.data || countriesResult.data.items.length === 0
      ? await buildFallbackCountriesFromProducts()
      : [];
  const countries = countriesResult.data?.items.length
    ? countriesResult.data.items
    : fallbackCountries;
  const selectedCountryCode = selectedCountryFromQuery ?? countries[0]?.countryCode ?? null;
  const countryDetailResult = selectedCountryCode
    ? await safeApiCall(() => getCountryDetail(selectedCountryCode))
    : { data: null, error: null };

  if (!countriesResult.data && countries.length === 0) {
    return (
      <div className="p-4 lg:p-8">
        <ErrorState
          title="Map data is unavailable"
          message={
            countriesResult.error?.message ||
            "The frontend could not load any country-level data for the map surface."
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-background p-4 lg:p-8 lg:pt-6">
      <div className="space-y-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
              Global Risk Map
            </h1>
            <p className="mt-1 text-[15px] text-slate-700">
              Filter country-level disruption pressure, inspect detail panels, and jump from country context into product-level analysis.
            </p>
          </div>
        </div>

        <SectionCard title="Filters" eyebrow="Map query state">
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {RISK_TYPE_OPTIONS.map((option) => (
                <Link
                  key={option.label}
                  href={buildPageHref(searchParams, {
                    riskType: option.value || null,
                    country: selectedCountryCode
                  })}
                  className={cx(
                    "rounded-full px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                    (query.riskType ?? "") === option.value
                      ? "bg-secondary text-white"
                      : "border border-outline-variant bg-white text-slate-600"
                  )}
                >
                  {option.label}
                </Link>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              {SEVERITY_OPTIONS.map((option) => (
                <Link
                  key={option}
                  href={buildPageHref(searchParams, {
                    severityMin: option,
                    country: selectedCountryCode
                  })}
                  className={cx(
                    "rounded-full border px-3 py-1.5 font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                    query.severityMin === option
                      ? "border-secondary bg-secondary text-white"
                      : "border-outline-variant bg-white text-slate-600"
                  )}
                >
                  {option}+
                </Link>
              ))}
            </div>
          </div>
        </SectionCard>
      </div>

      {countries.length > 0 ? (
        <>
          <section className="space-y-4 lg:hidden">
            <WorldRiskMap
              countries={countries}
              selectedCountryCode={selectedCountryCode}
              className="h-[320px]"
            />

            {countryDetailResult.data ? (
              <CountryDetailPanel
                detail={countryDetailResult.data}
                productsLinkHref={countryDetailResult.data.affectedProducts[0] ? `/products/${countryDetailResult.data.affectedProducts[0].productId}` : "/products/1"}
                reportsLinkHref={`/reports?scopeType=country&scopeId=${countryDetailResult.data.country.countryCode}`}
              />
            ) : (
              <ErrorState
                title="Country detail unavailable"
                message={
                  countryDetailResult.error?.message ||
                  "The selected country detail could not be loaded."
                }
              />
            )}
          </section>

          <section className="hidden lg:grid lg:grid-cols-[1.3fr,0.78fr] lg:gap-6">
            <SectionCard
              title="Interactive World View"
              eyebrow="React Simple Maps"
              trailing={
                <div className="flex items-center gap-2">
                  <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Selected
                  </span>
                  <StatusPill tone={severityTone(Math.round(countryDetailResult.data?.country.overallScore ?? 1))}>
                    {selectedCountryCode ?? "None"}
                  </StatusPill>
                </div>
              }
              className="overflow-hidden p-0"
            >
              <div className="relative h-[640px]">
                <WorldRiskMap
                  countries={countries}
                  selectedCountryCode={selectedCountryCode}
                  className="h-full rounded-none border-0"
                />

                <div className="absolute bottom-5 left-5 z-10 rounded-lg border border-slate-200 bg-white/95 px-4 py-3 shadow-overlay backdrop-blur">
                  <div className="flex items-center gap-4">
                    <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Risk scale
                    </span>
                    <div className="flex items-center gap-2">
                      {SEVERITY_OPTIONS.map((severity) => (
                        <div key={severity} className="flex items-center gap-1">
                          <span
                            className={cx(
                              "h-2.5 w-6 rounded-full",
                              severity >= 4
                                ? "bg-error"
                                : severity === 3
                                  ? "bg-caution"
                                  : severity === 2
                                    ? "bg-slate-400"
                                    : "bg-secondary"
                            )}
                          />
                          <span className="font-mono text-[10px] text-slate-500">{severity}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </SectionCard>

            <SectionCard
              title={countryDetailResult.data?.country.countryName ?? countryNameFromCode(selectedCountryCode ?? "—")}
              eyebrow="Selected country"
              className="h-fit"
            >
              {countryDetailResult.data ? (
                <CountryDetailPanel
                  detail={countryDetailResult.data}
                  productsLinkHref={countryDetailResult.data.affectedProducts[0] ? `/products/${countryDetailResult.data.affectedProducts[0].productId}` : "/products/1"}
                  reportsLinkHref={`/reports?scopeType=country&scopeId=${countryDetailResult.data.country.countryCode}`}
                />
              ) : (
                <ErrorState
                  title="Country detail unavailable"
                  message={
                    countryDetailResult.error?.message ||
                    "The selected country detail could not be loaded."
                  }
                />
              )}
            </SectionCard>
          </section>

        </>
      ) : (
        <EmptyState
          title="No countries match the current filters"
          description="Try a lower severity threshold or reset the risk-type filter to bring countries back into view."
        />
      )}
    </div>
  );
}
