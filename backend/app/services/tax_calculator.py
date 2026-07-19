from decimal import Decimal, ROUND_HALF_UP

from app.schemas.tax import (
    AgeGroup,
    EmployerType,
    RegimeRecommendation,
    TaxComparisonRequest,
    TaxComparisonResponse,
    TaxRegimeBreakdown,
)
from app.tax_rules.ty_2026_27 import (
    CALCULATION_VERSION,
    CESS_RATE,
    GOVERNMENT_OLD_EMPLOYER_NPS_RATE,
    NEARLY_EQUAL_THRESHOLD,
    NEW_EMPLOYER_NPS_RATE,
    NEW_REBATE_INCOME_LIMIT,
    NEW_REBATE_MAXIMUM,
    NEW_REGIME_SLABS,
    NEW_STANDARD_DEDUCTION,
    OLD_REBATE_INCOME_LIMIT,
    OLD_REBATE_MAXIMUM,
    OLD_REGIME_SLABS_60_TO_79,
    OLD_REGIME_SLABS_80_PLUS,
    OLD_REGIME_SLABS_UNDER_60,
    OLD_STANDARD_DEDUCTION,
    PRIVATE_OLD_EMPLOYER_NPS_RATE,
    SECTION_80C_LIMIT,
    SECTION_80CCD_1B_LIMIT,
    SECTION_80D_LIMIT,
    SELF_OCCUPIED_HOME_LOAN_INTEREST_LIMIT,
    TaxSlab,
    ZERO,
)


def to_decimal(value: float | int | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


def round_rupee(value: Decimal) -> Decimal:
    return value.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )


def to_response_amount(value: Decimal) -> float:
    return float(round_rupee(max(value, ZERO)))


def calculate_progressive_tax(
    taxable_income: Decimal,
    slabs: tuple[TaxSlab, ...],
) -> Decimal:
    remaining_income = max(taxable_income, ZERO)
    lower_limit = ZERO
    calculated_tax = ZERO

    for upper_limit, rate in slabs:
        if remaining_income <= ZERO:
            break

        if upper_limit is None:
            taxable_in_slab = remaining_income
        else:
            slab_width = upper_limit - lower_limit
            taxable_in_slab = min(remaining_income, slab_width)

        calculated_tax += taxable_in_slab * rate
        remaining_income -= taxable_in_slab

        if upper_limit is not None:
            lower_limit = upper_limit

    return max(calculated_tax, ZERO)


def get_old_regime_slabs(
    age_group: AgeGroup,
) -> tuple[TaxSlab, ...]:
    if age_group == AgeGroup.AGE_60_TO_79:
        return OLD_REGIME_SLABS_60_TO_79

    if age_group == AgeGroup.AGE_80_PLUS:
        return OLD_REGIME_SLABS_80_PLUS

    return OLD_REGIME_SLABS_UNDER_60


def calculate_hra_exemption(
    annual_hra_received: Decimal,
    annual_rent_paid: Decimal,
    annual_basic_salary: Decimal,
    is_metro_city: bool,
) -> Decimal:
    if (
        annual_hra_received <= ZERO
        or annual_rent_paid <= ZERO
        or annual_basic_salary <= ZERO
    ):
        return ZERO

    rent_minus_ten_percent_salary = max(
        annual_rent_paid - (annual_basic_salary * Decimal("0.10")),
        ZERO,
    )

    salary_percentage = (
        Decimal("0.50")
        if is_metro_city
        else Decimal("0.40")
    )

    percentage_of_salary = annual_basic_salary * salary_percentage

    return max(
        min(
            annual_hra_received,
            rent_minus_ten_percent_salary,
            percentage_of_salary,
        ),
        ZERO,
    )


def calculate_employer_nps_deduction(
    contribution: Decimal,
    annual_basic_salary: Decimal,
    permitted_rate: Decimal,
) -> Decimal:
    if contribution <= ZERO or annual_basic_salary <= ZERO:
        return ZERO

    return min(
        contribution,
        annual_basic_salary * permitted_rate,
    )


def build_breakdown(
    *,
    gross_salary: Decimal,
    other_taxable_income: Decimal,
    hra_exemption: Decimal,
    standard_deduction: Decimal,
    professional_tax_deduction: Decimal,
    chapter_vi_a_deductions: Decimal,
    home_loan_interest_deduction: Decimal,
    employer_nps_deduction: Decimal,
    taxable_income: Decimal,
    tax_before_rebate: Decimal,
    rebate: Decimal,
    marginal_relief: Decimal,
    income_tax_after_relief: Decimal,
    cess: Decimal,
    total_tax: Decimal,
) -> TaxRegimeBreakdown:
    return TaxRegimeBreakdown(
        gross_salary=to_response_amount(gross_salary),
        other_taxable_income=to_response_amount(other_taxable_income),
        hra_exemption=to_response_amount(hra_exemption),
        standard_deduction=to_response_amount(standard_deduction),
        professional_tax_deduction=to_response_amount(
            professional_tax_deduction
        ),
        chapter_vi_a_deductions=to_response_amount(
            chapter_vi_a_deductions
        ),
        home_loan_interest_deduction=to_response_amount(
            home_loan_interest_deduction
        ),
        employer_nps_deduction=to_response_amount(
            employer_nps_deduction
        ),
        taxable_income=to_response_amount(taxable_income),
        tax_before_rebate=to_response_amount(tax_before_rebate),
        rebate=to_response_amount(rebate),
        marginal_relief=to_response_amount(marginal_relief),
        income_tax_after_relief=to_response_amount(
            income_tax_after_relief
        ),
        health_and_education_cess=to_response_amount(cess),
        total_tax=to_response_amount(total_tax),
    )


