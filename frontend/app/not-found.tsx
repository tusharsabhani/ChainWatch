import Link from "next/link";

import { MaterialIcon } from "@/components/material-icon";
import { PageHeader } from "@/components/page-header";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

export default function NotFound() {
  return (
    <div className="space-y-6 p-4 lg:p-8">
      <PageHeader
        title="Page not found"
        description="That route is not part of the ChainWatch workspace."
        breadcrumbs={[
          { label: "ChainWatch", href: "/" },
          { label: "Missing route" }
        ]}
        badge="Route missing"
      />

      <SectionCard
        title="The requested workspace view is unavailable"
        eyebrow="Navigation fallback"
        trailing={<StatusPill tone="caution">404</StatusPill>}
      >
        <div className="space-y-5">
          <div className="flex h-20 w-20 items-center justify-center rounded-lg border border-outline-variant bg-surface-container-low text-secondary">
            <MaterialIcon icon="travel_explore" className="text-[34px]" />
          </div>
          <p className="max-w-2xl text-sm leading-7 text-slate-600">
            The frontend foundation only wires the documented routes. If you followed an
            older link, return to the dashboard or jump back into one of the active
            workspace surfaces from the main navigation.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg border border-outline-variant bg-white px-4 py-2 font-label text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-700 transition hover:border-secondary hover:text-secondary"
          >
            <MaterialIcon icon="arrow_back" className="text-[16px]" />
            Return to dashboard
          </Link>
        </div>
      </SectionCard>
    </div>
  );
}
