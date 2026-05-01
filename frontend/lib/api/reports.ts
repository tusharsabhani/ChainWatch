import { apiRequest } from "@/lib/api/client";
import type {
  ReportDetailResponse,
  ReportGenerateRequest,
  ReportGenerateResponse,
  ReportsListQuery,
  ReportsListResponse
} from "@/lib/api/types";

export function getReports(query: ReportsListQuery = {}) {
  return apiRequest<ReportsListResponse>("reports", { query });
}

export function getReportDetail(reportId: string) {
  return apiRequest<ReportDetailResponse>(`reports/${reportId}`);
}

export function generateReport(payload: ReportGenerateRequest) {
  return apiRequest<ReportGenerateResponse>("reports/generate", {
    method: "POST",
    body: payload
  });
}
