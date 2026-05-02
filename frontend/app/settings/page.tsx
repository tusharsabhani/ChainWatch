import { ErrorState } from "@/components/states/error-state";
import { EmptyState } from "@/components/states/empty-state";
import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { ImportControlPanel } from "@/components/settings/import-control-panel";
import { StatusPill } from "@/components/status-pill";
import { getHealth, getImports } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";
import { formatDateTime } from "@/lib/utils";

function ProviderRow({
  icon,
  title,
  subtitle,
  status,
  tone
}: {
  icon: string;
  title: string;
  subtitle: string;
  status: string;
  tone: "success" | "caution" | "danger";
}) {
  return (
    <div className="flex items-center justify-between border-b border-outline-variant px-4 py-4 last:border-b-0">
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center bg-slate-100 text-slate-500">
          <MaterialIcon icon={icon} className="text-[18px]" />
        </div>
        <div>
          <p className="font-data text-base text-slate-950">{title}</p>
          <p className="mt-1 font-label text-[10px] uppercase tracking-[0.16em] text-slate-500">
            {subtitle}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={
            tone === "success"
              ? "h-2 w-2 rounded-full bg-secondary"
              : tone === "caution"
                ? "h-2 w-2 rounded-full bg-caution"
                : "h-2 w-2 rounded-full bg-error"
          }
        />
        <span
          className={
            tone === "success"
              ? "font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-secondary"
              : tone === "caution"
                ? "font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-caution"
                : "font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-error"
          }
        >
          {status}
        </span>
      </div>
    </div>
  );
}

