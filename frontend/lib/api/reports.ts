import { apiRequest } from "@/lib/api/client";
import type {
  ReportDetailResponse,
  ReportGenerateRequest,
  ReportGenerateResponse,
  ReportsListResponse
} from "@/lib/api/types";

export function getReports() {
  return apiRequest<ReportsListResponse>("reports");
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
