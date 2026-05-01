import { MaterialIcon } from "@/components/material-icon";
import { StatusPill } from "@/components/status-pill";

function DesktopChat() {
  return (
    <div className="hidden h-[calc(100vh-128px)] bg-background lg:flex">
      <section className="flex min-w-0 flex-1 flex-col border-r border-slate-200">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-3xl space-y-8">
            <div className="py-10 text-center">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
                <MaterialIcon icon="smart_toy" className="text-[30px]" />
              </div>
              <h1 className="font-display text-[20px] font-semibold tracking-[-0.01em] text-slate-950">
                How can I assist your operations today?
              </h1>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Query real-time shipping feeds, ERP data, and global news monitors to mitigate
                supply chain risks.
              </p>
            </div>

            <div className="flex justify-end gap-4">
              <div className="max-w-xl">
                <div className="rounded-xl rounded-tr-none bg-primary-container p-5 text-white">
                  <p className="text-base leading-7">
                    Which suppliers are most exposed to the current port strike on the US East
                    Coast?
                  </p>
                </div>
                <p className="mt-2 text-right font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">
                  10:42 AM
                </p>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-slate-500">
                <MaterialIcon icon="person" className="text-[18px]" />
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container">
                <MaterialIcon icon="smart_toy" className="text-[18px]" />
              </div>
              <div className="flex-1">
                <div className="rounded-xl rounded-tl-none border border-slate-200 bg-white p-6 shadow-overlay">
                  <p className="text-base leading-7 text-slate-800">
                    Based on current shipping manifests and ERP purchase orders, three primary
                    suppliers have significant exposure to the US East Coast port strikes.
                  </p>

                  <div className="mt-6 space-y-3">
                    <div className="border-l-4 border-error bg-surface-container-low p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-data text-lg text-slate-950">Nexus Components Ltd.</h3>
                          <p className="mt-1 text-sm text-slate-600">4 active shipments diverted</p>
                        </div>
                        <div className="text-right">
                          <p className="font-display text-[24px] font-semibold text-error">$2.4M</p>
                          <p className="font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">
                            Risk Value
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="border-l-4 border-orange-500 bg-surface-container-low p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="font-data text-lg text-slate-950">Vertex Logistics China</h3>
                          <p className="mt-1 text-sm text-slate-600">12 containers at Port of Savannah</p>
                        </div>
                        <div className="text-right">
                          <p className="font-display text-[24px] font-semibold text-orange-500">$1.1M</p>
                          <p className="font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">
                            Risk Value
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
                    <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
                      Sources:
                    </span>
                    <button className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-secondary">
                      <MaterialIcon icon="description" className="text-[14px]" />
                      ERP_PO_DATA_Q4.csv
                    </button>
                    <button className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] text-secondary">
                      <MaterialIcon icon="link" className="text-[14px]" />
                      Maritime Global Feed
                    </button>
                  </div>
                </div>

                <p className="mt-2 font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">
                  10:43 AM • AI analysis complete
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-200 bg-white/70 p-6 backdrop-blur-sm">
          <div className="mb-4 flex gap-2 overflow-x-auto no-scrollbar">
            {[
              "Draft mitigation plan for Nexus",
              "View alternative shipping routes",
              "Contact procurement team"
            ].map((label) => (
              <button
                key={label}
                className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-600"
              >
                {label}
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-overlay">
            <textarea
              rows={3}
              readOnly
              value=""
              placeholder="Ask about risks, suppliers, or logistics..."
              className="w-full resize-none border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
            />
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-3 text-slate-500">
                <MaterialIcon icon="attach_file" className="text-[20px]" />
                <MaterialIcon icon="image" className="text-[20px]" />
              </div>
              <button className="inline-flex items-center gap-2 rounded bg-secondary px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white">
                Send
                <MaterialIcon icon="send" className="text-[16px]" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <aside className="w-[340px] border-l border-slate-200 bg-white">
        <div className="border-b border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-display text-[20px] font-semibold tracking-[-0.01em] text-slate-950">
                Intelligence Stack
              </h2>
              <p className="mt-2 text-sm text-slate-600">Active data nodes used for this query</p>
            </div>
            <StatusPill tone="success">Live</StatusPill>
          </div>
        </div>

        <div className="space-y-6 p-6">
          {[
            {
              icon: "database",
              title: "ERP Data",
              body: "Queried purchase orders, delivery dates, and SKU inventory levels."
            },
            {
              icon: "sailing",
              title: "Real-time Shipping Feeds",
              body: "Satellite vessel tracking and port congestion metrics."
            },
            {
              icon: "public",
              title: "News Monitor",
              body: "Scanned local and global news sources for strike updates."
            }
          ].map((item) => (
            <div key={item.title} className="flex gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded bg-surface-container-low text-slate-500">
                <MaterialIcon icon={item.icon} className="text-[18px]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-data text-base text-slate-950">{item.title}</p>
                  <span className="h-2 w-2 rounded-full bg-secondary" />
                </div>
                <p className="mt-1 text-sm leading-6 text-slate-600">{item.body}</p>
              </div>
            </div>
          ))}

          <div className="border-t border-slate-200 pt-6">
            <p className="font-label text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
              Impact zone visualization
            </p>
            <div className="mt-4 overflow-hidden rounded-lg border border-surface-container-high">
              <div className="relative h-44 bg-[linear-gradient(135deg,#111827,#6b7280)]">
                <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:18px_18px]" />
                <div className="absolute inset-x-0 top-1/2 flex -translate-y-1/2 justify-center">
                  <span className="rounded bg-white px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-900">
                    32 Vessels Idle
                  </span>
                </div>
              </div>
            </div>
          </div>

          <button className="inline-flex w-full items-center justify-center gap-2 rounded border border-slate-200 bg-white px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700">
            <MaterialIcon icon="download" className="text-[16px]" />
            Export Risk Brief
          </button>
        </div>
      </aside>
    </div>
  );
}

function MobileChat() {
  return (
    <div className="min-h-screen bg-background pb-72">
      <header className="fixed left-0 right-0 top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button className="text-slate-900">
            <MaterialIcon icon="arrow_back" className="text-[22px]" />
          </button>
          <div>
            <p className="font-display text-[18px] font-semibold tracking-[-0.02em] text-slate-950">
              ChainWatch
            </p>
            <div className="mt-1 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-secondary" />
              <span className="font-label text-[10px] uppercase tracking-[0.16em] text-slate-500">
                System Active • Risk AI
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-slate-600">
          <MaterialIcon icon="inventory_2" className="text-[20px]" />
          <MaterialIcon icon="more_vert" className="text-[20px]" />
        </div>
      </header>

      <main className="space-y-6 px-4 pb-6 pt-20">
        <div className="space-y-3 py-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-container text-white">
            <MaterialIcon icon="chat" className="text-[30px]" />
          </div>
          <h1 className="font-display text-[20px] font-semibold tracking-[-0.01em] text-slate-950">
            How can I assist your operations today?
          </h1>
          <p className="mx-auto max-w-xs text-sm leading-6 text-slate-600">
            Monitor risks, check product movement, or generate reports with natural language.
          </p>
        </div>

        <div className="max-w-[85%] space-y-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-overlay">
            <p className="text-base leading-7 text-slate-800">
              I&apos;ve completed the morning analysis for the <strong className="text-secondary">North East Region</strong>. I detected a potential logistical bottleneck in the supply chain near the Boston hub.
            </p>
            <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4">
              <MaterialIcon icon="report" filled className="text-[18px] text-error" />
              <span className="font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-error">
                Severity: High Risk
              </span>
            </div>
          </div>
          <p className="font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">08:42 AM</p>
        </div>

        <div className="ml-auto max-w-[85%] space-y-2">
          <div className="rounded-xl rounded-br-none bg-primary-container p-4 text-white shadow-overlay">
            <p className="text-base leading-7">
              What data sources were used to identify this bottleneck?
            </p>
          </div>
          <p className="text-right font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">
            08:43 AM
          </p>
        </div>

        <div className="max-w-[85%] space-y-2">
          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-overlay">
            <p className="text-base leading-7 text-slate-800">
              The identification was cross-referenced across 4 primary operational streams. You can review the specific datasets below.
            </p>
            <div className="mt-4 flex items-center justify-between rounded-lg border border-slate-100 bg-surface-container-low p-3">
              <div className="flex items-center gap-3">
                <MaterialIcon icon="database" className="text-[18px] text-secondary" />
                <span className="font-data text-sm text-slate-950">4 Active Data Streams</span>
              </div>
              <MaterialIcon icon="keyboard_arrow_up" className="text-[18px] text-slate-500" />
            </div>
          </div>
          <p className="font-label text-[10px] uppercase tracking-[0.16em] text-slate-400">08:43 AM</p>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
          {["Detailed Report", "View on Map", "Share Alert"].map((label) => (
            <button
              key={label}
              className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-4 py-3 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-700 shadow-overlay"
            >
              {label}
            </button>
          ))}
        </div>

        <section className="rounded-t-[20px] bg-white p-6 shadow-[0_-6px_20px_rgba(15,23,42,0.08)]">
          <div className="mx-auto mb-6 h-1 w-12 rounded-full bg-slate-300" />
          <h2 className="font-display text-[20px] font-semibold tracking-[-0.01em] text-slate-950">
            Data Sources Used
          </h2>
          <div className="mt-6 space-y-4">
            {[
              { icon: "local_shipping", title: "Real-time GPS Fleet Data", detail: "Updated 2m ago" },
              { icon: "thermometer", title: "Cold-Chain Sensors", detail: "External API" },
              { icon: "cloud", title: "Regional Weather Radar", detail: "Live Satellite Feed" }
            ].map((item) => (
              <div key={item.title} className="flex items-center justify-between rounded-xl border border-slate-100 p-3">
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary/10 text-secondary">
                    <MaterialIcon icon={item.icon} className="text-[18px]" />
                  </div>
                  <div>
                    <p className="font-data text-sm text-slate-950">{item.title}</p>
                    <p className="mt-1 text-xs text-slate-500">{item.detail}</p>
                  </div>
                </div>
                <span className="h-2 w-2 rounded-full bg-secondary-container" />
              </div>
            ))}
          </div>
          <button className="mt-6 w-full rounded-xl bg-primary px-4 py-4 font-label text-[10px] font-semibold uppercase tracking-[0.16em] text-white">
            Close Details
          </button>
        </section>
      </main>

      <div className="fixed bottom-0 left-0 right-0 border-t border-slate-200 bg-white p-4 pb-8 shadow-[0_-4px_16px_rgba(15,23,42,0.08)]">
        <div className="flex items-end gap-3">
          <div className="flex flex-1 items-center gap-2 rounded-2xl border border-slate-200 bg-surface-container-low px-2 py-2">
            <button className="text-slate-500">
              <MaterialIcon icon="add_circle" className="text-[22px]" />
            </button>
            <textarea
              rows={1}
              readOnly
              value=""
              placeholder="Ask about risks or reports..."
              className="flex-1 resize-none border-none bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none"
            />
            <button className="text-slate-500">
              <MaterialIcon icon="mic" className="text-[22px]" />
            </button>
          </div>
          <button className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary text-white shadow-overlay">
            <MaterialIcon icon="send" className="text-[20px]" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <>
      <MobileChat />
      <DesktopChat />
    </>
  );
}
