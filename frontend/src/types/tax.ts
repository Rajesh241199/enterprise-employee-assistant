export type TaxYear = "2026-27";

export type AgeGroup =
  | "under_60"
  | "age_60_to_79"
  | "age_80_plus";

export type EmployerType =
  | "private_or_other"
  | "central_or_state_government";

export type RegimeRecommendation =
  | "old_regime"
  | "new_regime"
  | "nearly_equal";

export type TaxComparisonRequest = {
  tax_year: TaxYear;
  age_group: AgeGroup;
  employer_type: EmployerType;

  annual_gross_salary: number;
  annual_basic_salary: number;

  annual_hra_received: number;
  annual_rent_paid: number;
  is_metro_city: boolean;

  professional_tax_paid: number;

  section_80c: number;
  section_80d: number;
  section_80ccd_1b: number;

  home_loan_interest_self_occupied: number;
  other_old_regime_deductions: number;

  employer_nps_contribution: number;
  other_taxable_income: number;

  has_business_income: boolean;
  has_special_rate_income: boolean;
  has_foreign_income: boolean;
};

export type TaxRegimeBreakdown = {
  gross_salary: number;
  other_taxable_income: number;

  hra_exemption: number;
  standard_deduction: number;
  professional_tax_deduction: number;

  chapter_vi_a_deductions: number;
  home_loan_interest_deduction: number;
  employer_nps_deduction: number;

  taxable_income: number;

  tax_before_rebate: number;
  rebate: number;
  marginal_relief: number;
  income_tax_after_relief: number;

  health_and_education_cess: number;
  total_tax: number;
};

export type TaxComparisonResponse = {
  tax_year: TaxYear;

  old_regime: TaxRegimeBreakdown;
  new_regime: TaxRegimeBreakdown;

  recommended_regime: RegimeRecommendation;
  estimated_annual_saving: number;
  reason: string;

  calculation_version: string;
  assumptions: string[];
  disclaimer: string;
};