def calculate_old_regime(
    payload: TaxComparisonRequest,
) -> tuple[TaxRegimeBreakdown, Decimal]:
    gross_salary = to_decimal(payload.annual_gross_salary)
    basic_salary = to_decimal(payload.annual_basic_salary)
    other_income = to_decimal(payload.other_taxable_income)

    hra_exemption = calculate_hra_exemption(
        annual_hra_received=to_decimal(payload.annual_hra_received),
        annual_rent_paid=to_decimal(payload.annual_rent_paid),
        annual_basic_salary=basic_salary,
        is_metro_city=payload.is_metro_city,
    )

    salary_after_hra = max(
        gross_salary - hra_exemption,
        ZERO,
    )

    standard_deduction = min(
        OLD_STANDARD_DEDUCTION,
        salary_after_hra,
    )

    remaining_salary_after_standard_deduction = max(
        salary_after_hra - standard_deduction,
        ZERO,
    )

    professional_tax_deduction = min(
        to_decimal(payload.professional_tax_paid),
        remaining_salary_after_standard_deduction,
    )

    taxable_salary = max(
        salary_after_hra
        - standard_deduction
        - professional_tax_deduction,
        ZERO,
    )

    section_80c = min(
        to_decimal(payload.section_80c),
        SECTION_80C_LIMIT,
    )

    section_80d = min(
        to_decimal(payload.section_80d),
        SECTION_80D_LIMIT,
    )

    section_80ccd_1b = min(
        to_decimal(payload.section_80ccd_1b),
        SECTION_80CCD_1B_LIMIT,
    )

    other_old_deductions = to_decimal(
        payload.other_old_regime_deductions
    )

    chapter_vi_a_deductions = (
        section_80c
        + section_80d
        + section_80ccd_1b
        + other_old_deductions
    )

    home_loan_interest_deduction = min(
        to_decimal(payload.home_loan_interest_self_occupied),
        SELF_OCCUPIED_HOME_LOAN_INTEREST_LIMIT,
    )

    old_nps_rate = (
        GOVERNMENT_OLD_EMPLOYER_NPS_RATE
        if payload.employer_type
        == EmployerType.CENTRAL_OR_STATE_GOVERNMENT
        else PRIVATE_OLD_EMPLOYER_NPS_RATE
    )

    employer_nps_deduction = calculate_employer_nps_deduction(
        contribution=to_decimal(
            payload.employer_nps_contribution
        ),
        annual_basic_salary=basic_salary,
        permitted_rate=old_nps_rate,
    )

    taxable_income = max(
        taxable_salary
        + other_income
        - chapter_vi_a_deductions
        - home_loan_interest_deduction
        - employer_nps_deduction,
        ZERO,
    )

    tax_before_rebate = calculate_progressive_tax(
        taxable_income=taxable_income,
        slabs=get_old_regime_slabs(payload.age_group),
    )

    rebate = ZERO

    if taxable_income <= OLD_REBATE_INCOME_LIMIT:
        rebate = min(
            tax_before_rebate,
            OLD_REBATE_MAXIMUM,
        )

    income_tax_after_relief = max(
        tax_before_rebate - rebate,
        ZERO,
    )

    marginal_relief = ZERO
    cess = income_tax_after_relief * CESS_RATE
    total_tax = income_tax_after_relief + cess

    breakdown = build_breakdown(
        gross_salary=gross_salary,
        other_taxable_income=other_income,
        hra_exemption=hra_exemption,
        standard_deduction=standard_deduction,
        professional_tax_deduction=professional_tax_deduction,
        chapter_vi_a_deductions=chapter_vi_a_deductions,
        home_loan_interest_deduction=home_loan_interest_deduction,
        employer_nps_deduction=employer_nps_deduction,
        taxable_income=taxable_income,
        tax_before_rebate=tax_before_rebate,
        rebate=rebate,
        marginal_relief=marginal_relief,
        income_tax_after_relief=income_tax_after_relief,
        cess=cess,
        total_tax=total_tax,
    )

    return breakdown, round_rupee(total_tax)


def calculate_new_regime(
    payload: TaxComparisonRequest,
) -> tuple[TaxRegimeBreakdown, Decimal]:
    gross_salary = to_decimal(payload.annual_gross_salary)
    basic_salary = to_decimal(payload.annual_basic_salary)
    other_income = to_decimal(payload.other_taxable_income)

    standard_deduction = min(
        NEW_STANDARD_DEDUCTION,
        gross_salary,
    )

    employer_nps_deduction = calculate_employer_nps_deduction(
        contribution=to_decimal(
            payload.employer_nps_contribution
        ),
        annual_basic_salary=basic_salary,
        permitted_rate=NEW_EMPLOYER_NPS_RATE,
    )

    taxable_income = max(
        gross_salary
        + other_income
        - standard_deduction
        - employer_nps_deduction,
        ZERO,
    )

    tax_before_rebate = calculate_progressive_tax(
        taxable_income=taxable_income,
        slabs=NEW_REGIME_SLABS,
    )

    rebate = ZERO
    marginal_relief = ZERO

    if taxable_income <= NEW_REBATE_INCOME_LIMIT:
        rebate = min(
            tax_before_rebate,
            NEW_REBATE_MAXIMUM,
        )
    else:
        income_above_rebate_limit = (
            taxable_income - NEW_REBATE_INCOME_LIMIT
        )

        marginal_relief = max(
            tax_before_rebate - income_above_rebate_limit,
            ZERO,
        )

    income_tax_after_relief = max(
        tax_before_rebate - rebate - marginal_relief,
        ZERO,
    )

    cess = income_tax_after_relief * CESS_RATE
    total_tax = income_tax_after_relief + cess

    breakdown = build_breakdown(
        gross_salary=gross_salary,
        other_taxable_income=other_income,
        hra_exemption=ZERO,
        standard_deduction=standard_deduction,
        professional_tax_deduction=ZERO,
        chapter_vi_a_deductions=ZERO,
        home_loan_interest_deduction=ZERO,
        employer_nps_deduction=employer_nps_deduction,
        taxable_income=taxable_income,
        tax_before_rebate=tax_before_rebate,
        rebate=rebate,
        marginal_relief=marginal_relief,
        income_tax_after_relief=income_tax_after_relief,
        cess=cess,
        total_tax=total_tax,
    )

    return breakdown, round_rupee(total_tax)


def compare_tax_regimes(
    payload: TaxComparisonRequest,
) -> TaxComparisonResponse:
    old_regime, old_tax = calculate_old_regime(payload)
    new_regime, new_tax = calculate_new_regime(payload)

    tax_difference = abs(old_tax - new_tax)

    if tax_difference <= NEARLY_EQUAL_THRESHOLD:
        recommendation = RegimeRecommendation.NEARLY_EQUAL
        reason = (
            "The estimated annual tax difference is ₹"
            f"{int(tax_difference):,}, so both regimes are nearly equal. "
            "Review compliance effort and deduction certainty before choosing."
        )
    elif old_tax < new_tax:
        recommendation = RegimeRecommendation.OLD_REGIME
        reason = (
            "The old tax regime has the lower estimated tax liability by ₹"
            f"{int(tax_difference):,}, mainly because of the eligible "
            "exemptions and deductions provided."
        )
    else:
        recommendation = RegimeRecommendation.NEW_REGIME
        reason = (
            "The new tax regime has the lower estimated tax liability by ₹"
            f"{int(tax_difference):,} after applying its lower slab rates "
            "and available deductions."
        )

    return TaxComparisonResponse(
        tax_year=payload.tax_year,
        old_regime=old_regime,
        new_regime=new_regime,
        recommended_regime=recommendation,
        estimated_annual_saving=float(tax_difference),
        reason=reason,
        calculation_version=CALCULATION_VERSION,
        assumptions=[
            "The taxpayer is a resident salaried individual.",
            "The calculation covers Tax Year 2026–27 only.",
            "Gross salary includes taxable employer NPS contribution where applicable.",
            "Only ordinary-rate salary and other taxable income are included.",
            "The calculation excludes business income and special-rate income.",
            "The calculation supports income up to ₹50,00,000 and excludes surcharge.",
            "Old-regime deduction inputs are treated as eligible amounts declared by the user.",
            "Salary and deduction values are not persisted by this calculator.",
        ],
        disclaimer=(
            "This is an indicative tax comparison based on the information "
            "provided. It is not tax, legal, or investment advice. Confirm "
            "eligibility and final liability using the official Income Tax "
            "Department calculator or a qualified tax professional."
        ),
    )


def answer_tax_question() -> str:
    return (
        "I can compare the old and new tax regimes using a deterministic "
        "tax calculator. Please open the Tax Regime Comparison form and provide "
        "your annual salary, basic salary, HRA and rent details, eligible "
        "deductions, employer NPS contribution, and other taxable income. "
        "Your financial inputs will not be stored in the application database."
    )