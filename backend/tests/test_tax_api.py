import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api.tax as tax_api
from app.core.permissions import require_authenticated_user
from app.main import app


def valid_payload() -> dict:
    return {
        "tax_year": "2026-27",
        "age_group": "under_60",
        "employer_type": "private_or_other",
        "annual_gross_salary": 1_275_000,
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


@pytest.fixture
def authorized_client(monkeypatch):
    audit_records: list[dict] = []

    def fake_audit_event(**kwargs):
        audit_records.append(kwargs)

    def authenticated_user():
        return SimpleNamespace(
            id=101,
            email="privacy.test@company.com",
            role="employee",
        )

    monkeypatch.setattr(
        tax_api,
        "audit_event",
        fake_audit_event,
    )

    app.dependency_overrides[
        require_authenticated_user
    ] = authenticated_user

    with TestClient(app) as client:
        yield client, audit_records

    app.dependency_overrides.pop(
        require_authenticated_user,
        None,
    )


def test_tax_endpoint_requires_authentication():
    app.dependency_overrides.pop(
        require_authenticated_user,
        None,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/tax/compare",
            json=valid_payload(),
        )

    assert response.status_code in {401, 403}


def test_tax_endpoint_returns_private_cache_headers(
    authorized_client,
):
    client, _audit_records = authorized_client

    response = client.post(
        "/api/tax/compare",
        json=valid_payload(),
    )

    assert response.status_code == 200

    assert (
        response.headers["cache-control"]
        == "no-store, max-age=0"
    )

    assert response.headers["pragma"] == "no-cache"
    assert response.headers["expires"] == "0"


def test_tax_endpoint_returns_expected_result(
    authorized_client,
):
    client, _audit_records = authorized_client

    response = client.post(
        "/api/tax/compare",
        json=valid_payload(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["recommended_regime"] == "new_regime"
    assert data["new_regime"]["taxable_income"] == 1_200_000
    assert data["new_regime"]["total_tax"] == 0
    assert data["calculation_version"] == "ty-2026-27-v1"


def test_financial_values_are_not_written_to_audit_log(
    authorized_client,
):
    client, audit_records = authorized_client

    response = client.post(
        "/api/tax/compare",
        json=valid_payload(),
    )

    assert response.status_code == 200
    assert len(audit_records) == 1

    record = audit_records[0]
    metadata = record["metadata"]

    assert metadata == {
        "tax_year": "2026-27",
        "recommended_regime": "new_regime",
        "calculation_version": "ty-2026-27-v1",
    }

    serialized_record = json.dumps(
        record,
        default=str,
    )

    sensitive_field_names = [
        "annual_gross_salary",
        "annual_basic_salary",
        "annual_hra_received",
        "annual_rent_paid",
        "section_80c",
        "section_80d",
        "section_80ccd_1b",
        "home_loan_interest_self_occupied",
        "employer_nps_contribution",
        "other_taxable_income",
        "taxable_income",
        "total_tax",
    ]

    for field_name in sensitive_field_names:
        assert field_name not in serialized_record

    assert "1275000" not in serialized_record
    assert "600000" not in serialized_record


def test_invalid_payload_is_rejected_before_audit_logging(
    authorized_client,
):
    client, audit_records = authorized_client

    payload = valid_payload()
    payload["annual_gross_salary"] = 500_000
    payload["annual_basic_salary"] = 600_000

    response = client.post(
        "/api/tax/compare",
        json=payload,
    )

    assert response.status_code == 422
    assert audit_records == []


def test_special_rate_income_is_rejected(
    authorized_client,
):
    client, audit_records = authorized_client

    payload = valid_payload()
    payload["has_special_rate_income"] = True

    response = client.post(
        "/api/tax/compare",
        json=payload,
    )

    assert response.status_code == 422
    assert audit_records == []