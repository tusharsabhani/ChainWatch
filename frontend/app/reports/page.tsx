import { ReportsWorkspace } from "@/components/reports/reports-workspace";

type SearchParams = Record<string, string | string[] | undefined>;

function readSearchParam(searchParams: SearchParams, key: string) {
  const value = searchParams[key];
  return Array.isArray(value) ? value[0] : value;
}

export default function ReportsPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  return (
    <ReportsWorkspace
      initialGenerateScopeType={readSearchParam(searchParams, "scopeType") || "dashboard"}
      initialGenerateScopeId={readSearchParam(searchParams, "scopeId") || null}
      initialGenerateReportType={readSearchParam(searchParams, "reportType") || "risk_summary"}
    />
  );
}
