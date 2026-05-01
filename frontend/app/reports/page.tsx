import { ReportsWorkspace } from "@/components/reports/reports-workspace";
import { ErrorState } from "@/components/states/error-state";
import { getReportDetail, getReports } from "@/lib/api";
import { safeApiCall } from "@/lib/api/client";

type SearchParams = Record<string, string | string[] | undefined>;

function readSearchParam(searchParams: SearchParams, key: string) {
  const value = searchParams[key];
  return Array.isArray(value) ? value[0] : value;
}

export default async function ReportsPage({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const initialFilters = {
    scopeType: readSearchParam(searchParams, "scopeType") || undefined,
    status: readSearchParam(searchParams, "status") || undefined
  };
  const reportsResult = await safeApiCall(() => getReports(initialFilters));
  const reports = reportsResult.data?.items ?? [];
  const selectedReportId =
    readSearchParam(searchParams, "reportId") || reports[0]?.id || null;
  const selectedReportResult = selectedReportId
    ? await safeApiCall(() => getReportDetail(selectedReportId))
    : { data: null, error: null };

  if (reportsResult.error && !reportsResult.data) {
    return (
      <div className="p-4 lg:p-8">
        <ErrorState
          title="Reports workspace unavailable"
          message={reportsResult.error.message}
        />
      </div>
    );
  }

  return (
    <ReportsWorkspace
      initialReports={reports}
      initialSelectedReport={selectedReportResult.data}
      initialFilters={initialFilters}
      initialGenerateScopeType={readSearchParam(searchParams, "scopeType") || "dashboard"}
      initialGenerateScopeId={readSearchParam(searchParams, "scopeId") || null}
      initialGenerateReportType={readSearchParam(searchParams, "reportType") || "risk_summary"}
    />
  );
}
