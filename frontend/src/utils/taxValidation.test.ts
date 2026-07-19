import {
  describe,
  expect,
  it,
} from "vitest";

import type {
  TaxComparisonRequest,
} from "../types/tax";

import {
  toAmount,
  validateTaxComparisonRequest,
} from "./taxValidation";


function buildPayload(
  overrides: Partial<TaxComparisonRequest> = {}
): TaxComparisonRequest {
  return {
    tax_year: "2026-27",
    age_group: "under_60",
    employer_type: "private_or_other",

    annual_gross_salary: 1_275_000,
    annual_basic_salary: 600_000,

    annual_hra_received: 0,
    annual_rent_paid: 0,
    is_metro_city: false,

    professional_tax_paid: 0,

    section_80c: 0,
    section_80d: 0,
    section_80ccd_1b: 0,

    home_loan_interest_self_occupied: 0,
    other_old_regime_deductions: 0,

    employer_nps_contribution: 0,
    other_taxable_income: 0,

    has_business_income: false,
    has_special_rate_income: false,
    has_foreign_income: false,

    ...overrides,
  };
}


describe("toAmount", () => {
  it("converts a valid amount", () => {
    expect(toAmount("1275000")).toBe(1_275_000);
  });

  it("converts an empty value to zero", () => {
    expect(toAmount("")).toBe(0);
  });

  it("does not permit negative values", () => {
    expect(toAmount("-5000")).toBe(0);
  });

  it("converts invalid values to zero", () => {
    expect(toAmount("invalid")).toBe(0);
  });
});


describe("validateTaxComparisonRequest", () => {
  it("accepts a valid payload", () => {
    expect(
      validateTaxComparisonRequest(buildPayload())
    ).toBeNull();
  });

  it("requires annual gross salary", () => {
    const result = validateTaxComparisonRequest(
      buildPayload({
        annual_gross_salary: 0,
      })
    );

    expect(result).toBe(
      "Enter your annual gross salary."
    );
  });

  it("rejects basic salary above gross salary", () => {
    const result = validateTaxComparisonRequest(
      buildPayload({
        annual_gross_salary: 500_000,
        annual_basic_salary: 600_000,
      })
    );

    expect(result).toContain(
      "cannot exceed annual gross salary"
    );
  });

  it("requires basic salary for HRA calculation", () => {
    const result = validateTaxComparisonRequest(
      buildPayload({
        annual_basic_salary: 0,
        annual_hra_received: 200_000,
        annual_rent_paid: 240_000,
      })
    );

    expect(result).toContain(
      "Annual basic salary is required"
    );
  });

  it("rejects income above supported scope", () => {
    const result = validateTaxComparisonRequest(
      buildPayload({
        annual_gross_salary: 4_900_000,
        annual_basic_salary: 2_000_000,
        other_taxable_income: 200_000,
      })
    );

    expect(result).toContain("₹50,00,000");
  });
});