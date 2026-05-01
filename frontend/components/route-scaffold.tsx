import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

export function RouteScaffold({
  title,
  description,
  breadcrumbs,
  phaseLabel,
  nextMilestone,
  plannedApis,
  children
}: {
  title: string;
  description: string;
  breadcrumbs: { label: string; href?: string }[];
  phaseLabel: string;
  nextMilestone: string;
  plannedApis: string[];
  children?: React.ReactNode;
}) {
  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        description={description}
        breadcrumbs={breadcrumbs}
        badge={phaseLabel}
      />

      <div className="grid gap-4 xl:grid-cols-[1.45fr,1fr]">
        <SectionCard title="Current state" eyebrow="Foundation status">
          <div className="space-y-3 text-sm leading-7 text-slate-600">
            <p>
              This route already lives inside the real operational shell, shares the
              runtime heartbeat, and can use the common loading, empty, error, retry, and
              freshness components from the shared frontend layer.
            </p>
            <p>{nextMilestone}</p>
          </div>
        </SectionCard>

        <SectionCard title="Planned backend feeds" eyebrow="API contracts already live">
          <ul className="space-y-3 text-sm text-slate-900">
            {plannedApis.map((api) => (
              <li
                key={api}
                className="rounded-lg border border-outline-variant bg-surface-container-low px-4 py-3 font-mono text-xs sm:text-sm"
              >
                {api}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <SectionCard
        title="Phase 1 note"
        eyebrow="Visual scaffold"
        trailing={<StatusPill tone="neutral">{phaseLabel}</StatusPill>}
      >
        <p className="max-w-3xl text-sm leading-7 text-slate-600">
          This surface is intentionally shaped like the approved UI mock, while deeper
          live widgets and interactions land in later frontend phases.
        </p>
      </SectionCard>

      {children ? <div>{children}</div> : null}
    </div>
  );
}
