import { apiClient } from "./client";

import type {
  CreateEmployeeOnboardingRequest,
  EmployeeOnboardingListResponse,
  EmployeeOnboardingRecord,
  UpdateEmployeeOnboardingRequest,
} from "../types/adminOnboarding";


export async function listEmployeeOnboardingRecords(
  offset = 0,
  limit = 100
): Promise<EmployeeOnboardingListResponse> {
  const response =
    await apiClient.get<EmployeeOnboardingListResponse>(
      "/api/admin/onboarding/employees",
      {
        params: {
          offset,
          limit,
        },
      }
    );

  return response.data;
}


export async function getEmployeeOnboardingRecord(
  userId: number
): Promise<EmployeeOnboardingRecord> {
  const response =
    await apiClient.get<EmployeeOnboardingRecord>(
      `/api/admin/onboarding/employees/${userId}`
    );

  return response.data;
}


export async function createEmployeeOnboardingRecord(
  payload: CreateEmployeeOnboardingRequest
): Promise<EmployeeOnboardingRecord> {
  const response =
    await apiClient.post<EmployeeOnboardingRecord>(
      "/api/admin/onboarding/employees",
      payload
    );

  return response.data;
}


export async function updateEmployeeOnboardingRecord(
  userId: number,
  payload: UpdateEmployeeOnboardingRequest
): Promise<EmployeeOnboardingRecord> {
  const response =
    await apiClient.put<EmployeeOnboardingRecord>(
      `/api/admin/onboarding/employees/${userId}`,
      payload
    );

  return response.data;
}