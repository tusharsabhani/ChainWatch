"use client";

import { useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  ComposableMap,
  Geographies,
  Geography
} from "react-simple-maps";
import worldAtlas from "world-atlas/countries-110m.json";

import { countryNumericCode, COUNTRY_NUMERIC_BY_CODE } from "@/lib/countries";
import { cx, formatRiskScore } from "@/lib/utils";

type MapCountryDatum = {
  countryCode: string;
  countryName: string;
  overallScore: number;
  highestSeverity: number;
  activeEventCount: number;
};

const COUNTRY_CODE_BY_NUMERIC = Object.fromEntries(
  Object.entries(COUNTRY_NUMERIC_BY_CODE).map(([countryCode, numericCode]) => [
    numericCode.padStart(3, "0"),
    countryCode
  ])
);

function normalizeNumericId(value: string | number) {
  return String(value).padStart(3, "0");
}

function fillForCountry(country: MapCountryDatum | undefined, isSelected: boolean) {
  if (isSelected) {
    return "#0f766e";
  }

  if (!country) {
    return "#f1f5f9";
  }

  if (country.highestSeverity >= 4) {
    return "#ef4444";
  }

  if (country.highestSeverity === 3) {
    return "#f59e0b";
  }

  if (country.highestSeverity === 2) {
    return "#94a3b8";
  }

  return "#14b8a6";
}

export function WorldRiskMap({
  countries,
  selectedCountryCode,
  className
}: {
  countries: MapCountryDatum[];
  selectedCountryCode?: string | null;
  className?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [hoveredCountryCode, setHoveredCountryCode] = useState<string | null>(null);

  const countriesByCode = useMemo(
    () =>
      Object.fromEntries(
        countries.map((country) => [country.countryCode.toUpperCase(), country])
      ),
    [countries]
  );

  const hoveredCountry =
    (hoveredCountryCode ? countriesByCode[hoveredCountryCode] : null) ??
    (selectedCountryCode ? countriesByCode[selectedCountryCode] : null);

  return (
    <div className={cx("relative overflow-hidden rounded-lg border border-slate-200 bg-slate-50", className)}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(20,184,166,0.12),transparent_32%),linear-gradient(to_right,rgba(148,163,184,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.1)_1px,transparent_1px)] bg-[size:auto,24px_24px,24px_24px]" />

      {hoveredCountry ? (
        <div className="absolute right-4 top-4 z-10 min-w-[180px] rounded-lg border border-slate-200 bg-white/95 p-3 shadow-overlay backdrop-blur">
          <p className="font-data text-sm text-slate-900">{hoveredCountry.countryName}</p>
          <p className="mt-1 text-xs text-slate-600">
            Score {formatRiskScore(hoveredCountry.overallScore)} • Severity {hoveredCountry.highestSeverity}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {hoveredCountry.activeEventCount} active event{hoveredCountry.activeEventCount === 1 ? "" : "s"}
          </p>
        </div>
      ) : null}

      <ComposableMap
        projection="geoEqualEarth"
        projectionConfig={{ scale: 145 }}
        className="relative z-[1] h-full w-full"
      >
        <Geographies geography={worldAtlas as never}>
          {({ geographies }) =>
            geographies.map((geography) => {
              const geographyId = geography.id;
              if (typeof geographyId !== "string" && typeof geographyId !== "number") {
                return null;
              }

              const numericId = normalizeNumericId(geographyId);
              const countryCode = COUNTRY_CODE_BY_NUMERIC[numericId] ?? null;
              const country = countryCode ? countriesByCode[countryCode] : undefined;
              const isSelected =
                Boolean(countryCode) &&
                countryCode === selectedCountryCode;
              const isInteractive = Boolean(countryCode && (country || countryNumericCode(countryCode)));

              return (
                <Geography
                  key={String(geography.rsmKey ?? numericId)}
                  geography={geography}
                  onMouseEnter={() => {
                    if (countryCode) {
                      setHoveredCountryCode(countryCode);
                    }
                  }}
                  onMouseLeave={() => setHoveredCountryCode(null)}
                  onClick={() => {
                    if (!countryCode || !isInteractive) {
                      return;
                    }

                    const nextParams = new URLSearchParams(searchParams.toString());
                    nextParams.set("country", countryCode);
                    router.replace(`${pathname}?${nextParams.toString()}`, { scroll: false });
                  }}
                  className={cx(
                    "transition-colors duration-200",
                    isInteractive ? "cursor-pointer" : "cursor-default"
                  )}
                  style={{
                    default: {
                      fill: fillForCountry(country, isSelected),
                      stroke: isSelected ? "#0f172a" : "#cbd5e1",
                      strokeWidth: isSelected ? 1.2 : 0.6,
                      outline: "none"
                    },
                    hover: {
                      fill: isInteractive ? "#0f766e" : fillForCountry(country, isSelected),
                      stroke: "#0f172a",
                      strokeWidth: 1,
                      outline: "none"
                    },
                    pressed: {
                      fill: "#134e4a",
                      stroke: "#0f172a",
                      strokeWidth: 1.2,
                      outline: "none"
                    }
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>
    </div>
  );
}
