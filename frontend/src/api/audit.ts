import {
  apiClient,
} from "./client";

import type {
  AuditLogFilters,
  AuditLogListResponse,
  AuditLogSummary,
} from "../types/audit";


export async function getAuditLogs(
  offset = 0,
  limit = 50,
  filters: AuditLogFilters = {}
): Promise<AuditLogListResponse> {
  const response =
    await apiClient.get<AuditLogListResponse>(
      "/api/admin/audit-logs",
      {
        params: {
          offset,
          limit,
          ...filters,
        },
      }
    );

  return response.data;
}


export async function getAuditSummary():
  Promise<AuditLogSummary> {
  const response =
    await apiClient.get<AuditLogSummary>(
      "/api/admin/audit-logs/summary"
    );

  return response.data;
}