"use client";

import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { FreshnessBadge } from "@/components/freshness-badge";
import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";
import type {
  ReportDetailResponse,
  ReportGenerateResponse,
  ReportsListQuery,
  ReportsListResponse
} from "@/lib/api/types";
import { localApiRequest, safeLocalApiCall } from "@/lib/local-api";
import { cx, formatDateTime } from "@/lib/utils";

type ReportItem = ReportsListResponse["items"][number];

const STATUS_OPTIONS = [
  { label: "All statuses", value: "" },
  { label: "Queued", value: "queued" },
  { label: "Running", value: "running" },
  { label: "Completed", value: "completed" },
  { label: "Partial", value: "partial" },
  { label: "Failed", value: "failed" }
] as const;

const SCOPE_OPTIONS = [
  { label: "All scopes", value: "" },
  { label: "Dashboard", value: "dashboard" },
  { label: "Product", value: "product" },
  { label: "Country", value: "country" },
  { label: "Supplier", value: "supplier" },
  { label: "Chat", value: "chat" }
] as const;

const REPORT_TYPE_OPTIONS = [
  { label: "Risk Summary", value: "risk_summary" },
  { label: "Product Risk", value: "product_risk" },
  { label: "Country Risk", value: "country_risk" },
  { label: "Supplier Risk", value: "supplier_risk" },
  { label: "Chat Export", value: "chat_export" }
] as const;

function reportTone(status: string): "success" | "caution" | "danger" | "neutral" {
  if (status === "completed") {
    return "success";
  }
  if (status === "partial" || status === "queued" || status === "running") {
    return "caution";
  }
  if (status === "failed") {
    return "danger";
  }
  return "neutral";
}

function normalizeFilters(filters: ReportsListQuery) {
  return {
    scopeType: filters.scopeType || "",
    status: filters.status || ""
  };
}

