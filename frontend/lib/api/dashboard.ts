import { apiRequest } from "@/lib/api/client";
import type {
  DashboardAlertsQuery,
  DashboardAlertsResponse,
  DashboardSummaryQuery,
  DashboardSummaryResponse
} from "@/lib/api/types";

export function getDashboardSummary(query: DashboardSummaryQuery = {}) {
  return apiRequest<DashboardSummaryResponse>("dashboard/summary", { query });
}

export function getDashboardAlerts(query: DashboardAlertsQuery = {}) {
  return apiRequest<DashboardAlertsResponse>("dashboard/alerts", { query });
}
