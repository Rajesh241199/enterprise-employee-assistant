import type {
  TaxComparisonRequest,
} from "../types/tax";


export function toAmount(value: string): number {
  const parsedValue = Number(value || 0);

  if (!Number.isFinite(parsedValue)) {
    return 0;
  }

  return Math.max(parsedValue, 0);
}


export function validateTaxComparisonRequest(
  payload: TaxComparisonRequest
): string | null {
  if (payload.annual_gross_salary <= 0) {
    return "Enter your annual gross salary.";
  }

  if (
    payload.annual_basic_salary >
    payload.annual_gross_salary
  ) {
    return (
      "Annual basic salary cannot exceed " +
      "annual gross salary."
    );
  }

  const requiresBasicSalary =
    payload.annual_hra_received > 0 ||
    payload.annual_rent_paid > 0 ||
    payload.employer_nps_contribution > 0;

  if (
    requiresBasicSalary &&
    payload.annual_basic_salary <= 0
  ) {
    return (
      "Annual basic salary is required when " +
      "HRA, rent, or employer NPS is entered."
    );
  }

  const totalSupportedIncome =
    payload.annual_gross_salary +
    payload.other_taxable_income;

  if (totalSupportedIncome > 5_000_000) {
    return (
      "Version 1 supports gross income up to " +
      "₹50,00,000 only."
    );
  }

  return null;
}