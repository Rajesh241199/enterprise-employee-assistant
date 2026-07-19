from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from app.core.permissions import require_authenticated_user
from app.db.models import User
from app.schemas.tax import (
    TaxComparisonRequest,
    TaxComparisonResponse,
)
from app.services.audit_logger import audit_event
from app.services.tax_calculator import compare_tax_regimes


router = APIRouter()


def get_user_role_value(current_user: User) -> str:
    user_role = getattr(current_user, "role", "")

    if hasattr(user_role, "value"):
        return str(user_role.value)

    return str(user_role)


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def set_private_response_headers(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"


@router.post(
    "/tax/compare",
    response_model=TaxComparisonResponse,
)
def compare_tax_regime_endpoint(
    payload: TaxComparisonRequest,
    request: Request,
    response: Response,
    current_user: User = Depends(require_authenticated_user),
):
    set_private_response_headers(response)

    try:
        result = compare_tax_regimes(payload)

        # Salary, rent, income, deductions and calculated tax
        # are deliberately excluded from audit metadata.
        audit_event(
            event_type="tax.comparison_success",
            outcome="success",
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            actor_user_id=getattr(
                current_user,
                "id",
                None,
            ),
            actor_email=getattr(
                current_user,
                "email",
                None,
            ),
            actor_role=get_user_role_value(current_user),
            client_ip=get_client_ip(request),
            user_agent=request.headers.get(
                "user-agent",
                "unknown",
            ),
            resource_type="tax_comparison",
            resource_id=None,
            metadata={
                "tax_year": result.tax_year.value,
                "recommended_regime": (
                    result.recommended_regime.value
                ),
                "calculation_version": (
                    result.calculation_version
                ),
            },
        )

        return result

    except ValueError as exc:
        audit_event(
            event_type="tax.comparison_failed",
            outcome="failed",
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            actor_user_id=getattr(
                current_user,
                "id",
                None,
            ),
            actor_email=getattr(
                current_user,
                "email",
                None,
            ),
            actor_role=get_user_role_value(current_user),
            client_ip=get_client_ip(request),
            user_agent=request.headers.get(
                "user-agent",
                "unknown",
            ),
            resource_type="tax_comparison",
            resource_id=None,
            metadata={
                "tax_year": payload.tax_year.value,
                "reason": str(exc)[:500],
            },
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc