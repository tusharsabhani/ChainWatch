"use client";

import { useState } from "react";
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

export function ImportControlPanel({
  importsPath,
  variant = "surface"
}: {
  importsPath: string;
  variant?: "surface" | "inverted";
}) {
  const router = useRouter();
  const [paths, setPaths] = useState<Record<string, string>>({
    products: "",
    sales: "",
    inventory: "",
    suppliers: ""
  });
  const [pendingImportType, setPendingImportType] = useState<string | null>(null);
  const [banner, setBanner] = useState<{
    tone: "success" | "danger" | "caution";
    message: string;
  } | null>(null);

  async function handleSubmit(importType: string) {
    const filePath = paths[importType]?.trim();
    if (!filePath) {
      setBanner({
        tone: "caution",
        message: `Enter a local file path for the ${importType} import.`
      });
      return;
    }

    setPendingImportType(importType);
    setBanner(null);
    const result = await safeLocalApiCall(() =>
      localApiRequest<ImportStartResponse>(`imports/${importType}`, {
        method: "POST",
        body: { filePath }
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
      message: `${importType} import queued as ${result.data.id}.`
    });
    setPaths((current) => ({ ...current, [importType]: "" }));
    router.refresh();
  }

  return (
    <div className="space-y-4">
      <div
        className={cx(
          "rounded-lg border p-4",
          variant === "inverted"
            ? "border-white/10 bg-white/5 text-white"
            : "border-outline-variant bg-surface-container-low text-slate-700"
        )}
      >
        <div className="flex items-start gap-3">
          <MaterialIcon
            icon="folder_open"
            className={cx(
              "mt-0.5 text-[18px]",
              variant === "inverted" ? "text-white/70" : "text-slate-500"
            )}
          />
          <div>
            <p
              className={cx(
                "font-label text-[10px] font-semibold uppercase tracking-[0.16em]",
                variant === "inverted" ? "text-white/60" : "text-slate-500"
              )}
            >
              Local import mode
            </p>
            <p className="mt-2 text-sm leading-6">
              The backend import API expects a local CSV file path that the backend process can access.
            </p>
            <p
              className={cx(
                "mt-2 font-mono text-xs",
                variant === "inverted" ? "text-white/80" : "text-slate-600"
              )}
            >
              Managed root: {importsPath}
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

      <div className="grid gap-4 xl:grid-cols-2">
        {IMPORT_TYPES.map((item) => (
          <div
            key={item.key}
            className={cx(
              "rounded-lg border p-4",
              variant === "inverted"
                ? "border-white/10 bg-white/5"
                : "border-outline-variant bg-white"
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p
                  className={cx(
                    "font-data text-base",
                    variant === "inverted" ? "text-white" : "text-slate-950"
                  )}
                >
                  {item.label}
                </p>
                <p
                  className={cx(
                    "mt-1 text-sm leading-6",
                    variant === "inverted" ? "text-white/70" : "text-slate-600"
                  )}
                >
                  {item.description}
                </p>
              </div>
              <StatusPill tone="neutral">{item.key}</StatusPill>
            </div>

            <div className="mt-4 space-y-3">
              <input
                value={paths[item.key]}
                onChange={(event) =>
                  setPaths((current) => ({ ...current, [item.key]: event.target.value }))
                }
                placeholder={`/absolute/path/to/${item.key}.csv`}
                className={cx(
                  "w-full rounded-lg border px-3 py-2 text-sm placeholder:text-slate-400",
                  variant === "inverted"
                    ? "border-white/10 bg-slate-950/30 text-white"
                    : "border-outline-variant bg-white text-slate-700"
                )}
              />
              <button
                type="button"
                onClick={() => void handleSubmit(item.key)}
                disabled={pendingImportType === item.key}
                className={cx(
                  "inline-flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.16em] disabled:opacity-60",
                  variant === "inverted"
                    ? "bg-secondary text-white"
                    : "bg-secondary text-white"
                )}
              >
                <MaterialIcon icon="upload_file" className="text-[16px]" />
                {pendingImportType === item.key ? `Importing ${item.label}` : `Import ${item.label}`}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