export default async function SettingsPage() {
  const [healthResult, importsResult] = await Promise.all([
    safeApiCall(() => getHealth()),
    safeApiCall(() => getImports())
  ]);

  const health = healthResult.data;
  const imports = importsResult.data;

  const providerItems: Array<{
    icon: string;
    title: string;
    subtitle: string;
    status: string;
    tone: "success" | "caution" | "danger";
  }> = health
    ? [
        {
          icon: "travel_explore",
          title: "Search Adapter",
          subtitle: "EXTERNAL INTELLIGENCE FEEDS",
          status: health.providers.searchConfigured ? "Connected" : "Offline",
          tone: health.providers.searchConfigured ? "success" : "caution"
        },
        {
          icon: "psychology",
          title: "LLM Adapter",
          subtitle: "NARRATIVE SUMMARIZATION",
          status: health.providers.llmConfigured ? "Connected" : "Offline",
          tone: health.providers.llmConfigured ? "success" : "caution"
        },
        {
          icon: "description",
          title: "Reports Background Task",
          subtitle: "ASYNC REPORT GENERATION",
          status: health.backgroundTasks.reportsEnabled ? "Enabled" : "Disabled",
          tone: health.backgroundTasks.reportsEnabled ? "success" : "danger"
        },
        {
          icon: "sync",
          title: "External Risk Refresh",
          subtitle: "CACHE REVALIDATION",
          status: health.backgroundTasks.externalRiskRefreshEnabled ? "Enabled" : "Disabled",
          tone: health.backgroundTasks.externalRiskRefreshEnabled ? "success" : "danger"
        }
      ]
    : [];
  const warningItems = health
    ? [
        !health.providers.searchConfigured
          ? "Search adapter is offline, so external-risk and cited map/dashboard evidence may remain empty."
          : null,
        !health.providers.llmConfigured
          ? "LLM adapter is offline, so chat and summaries fall back to deterministic composition."
          : null,
        !health.backgroundTasks.reportsEnabled
          ? "Background report generation is disabled, so queued reports will not complete automatically."
          : null,
        !health.backgroundTasks.externalRiskRefreshEnabled
          ? "External-risk cache refresh is disabled, so stale country data will not self-refresh in the background."
          : null
      ].filter(Boolean)
    : [];

  return (
    <div className="bg-background p-4 lg:p-8 lg:pt-6">
      <section className="space-y-6 lg:hidden">
        <div>
          <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
            System Settings
          </h1>
          <p className="mt-1 text-[15px] text-slate-700">
            Runtime health, provider readiness, and recent import activity.
          </p>
        </div>

        {warningItems.length > 0 ? (
          <SectionCard title="Operational Warnings" eyebrow="Live provider status">
            <div className="space-y-3">
              {warningItems.map((warning) => (
                <div key={warning} className="rounded-lg border border-caution/20 bg-caution/10 px-4 py-3 text-sm text-caution">
                  {warning}
                </div>
              ))}
            </div>
          </SectionCard>
        ) : null}

        {health ? (
          <SectionCard title="Runtime Health" eyebrow="Live backend preview">
            <div className="grid gap-4">
              <div className="rounded-lg border border-outline-variant bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  App Status
                </p>
                <p className="mt-3 font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
                  {health.status.toUpperCase()}
                </p>
                <p className="mt-2 text-sm text-slate-600">Version {health.appVersion}</p>
              </div>
              <div className="rounded-lg border border-outline-variant bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Database
                </p>
                <p className="mt-3 font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
                  {health.database.status}
                </p>
                <p className="mt-2 font-mono text-xs text-slate-600">{health.database.path}</p>
              </div>
              <div className="rounded-lg border border-outline-variant bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Managed Cache
                </p>
                <p className="mt-3 font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
                  Ready
                </p>
                <p className="mt-2 font-mono text-xs text-slate-600">{health.storage.cachePath}</p>
              </div>
            </div>
          </SectionCard>
        ) : (
          <ErrorState
            title="Runtime status unavailable"
            message="The frontend could not reach the backend health endpoint."
          />
        )}

        <SectionCard title="Import Data" eyebrow="Live local ingestion">
          <ImportControlPanel />
        </SectionCard>

        {health ? (
          <SectionCard title="Provider Readiness" eyebrow="Live configuration state" className="p-0">
            <div className="divide-y divide-outline-variant">
              {providerItems.map((item) => (
                <ProviderRow key={item.title} {...item} />
              ))}
            </div>
          </SectionCard>
        ) : null}

        <SectionCard
          title="Import History"
          eyebrow="Recent runs"
        >
          {imports ? (
            imports.items.length > 0 ? (
              <div className="space-y-3">
                {imports.items.slice(0, 5).map((item) => (
                  <div key={item.id} className="rounded-lg border border-outline-variant bg-surface-container-low p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-data text-sm text-slate-950">{item.filename}</p>
                        <p className="mt-1 font-label text-[10px] uppercase tracking-[0.16em] text-slate-500">
                          {item.importType}
                        </p>
                      </div>
                      <StatusPill tone={item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "caution"}>
                        {item.status}
                      </StatusPill>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-3 text-xs text-slate-600">
                      <span>Rows {item.rowCount}</span>
                      <span>Inserted {item.insertedCount}</span>
                      <span>Errors {item.errorCount}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No imports yet"
                description="Run the seed flow or import one of the supported CSVs to populate this table."
              />
            )
          ) : (
            <ErrorState title="Import history unavailable" message="The recent imports feed could not be loaded." />
          )}
        </SectionCard>
      </section>

      <section className="hidden space-y-6 lg:block">
        {warningItems.length > 0 ? (
          <SectionCard title="Operational Warnings" eyebrow="Live provider status">
            <div className="grid gap-3 xl:grid-cols-2">
              {warningItems.map((warning) => (
                <div key={warning} className="rounded-lg border border-caution/20 bg-caution/10 px-4 py-3 text-sm text-caution">
                  {warning}
                </div>
              ))}
            </div>
          </SectionCard>
        ) : null}

        <div className="grid grid-cols-12 gap-6">
          <SectionCard title="Import Data" eyebrow="Live local ingestion" className="col-span-12">
            <ImportControlPanel />
          </SectionCard>
        </div>

        <div className="grid grid-cols-12 gap-6">
          <SectionCard title="Provider Readiness" eyebrow="External intelligence feeds status" className="col-span-5 p-0">
            {health ? (
              <div className="divide-y divide-outline-variant">
                {providerItems.map((item) => (
                  <ProviderRow key={item.title} {...item} />
                ))}
              </div>
            ) : (
              <div className="p-6">
                <ErrorState
                  title="Provider state unavailable"
                  message="Provider readiness depends on the backend health endpoint."
                />
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Import History"
            eyebrow="Last ingestion operations"
            className="col-span-7"
          >
            {imports ? (
              imports.items.length > 0 ? (
                <div className="overflow-hidden rounded-lg border border-outline-variant">
                  <div className="grid grid-cols-[1.2fr,1.4fr,0.8fr,0.7fr] gap-4 border-b border-outline-variant bg-surface-container-low px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                    <span>Batch ID</span>
                    <span>Source</span>
                    <span>Time</span>
                    <span>Status</span>
                  </div>
                  <div className="divide-y divide-outline-variant">
                    {imports.items.slice(0, 6).map((item) => (
                      <div
                        key={item.id}
                        className="grid grid-cols-[1.2fr,1.4fr,0.8fr,0.7fr] gap-4 px-4 py-4"
                      >
                        <span className="font-data text-sm text-slate-900">{item.id}</span>
                        <span className="font-data text-sm text-slate-700">{item.filename}</span>
                        <span className="font-data text-sm text-slate-700">
                          {formatDateTime(item.completedAt)}
                        </span>
                        <StatusPill tone={item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "caution"}>
                          {item.status}
                        </StatusPill>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="No imports yet"
                  description="Run the local seed flow or upload one of the supported source files to populate the import history panel."
                />
              )
            ) : (
              <ErrorState title="Import history unavailable" message="The recent imports feed could not be loaded." />
            )}
          </SectionCard>
        </div>

      </section>
    </div>
  );
}
