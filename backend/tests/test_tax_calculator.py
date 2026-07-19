import pytest
from pydantic import ValidationError

from app.schemas.tax import (
    RegimeRecommendation,
    TaxComparisonRequest,
)
from app.services.tax_calculator import (
    calculate_hra_exemption,
    compare_tax_regimes,
    to_decimal,
)


def build_request(**overrides) -> TaxComparisonRequest:
    payload = {
        "tax_year": "2026-27",
        "age_group": "under_60",
        "employer_type": "private_or_other",
        "annual_gross_salary": 1_500_000,
        "annual_basic_salary": 600_000,
        "annual_hra_received": 0,
        "annual_rent_paid": 0,
        "is_metro_city": False,
        "professional_tax_paid": 0,
        "section_80c": 0,
        "section_80d": 0,
        "section_80ccd_1b": 0,
        "home_loan_interest_self_occupied": 0,
        "other_old_regime_deductions": 0,
        "employer_nps_contribution": 0,
        "other_taxable_income": 0,
        "has_business_income": False,
        "has_special_rate_income": False,
        "has_foreign_income": False,
    }

    payload.update(overrides)

    return TaxComparisonRequest(**payload)


def test_new_regime_has_zero_tax_at_salaried_limit():
    request = build_request(
        annual_gross_salary=1_275_000,
        annual_basic_salary=600_000,
    )

    result = compare_tax_regimes(request)

    assert result.new_regime.taxable_income == 1_200_000
    assert result.new_regime.rebate == 60_000
    assert result.new_regime.total_tax == 0
    assert (
        result.recommended_regime
        == RegimeRecommendation.NEW_REGIME
    )


def test_new_regime_marginal_relief_above_rebate_limit():
    request = build_request(
        annual_gross_salary=1_285_000,
        annual_basic_salary=600_000,
    )

    result = compare_tax_regimes(request)

    assert result.new_regime.taxable_income == 1_210_000
    assert result.new_regime.tax_before_rebate == 61_500
    assert result.new_regime.marginal_relief == 51_500
    assert result.new_regime.income_tax_after_relief == 10_000
    assert result.new_regime.health_and_education_cess == 400
    assert result.new_regime.total_tax == 10_400


def test_old_regime_can_win_with_large_eligible_deductions():
    request = build_request(
        annual_gross_salary=2_000_000,
        annual_basic_salary=1_000_000,
        annual_hra_received=600_000,
        annual_rent_paid=600_000,
        is_metro_city=True,
        professional_tax_paid=2_400,
        section_80c=150_000,
        section_80d=50_000,
        section_80ccd_1b=50_000,
        home_loan_interest_self_occupied=200_000,
        employer_nps_contribution=140_000,
    )

    result = compare_tax_regimes(request)

    assert result.old_regime.hra_exemption == 500_000
    assert result.old_regime.taxable_income == 897_600
    assert (
        result.recommended_regime
        == RegimeRecommendation.OLD_REGIME
    )
    assert (
        result.old_regime.total_tax
        < result.new_regime.total_tax
    )


def test_hra_exemption_uses_lowest_permitted_amount():
    exemption = calculate_hra_exemption(
        annual_hra_received=to_decimal(600_000),
        annual_rent_paid=to_decimal(600_000),
        annual_basic_salary=to_decimal(1_000_000),
        is_metro_city=True,
    )

    assert exemption == to_decimal(500_000)


def test_new_regime_ignores_old_regime_deductions():
    request = build_request(
        annual_gross_salary=1_500_000,
        annual_basic_salary=700_000,
        section_80c=150_000,
        section_80d=100_000,
        section_80ccd_1b=50_000,
        home_loan_interest_self_occupied=200_000,
        professional_tax_paid=2_400,
    )

    result = compare_tax_regimes(request)

    assert result.new_regime.hra_exemption == 0
    assert result.new_regime.professional_tax_deduction == 0
    assert result.new_regime.chapter_vi_a_deductions == 0
    assert result.new_regime.home_loan_interest_deduction == 0


def test_business_income_is_rejected():
    with pytest.raises(
        ValidationError,
        match="does not support business or professional income",
    ):
        build_request(has_business_income=True)


def test_special_rate_income_is_rejected():
    with pytest.raises(
        ValidationError,
        match="does not support capital gains",
    ):
        build_request(has_special_rate_income=True)


def test_income_above_supported_limit_is_rejected():
    with pytest.raises(
        ValidationError,
        match="supports gross income up to",
    ):
        build_request(
            annual_gross_salary=4_900_000,
            other_taxable_income=200_000,
        )