export function ReportsWorkspace({
  initialReports,
  initialSelectedReport,
  initialFilters,
  initialGenerateScopeType,
  initialGenerateScopeId,
  initialGenerateReportType
}: {
  initialReports: ReportItem[];
  initialSelectedReport: ReportDetailResponse | null;
  initialFilters: ReportsListQuery;
  initialGenerateScopeType: string;
  initialGenerateScopeId: string | null;
  initialGenerateReportType: string;
}) {
  const [filters, setFilters] = useState(normalizeFilters(initialFilters));
  const [reports, setReports] = useState<ReportItem[]>(initialReports);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(
    initialSelectedReport?.id ?? initialReports[0]?.id ?? null
  );
  const [selectedReport, setSelectedReport] = useState<ReportDetailResponse | null>(
    initialSelectedReport
  );
  const [loadingList, setLoadingList] = useState(false);
  const [loadingReportId, setLoadingReportId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [banner, setBanner] = useState<{
    tone: "success" | "caution" | "danger";
    message: string;
  } | null>(null);
  const [generateForm, setGenerateForm] = useState({
    scopeType: initialGenerateScopeType,
    scopeId: initialGenerateScopeId ?? "",
    reportType: initialGenerateReportType,
    title: ""
  });

  const selectedReportRow = useMemo(
    () => reports.find((item) => item.id === selectedReportId) ?? null,
    [reports, selectedReportId]
  );

  async function loadReports(nextFilters = filters, preferredReportId?: string | null) {
    setLoadingList(true);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ReportsListResponse>("reports", {
        query: {
          scopeType: nextFilters.scopeType || undefined,
          status: nextFilters.status || undefined,
          limit: 30
        }
      })
    );
    setLoadingList(false);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "The report list could not be loaded."
      });
      return;
    }

    setReports(result.data.items);
    const nextSelectedId =
      preferredReportId && result.data.items.some((item) => item.id === preferredReportId)
        ? preferredReportId
        : result.data.items[0]?.id ?? null;
    setSelectedReportId(nextSelectedId);

    if (nextSelectedId) {
      await loadReportDetail(nextSelectedId);
    } else {
      setSelectedReport(null);
    }
  }

  async function loadReportDetail(reportId: string) {
    setLoadingReportId(reportId);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ReportDetailResponse>(`reports/${reportId}`)
    );
    setLoadingReportId(null);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "The report detail could not be loaded."
      });
      return;
    }

    setSelectedReport(result.data);
  }

  async function handleSelectReport(reportId: string) {
    setSelectedReportId(reportId);
    await loadReportDetail(reportId);
  }

  async function handleApplyFilters(nextFilters: typeof filters) {
    setFilters(nextFilters);
    setBanner(null);
    await loadReports(nextFilters, selectedReportId);
  }

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsGenerating(true);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ReportGenerateResponse>("reports/generate", {
        method: "POST",
        body: {
          scopeType: generateForm.scopeType,
          scopeId: generateForm.scopeId.trim() || null,
          reportType: generateForm.reportType,
          title: generateForm.title.trim() || null
        }
      })
    );
    setIsGenerating(false);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || "The report could not be queued."
      });
      return;
    }

    setBanner({
      tone: "success",
      message: `Report ${result.data.id} queued successfully.`
    });
    await loadReports(filters, result.data.id);
  }

  useEffect(() => {
    if (!selectedReport || !selectedReportId) {
      return;
    }

    if (!["queued", "running"].includes(selectedReport.status)) {
      return;
    }

    const intervalId = window.setInterval(async () => {
      await loadReportDetail(selectedReportId);
      await loadReports(filters, selectedReportId);
    }, 2500);

    return () => window.clearInterval(intervalId);
  }, [selectedReport?.status, selectedReportId]);

  return (
    <div className="space-y-6 bg-background p-4 lg:p-6 lg:pt-6">
      <div className="space-y-4">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
              Reports & Analysis
            </h1>
            <p className="mt-1 text-[15px] text-slate-700">
              Browse generated artifacts, queue new summaries, and inspect Markdown plus artifact paths from the live backend.
            </p>
          </div>

          {selectedReport ? (
            <FreshnessBadge
              freshness={selectedReport.freshness}
              lastUpdatedAt={selectedReport.completedAt ?? selectedReport.createdAt}
            />
          ) : null}
        </div>

        {banner ? (
          <div
            className={cx(
              "rounded-lg border px-4 py-3 text-sm",
              banner.tone === "success"
                ? "border-secondary/20 bg-secondary/10 text-secondary"
                : banner.tone === "caution"
                  ? "border-caution/20 bg-caution/10 text-caution"
                  : "border-error/20 bg-error/10 text-error"
            )}
          >
            {banner.message}
          </div>
        ) : null}
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr,1.45fr]">
        <SectionCard title="Generate Report" eyebrow="Queue backend work">
          <form onSubmit={handleGenerate} className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Scope Type
                </span>
                <select
                  value={generateForm.scopeType}
                  onChange={(event) =>
                    setGenerateForm((current) => ({ ...current, scopeType: event.target.value }))
                  }
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
                >
                  {SCOPE_OPTIONS.filter((option) => option.value).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Report Type
                </span>
                <select
                  value={generateForm.reportType}
                  onChange={(event) =>
                    setGenerateForm((current) => ({ ...current, reportType: event.target.value }))
                  }
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
                >
                  {REPORT_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="grid gap-4 sm:grid-cols-[0.8fr,1.2fr]">
              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Scope Id
                </span>
                <input
                  value={generateForm.scopeId}
                  onChange={(event) =>
                    setGenerateForm((current) => ({ ...current, scopeId: event.target.value }))
                  }
                  placeholder="Optional"
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400"
                />
              </label>

              <label className="space-y-2 text-sm text-slate-600">
                <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Title
                </span>
                <input
                  value={generateForm.title}
                  onChange={(event) =>
                    setGenerateForm((current) => ({ ...current, title: event.target.value }))
                  }
                  placeholder="Optional custom title"
                  className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400"
                />
              </label>
            </div>

            <button
              type="submit"
              disabled={isGenerating}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white disabled:opacity-60"
            >
              <MaterialIcon icon="add" className="text-[16px]" />
              {isGenerating ? "Queuing" : "Generate Report"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Filters" eyebrow="Report archive query">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-600">
              <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                Scope Filter
              </span>
              <select
                value={filters.scopeType}
                onChange={(event) =>
                  void handleApplyFilters({
                    ...filters,
                    scopeType: event.target.value
                  })
                }
                className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
              >
                {SCOPE_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-600">
              <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                Status Filter
              </span>
              <select
                value={filters.status}
                onChange={(event) =>
                  void handleApplyFilters({
                    ...filters,
                    status: event.target.value
                  })
                }
                className="w-full rounded-lg border border-outline-variant bg-white px-3 py-2 text-sm text-slate-700"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr,1.25fr]">
        <SectionCard
          title="Report Library"
          eyebrow="Persisted artifacts"
          trailing={
            <StatusPill tone={loadingList ? "caution" : "success"}>
              {loadingList ? "Refreshing" : `${reports.length} loaded`}
            </StatusPill>
          }
          className="overflow-hidden"
        >
          {reports.length > 0 ? (
            <div className="overflow-hidden rounded-lg border border-outline-variant">
              <div className="grid grid-cols-[1.3fr,0.8fr,0.8fr] gap-4 border-b border-outline-variant bg-surface-container-low px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                <span>Report</span>
                <span>Scope</span>
                <span>Status</span>
              </div>
              <div className="divide-y divide-outline-variant">
                {reports.map((report) => (
                  <button
                    key={report.id}
                    type="button"
                    onClick={() => void handleSelectReport(report.id)}
                    className={cx(
                      "grid w-full grid-cols-[1.3fr,0.8fr,0.8fr] gap-4 px-4 py-4 text-left transition",
                      selectedReportId === report.id
                        ? "bg-surface-container-low"
                        : "bg-white hover:bg-surface-container-low/50"
                    )}
                  >
                    <div>
                      <p className="font-data text-sm text-slate-950">{report.title}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {report.id} • {formatDateTime(report.createdAt)}
                      </p>
                    </div>
                    <p className="text-sm text-slate-700">{report.scopeType}</p>
                    <div className="flex items-center justify-between gap-2">
                      <StatusPill tone={reportTone(report.status)}>{report.status}</StatusPill>
                      {loadingReportId === report.id ? (
                        <span className="text-xs text-slate-400">Loading</span>
                      ) : null}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              title="No reports match the filters"
              description="Adjust the scope or status filter, or queue a new report using the generator above."
            />
          )}
        </SectionCard>

        <SectionCard
          title={selectedReport?.title ?? "Report Preview"}
          eyebrow={selectedReportRow ? `Selected • ${selectedReportRow.scopeType}` : "No report selected"}
          trailing={
            selectedReport ? (
              <StatusPill tone={reportTone(selectedReport.status)}>{selectedReport.status}</StatusPill>
            ) : null
          }
        >
          {selectedReport ? (
            <div className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                  <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Scope
                  </p>
                  <p className="mt-2 text-sm text-slate-900">
                    {selectedReport.scopeType}
                    {selectedReport.scopeId ? ` • ${selectedReport.scopeId}` : ""}
                  </p>
                </div>
                <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                  <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                    Created
                  </p>
                  <p className="mt-2 text-sm text-slate-900">{formatDateTime(selectedReport.createdAt)}</p>
                </div>
              </div>

              {selectedReport.summary ? (
                <SectionCard title="Summary" eyebrow="Backend-generated">
                  <p className="text-sm leading-7 text-slate-700">{selectedReport.summary}</p>
                </SectionCard>
              ) : null}

              <SectionCard title="Markdown Preview" eyebrow="Artifact content">
                {selectedReport.markdownPreview ? (
                  <pre className="whitespace-pre-wrap font-body text-sm leading-7 text-slate-700">
                    {selectedReport.markdownPreview}
                  </pre>
                ) : (
                  <EmptyState
                    title="No Markdown preview yet"
                    description="Queued or running reports will show content here once the backend finishes rendering the Markdown artifact."
                  />
                )}
              </SectionCard>

              <SectionCard title="Artifacts" eyebrow="Filesystem paths">
                <div className="space-y-3">
                  <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4 font-mono text-xs text-slate-700">
                    JSON: {selectedReport.jsonPath ?? "Not generated yet"}
                  </div>
                  <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4 font-mono text-xs text-slate-700">
                    Markdown: {selectedReport.markdownPath ?? "Not generated yet"}
                  </div>
                </div>
              </SectionCard>
            </div>
          ) : (
            <EmptyState
              title="Select a report"
              description="Choose a report from the library to inspect its metadata, summary, and Markdown preview."
            />
          )}
        </SectionCard>
      </div>
    </div>
  );
}
