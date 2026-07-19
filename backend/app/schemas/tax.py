from enum import Enum

from pydantic import BaseModel, Field, model_validator


MAX_SUPPORTED_INCOME = 5_000_000


class TaxYear(str, Enum):
    TAX_YEAR_2026_27 = "2026-27"


class AgeGroup(str, Enum):
    UNDER_60 = "under_60"
    AGE_60_TO_79 = "age_60_to_79"
    AGE_80_PLUS = "age_80_plus"


class EmployerType(str, Enum):
    PRIVATE_OR_OTHER = "private_or_other"
    CENTRAL_OR_STATE_GOVERNMENT = "central_or_state_government"


class RegimeRecommendation(str, Enum):
    OLD_REGIME = "old_regime"
    NEW_REGIME = "new_regime"
    NEARLY_EQUAL = "nearly_equal"


class TaxComparisonRequest(BaseModel):
    tax_year: TaxYear = TaxYear.TAX_YEAR_2026_27
    age_group: AgeGroup = AgeGroup.UNDER_60
    employer_type: EmployerType = EmployerType.PRIVATE_OR_OTHER

    annual_gross_salary: float = Field(
        ...,
        gt=0,
        le=MAX_SUPPORTED_INCOME,
        description=(
            "Annual gross taxable salary before exemptions and deductions. "
            "Include employer NPS contribution if it forms part of salary."
        ),
    )

    annual_basic_salary: float = Field(
        default=0,
        ge=0,
        le=MAX_SUPPORTED_INCOME,
        description=(
            "Annual basic salary plus eligible dearness allowance used for "
            "HRA and employer NPS limits."
        ),
    )

    annual_hra_received: float = Field(default=0, ge=0, le=MAX_SUPPORTED_INCOME)
    annual_rent_paid: float = Field(default=0, ge=0, le=MAX_SUPPORTED_INCOME)
    is_metro_city: bool = False

    professional_tax_paid: float = Field(default=0, ge=0, le=20_000)

    section_80c: float = Field(default=0, ge=0, le=500_000)
    section_80d: float = Field(default=0, ge=0, le=200_000)
    section_80ccd_1b: float = Field(default=0, ge=0, le=200_000)

    home_loan_interest_self_occupied: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    other_old_regime_deductions: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
        description=(
            "Other eligible old-regime deductions already validated by the user."
        ),
    )

    employer_nps_contribution: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    other_taxable_income: float = Field(
        default=0,
        ge=0,
        le=MAX_SUPPORTED_INCOME,
        description=(
            "Ordinary-rate taxable income such as interest income. "
            "Do not include capital gains or other special-rate income."
        ),
    )

    has_business_income: bool = False
    has_special_rate_income: bool = False
    has_foreign_income: bool = False

    @model_validator(mode="after")
    def validate_supported_scope(self) -> "TaxComparisonRequest":
        if self.annual_basic_salary > self.annual_gross_salary:
            raise ValueError(
                "Annual basic salary cannot exceed annual gross salary."
            )

        if (
            self.annual_hra_received > 0
            or self.annual_rent_paid > 0
            or self.employer_nps_contribution > 0
        ) and self.annual_basic_salary <= 0:
            raise ValueError(
                "Annual basic salary is required for HRA or employer NPS calculations."
            )

        if self.annual_gross_salary + self.other_taxable_income > MAX_SUPPORTED_INCOME:
            raise ValueError(
                "Version 1 supports gross income up to ₹50,00,000 only."
            )

        if self.has_business_income:
            raise ValueError(
                "Version 1 does not support business or professional income."
            )

        if self.has_special_rate_income:
            raise ValueError(
                "Version 1 does not support capital gains, crypto, lottery, "
                "or other special-rate income."
            )

        if self.has_foreign_income:
            raise ValueError(
                "Version 1 does not support foreign income or foreign tax credit."
            )

        return self


class TaxRegimeBreakdown(BaseModel):
    gross_salary: float
    other_taxable_income: float

    hra_exemption: float
    standard_deduction: float
    professional_tax_deduction: float

    chapter_vi_a_deductions: float
    home_loan_interest_deduction: float
    employer_nps_deduction: float

    taxable_income: float

    tax_before_rebate: float
    rebate: float
    marginal_relief: float
    income_tax_after_relief: float

    health_and_education_cess: float
    total_tax: float


class TaxComparisonResponse(BaseModel):
    tax_year: TaxYear
    old_regime: TaxRegimeBreakdown
    new_regime: TaxRegimeBreakdown

    recommended_regime: RegimeRecommendation
    estimated_annual_saving: float
    reason: str

    calculation_version: str
    assumptions: list[str]
    disclaimer: str