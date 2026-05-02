"use client";

import { useState } from "react";

import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import type { ReportGenerateResponse } from "@/lib/api/types";
import { localApiRequest, safeLocalApiCall } from "@/lib/local-api";
import { cx } from "@/lib/utils";

const SCOPE_OPTIONS = [
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

export function ReportsWorkspace({
  initialGenerateScopeType,
  initialGenerateScopeId,
  initialGenerateReportType
}: {
  initialGenerateScopeType: string;
  initialGenerateScopeId: string | null;
  initialGenerateReportType: string;
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState<{
    tone: "success" | "danger";
    text: string;
  } | null>(null);
  const [generateForm, setGenerateForm] = useState({
    scopeType: initialGenerateScopeType,
    scopeId: initialGenerateScopeId ?? "",
    reportType: initialGenerateReportType,
    title: ""
  });

  async function handleGenerate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsGenerating(true);
    setMessage(null);
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
      setMessage({
        tone: "danger",
        text: result.error?.message || "The report could not be queued."
      });
      return;
    }

    setMessage({
      tone: "success",
      text: `Report ${result.data.id} queued successfully.`
    });
  }

  return (
    <div className="space-y-6 bg-background p-4 lg:p-6 lg:pt-6">
      <div>
        <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
          Reports & Analysis
        </h1>
      </div>

      <SectionCard title="Generate Report">
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
                {SCOPE_OPTIONS.map((option) => (
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

          {message ? (
            <p
              className={cx(
                "text-sm",
                message.tone === "success" ? "text-secondary" : "text-error"
              )}
            >
              {message.text}
            </p>
          ) : null}
        </form>
      </SectionCard>
    </div>
  );
}
