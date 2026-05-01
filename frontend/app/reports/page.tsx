import { MaterialIcon } from "@/components/material-icon";
import { SectionCard } from "@/components/section-card";
import { StatusPill } from "@/components/status-pill";

const reportRows = [
  {
    title: "Weekly Supply Chain Outlook",
    date: "Oct 24, 2023",
    status: "Ready",
    author: "Local System",
    tone: "success" as const
  },
  {
    title: "Q3 Supplier Exposure Audit",
    date: "Oct 22, 2023",
    status: "Ready",
    author: "Phase 1 Preview",
    tone: "success" as const
  },
  {
    title: "Flash Report: Suez Canal Delay",
    date: "Oct 20, 2023",
    status: "Processing",
    author: "Local System",
    tone: "caution" as const
  }
];

export default function ReportsPage() {
  return (
    <div className="bg-background p-4 lg:p-6 lg:pt-6">
      <section className="space-y-6 lg:hidden">
        <div>
          <h1 className="font-display text-[30px] font-bold tracking-[-0.02em] text-slate-950">
            Reports & Analysis
          </h1>
          <p className="mt-1 text-[15px] text-slate-700">
            Browse generated briefs and preview report detail panels.
          </p>
        </div>

        <div className="space-y-4">
          {reportRows.map((report) => (
            <SectionCard
              key={report.title}
              title={report.title}
              eyebrow={report.date}
              trailing={<StatusPill tone={report.tone}>{report.status}</StatusPill>}
            >
              <p className="text-sm leading-6 text-slate-600">
                Phase 1 preserves the report browsing structure and status treatment while the full
                report viewer lands in a later workflow phase.
              </p>
            </SectionCard>
          ))}
        </div>

        <SectionCard title="Selected preview" eyebrow="Current detail panel">
          <p className="text-sm leading-6 text-slate-600">
            The eventual report detail experience will show markdown content, metadata, artifact
            paths, and generation status from the live backend responses.
          </p>
          <div className="mt-4 rounded-lg border border-surface-container-high bg-surface-container-low p-4">
            <p className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
              Summary preview
            </p>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              Supplier exposure remains concentrated in East Asia and regional port congestion is
              the most persistent external driver this week.
            </p>
          </div>
        </SectionCard>
      </section>

      <section className="hidden h-[calc(100vh-104px)] gap-4 lg:flex">
        <SectionCard
          title="Intelligence Library"
          eyebrow="Report archive"
          trailing={
            <button className="inline-flex items-center gap-2 rounded-lg bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white">
              <MaterialIcon icon="add" className="text-[16px]" />
              Generate New Report
            </button>
          }
          className="flex flex-1 flex-col overflow-hidden"
        >
          <div className="overflow-y-auto no-scrollbar">
            <table className="w-full border-collapse text-left">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-outline-variant font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  <th className="px-4 py-4">Report Name</th>
                  <th className="px-4 py-4">Date Generated</th>
                  <th className="px-4 py-4">Status</th>
                  <th className="px-4 py-4">Created By</th>
                  <th className="px-4 py-4" />
                </tr>
              </thead>
              <tbody className="font-data text-sm">
                {reportRows.map((report, index) => (
                  <tr
                    key={report.title}
                    className={index === 1 ? "border-b border-outline-variant bg-surface-container-low/50" : "border-b border-outline-variant hover:bg-surface-container-low"}
                  >
                    <td className="px-4 py-4 font-semibold text-slate-900">{report.title}</td>
                    <td className="px-4 py-4 text-slate-600">{report.date}</td>
                    <td className="px-4 py-4">
                      <StatusPill tone={report.tone}>{report.status}</StatusPill>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{report.author}</td>
                    <td className="px-4 py-4 text-right">
                      <MaterialIcon icon="chevron_right" className="text-[18px] text-slate-400" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard title="Report Preview" eyebrow="Selected report" className="w-[440px] overflow-hidden">
          <div className="space-y-6">
            <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-data text-lg text-slate-900">Q3 Supplier Exposure Audit</p>
                  <p className="mt-1 text-sm text-slate-600">Generated Oct 22, 2023</p>
                </div>
                <StatusPill tone="success">Ready</StatusPill>
              </div>
            </div>

            <div className="rounded-lg border border-surface-container-high bg-white p-5">
              <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                Markdown preview
              </p>
              <div className="mt-4 space-y-4 text-sm leading-7 text-slate-700">
                <p>
                  East Asia remains the densest exposure cluster, with 3 primary suppliers carrying
                  elevated risk due to freight delay and customs variance.
                </p>
                <p>
                  Inventory buffers remain adequate for the top 20 SKUs, but replenishment windows
                  for seasonal products are tightening.
                </p>
                <p>
                  Later frontend phases will replace this preview shell with the real markdown
                  content from `GET /api/reports/{'{'}report_id{'}'}`.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Artifact paths
                </p>
                <p className="mt-3 font-mono text-xs text-slate-700">/data/reports/json/...</p>
                <p className="mt-1 font-mono text-xs text-slate-700">/data/reports/markdown/...</p>
              </div>
              <div className="rounded-lg border border-surface-container-high bg-surface-container-low p-4">
                <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                  Scope
                </p>
                <p className="mt-3 text-sm text-slate-700">Dashboard risk overview</p>
                <p className="mt-1 text-sm text-slate-500">Structured report shell only in phase 1</p>
              </div>
            </div>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
