import { apiClient } from "./client";
import type {
  TaxComparisonRequest,
  TaxComparisonResponse,
} from "../types/tax";

export async function compareTaxRegimes(
  payload: TaxComparisonRequest
): Promise<TaxComparisonResponse> {
  const response = await apiClient.post<TaxComparisonResponse>(
    "/api/tax/compare",
    payload
  );

  return response.data;
}