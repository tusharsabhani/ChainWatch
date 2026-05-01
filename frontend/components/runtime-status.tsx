import { getHealth } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";

function StatusChip({
  label,
  value,
  tone
}: {
  label: string;
  value: string;
  tone: "success" | "caution" | "danger" | "neutral";
}) {
  const toneClasses = {
    success: "border-secondary/20 bg-secondary/10 text-secondary",
    caution: "border-caution/20 bg-caution/10 text-caution",
    danger: "border-error/20 bg-error/10 text-error",
    neutral: "border-slate-300 bg-slate-100 text-slate-700"
  };

  return (
    <div className={`rounded-full border px-3 py-2 ${toneClasses[tone]}`}>
      <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export async function RuntimeStatus() {
  const healthResult = await safeApiCall(() => getHealth());

  if (!healthResult.data) {
    return (
      <div className="inline-flex rounded-full border border-error/20 bg-error/10 px-4 py-3 text-sm text-error">
        Backend unavailable
      </div>
    );
  }

  const { data } = healthResult;

  return (
    <div className="flex flex-wrap items-center justify-end gap-2">
      <StatusChip label="Backend" value={data.status} tone="success" />
      <StatusChip
        label="Database"
        value={data.database.status}
        tone={data.database.status === "connected" ? "neutral" : "danger"}
      />
      <StatusChip
        label="Search"
        value={data.providers.searchConfigured ? "Configured" : "Off"}
        tone={data.providers.searchConfigured ? "success" : "caution"}
      />
      <StatusChip
        label="LLM"
        value={data.providers.llmConfigured ? "Configured" : "Off"}
        tone={data.providers.llmConfigured ? "success" : "caution"}
      />
    </div>
  );
}
