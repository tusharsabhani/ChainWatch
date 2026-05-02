"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { MaterialIcon } from "@/components/material-icon";
import { StatusPill } from "@/components/status-pill";
import type { ImportStartResponse } from "@/lib/api/types";
import { localApiRequest, safeLocalApiCall } from "@/lib/local-api";
import { cx } from "@/lib/utils";

const IMPORT_TYPES = [
  {
    key: "products",
    label: "Products",
    description: "Catalog rows with SKU, product name, and category."
  },
  {
    key: "sales",
    label: "Sales",
    description: "Historical demand rows for seasonality and spike analysis."
  },
  {
    key: "inventory",
    label: "Inventory",
    description: "Current stock, reserved quantities, and inbound positions."
  },
  {
    key: "suppliers",
    label: "Suppliers",
    description: "Supplier master data and sourcing region coverage."
  }
] as const;

type ImportTypeKey = (typeof IMPORT_TYPES)[number]["key"];

export function ImportControlPanel({
  variant = "surface"
}: {
  variant?: "surface" | "inverted";
}) {
  const router = useRouter();
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [selectedFiles, setSelectedFiles] = useState<Record<ImportTypeKey, File | null>>({
    products: null,
    sales: null,
    inventory: null,
    suppliers: null
  });
  const [expandedImportType, setExpandedImportType] = useState<ImportTypeKey | null>(null);
  const [draggingImportType, setDraggingImportType] = useState<ImportTypeKey | null>(null);
  const [pendingImportType, setPendingImportType] = useState<ImportTypeKey | null>(null);
  const [banner, setBanner] = useState<{
    tone: "success" | "danger" | "caution";
    message: string;
  } | null>(null);

  const panelTone = useMemo(
    () =>
      variant === "inverted"
        ? {
            surface: "border-white/10 bg-white/5 text-white",
            subtle: "text-white/70",
            accent: "text-white/60",
            dropzone: "border-white/15 bg-slate-950/25 text-white hover:border-white/30 hover:bg-slate-950/40",
            active: "border-secondary/60 bg-secondary/15",
            filename: "text-white/80",
            helper: "text-white/55"
          }
        : {
            surface: "border-outline-variant bg-white text-slate-950",
            subtle: "text-slate-600",
            accent: "text-slate-500",
            dropzone: "border-outline-variant bg-surface-container-low text-slate-950 hover:border-secondary/40 hover:bg-secondary/5",
            active: "border-secondary/50 bg-secondary/10",
            filename: "text-slate-700",
            helper: "text-slate-500"
          },
    [variant]
  );

  function updateSelectedFile(importType: ImportTypeKey, file: File | null) {
    setSelectedFiles((current) => ({ ...current, [importType]: file }));
  }

  function handleFileSelection(importType: ImportTypeKey, fileList: FileList | null) {
    const file = fileList?.[0] ?? null;
    if (!file) {
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setBanner({
        tone: "caution",
        message: `Please choose a CSV file for the ${importType} import.`
      });
      return;
    }

    updateSelectedFile(importType, file);
    setBanner(null);
  }

  async function handleSubmit(importType: ImportTypeKey) {
    const file = selectedFiles[importType];
    if (!file) {
      setBanner({
        tone: "caution",
        message: `Choose a CSV file for the ${importType} import first.`
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setPendingImportType(importType);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ImportStartResponse>(`imports/${importType}`, {
        method: "POST",
        body: formData
      })
    );
    setPendingImportType(null);

    if (!result.data) {
      setBanner({
        tone: "danger",
        message: result.error?.message || `The ${importType} import failed.`
      });
      return;
    }

    setBanner({
      tone: "success",
      message: `${file.name} imported as ${result.data.id}.`
    });
    updateSelectedFile(importType, null);
    const input = fileInputRefs.current[importType];
    if (input) {
      input.value = "";
    }
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <div className={cx("rounded-lg border p-4", panelTone.surface)}>
        <div className="flex items-start gap-3">
          <MaterialIcon
            icon="upload_file"
            className={cx("mt-0.5 text-[18px]", panelTone.accent)}
          />
          <div>
            <p className={cx("font-label text-[10px] font-semibold uppercase tracking-[0.16em]", panelTone.accent)}>
              CSV upload
            </p>
            <p className="mt-2 text-sm leading-6">
              Open any dataset below, then drag in a CSV or browse from your machine. Each upload is staged locally, then sent through the same backend import flow.
            </p>
          </div>
        </div>
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

      <div className="space-y-4">
        {IMPORT_TYPES.map((item) => {
          const selectedFile = selectedFiles[item.key];
          const isDragging = draggingImportType === item.key;
          const isPending = pendingImportType === item.key;
          const isExpanded = expandedImportType === item.key;

          return (
            <div
              key={item.key}
              className={cx("rounded-lg border p-4", panelTone.surface)}
            >
              <button
                type="button"
                onClick={() =>
                  setExpandedImportType((current) => (current === item.key ? null : item.key))
                }
                className="flex w-full items-start justify-between gap-3 text-left"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <p className="font-data text-base">{item.label}</p>
                    <StatusPill tone="neutral">{item.key}</StatusPill>
                  </div>
                  <p className={cx("mt-1 text-sm leading-6", panelTone.subtle)}>{item.description}</p>
                  {selectedFile ? (
                    <p className={cx("mt-2 truncate font-mono text-xs", panelTone.helper)}>
                      Ready: {selectedFile.name}
                    </p>
                  ) : null}
                </div>
                <MaterialIcon
                  icon={isExpanded ? "expand_less" : "expand_more"}
                  className={cx("mt-0.5 text-[20px]", panelTone.accent)}
                />
              </button>

              {isExpanded ? (
                <div className="mt-4 space-y-3 border-t border-outline-variant pt-4">
                <input
                  ref={(node) => {
                    fileInputRefs.current[item.key] = node;
                  }}
                  type="file"
                  accept=".csv,text/csv"
                  className="hidden"
                  onChange={(event) => handleFileSelection(item.key, event.target.files)}
                />

                <button
                  type="button"
                  onClick={() => fileInputRefs.current[item.key]?.click()}
                  onDragEnter={(event) => {
                    event.preventDefault();
                    setDraggingImportType(item.key);
                  }}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDraggingImportType(item.key);
                  }}
                  onDragLeave={(event) => {
                    event.preventDefault();
                    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                      setDraggingImportType((current) => (current === item.key ? null : current));
                    }
                  }}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDraggingImportType(null);
                    handleFileSelection(item.key, event.dataTransfer.files);
                  }}
                  className={cx(
                    "flex min-h-36 w-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed px-4 py-5 text-center transition",
                    panelTone.dropzone,
                    isDragging ? panelTone.active : null
                  )}
                >
                  <MaterialIcon icon="upload" className="text-[20px]" />
                  <span className="font-label text-[10px] font-semibold uppercase tracking-[0.18em]">
                    Drag & drop CSV
                  </span>
                  <span className={cx("text-sm", panelTone.subtle)}>or click to browse</span>
                  <span className={cx("font-mono text-xs", panelTone.helper)}>Accepted format: .csv</span>
                </button>

                <div
                  className={cx(
                    "rounded-lg border px-3 py-3 text-sm",
                    variant === "inverted"
                      ? "border-white/10 bg-slate-950/25"
                      : "border-outline-variant bg-surface-container-low"
                  )}
                >
                  {selectedFile ? (
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className={cx("truncate font-data", panelTone.filename)}>{selectedFile.name}</p>
                        <p className={cx("mt-1 text-xs", panelTone.helper)}>
                          {(selectedFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          updateSelectedFile(item.key, null);
                          const input = fileInputRefs.current[item.key];
                          if (input) {
                            input.value = "";
                          }
                        }}
                        className={cx("shrink-0 text-xs underline underline-offset-4", panelTone.subtle)}
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <p className={cx("text-sm", panelTone.helper)}>No file selected yet.</p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => void handleSubmit(item.key)}
                  disabled={isPending}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-secondary px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white disabled:opacity-60"
                >
                  <MaterialIcon icon="publish" className="text-[16px]" />
                  {isPending ? `Importing ${item.label}` : `Import ${item.label}`}
                </button>
              </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}
