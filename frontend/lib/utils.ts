export function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function formatClockTime(value?: string | null) {
  if (!value) {
    return "--:--";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit"
  }).format(parsed);
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "Not available";
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(parsed);
}

export function formatCompactNumber(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: value >= 100 ? 0 : 1
  }).format(value);
}

export function formatPercent(
  value?: number | null,
  options: {
    scale?: "fraction" | "whole";
    maximumFractionDigits?: number;
  } = {}
) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  const { scale = "whole", maximumFractionDigits = 0 } = options;
  const normalized = scale === "fraction" ? value * 100 : value;

  return `${normalized.toFixed(maximumFractionDigits)}%`;
}

export function formatRiskScore(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "--";
  }

  return value.toFixed(1);
}

export function severityTone(
  severity?: number | null
): "success" | "caution" | "danger" | "neutral" {
  if (severity === null || severity === undefined) {
    return "neutral";
  }

  if (severity >= 4) {
    return "danger";
  }

  if (severity === 3) {
    return "caution";
  }

  return "success";
}

export function toDisplayLabel(value: string) {
  return value
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
