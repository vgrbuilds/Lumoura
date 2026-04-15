from fastapi import APIRouter, Depends, Header, HTTPException, Request

from src.core.dependencies import get_current_user
from src.schemas.billing import (
    BillingConfigResponse,
    CreatePlanRequest,
    CreateSubscriptionRequest,
    SubscriptionCreateResponse,
    SubscriptionSummary,
    WebhookAck,
)
from src.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])
billing_service = BillingService()


@router.get("/config", response_model=BillingConfigResponse)
def get_billing_config() -> BillingConfigResponse:
    return BillingConfigResponse(**billing_service.get_public_config())


@router.get("/plans")
def list_plans():
    return {"plans": billing_service.list_plans()}


@router.post("/plans/sync")
def sync_plan(payload: CreatePlanRequest):
    try:
        return billing_service.sync_plan_to_razorpay(payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/subscriptions", response_model=SubscriptionCreateResponse)
def create_subscription(
    payload: CreateSubscriptionRequest,
    current_user=Depends(get_current_user),
) -> SubscriptionCreateResponse:
    try:
        result = billing_service.create_subscription(
            user_id=current_user["user_id"],
            plan_code=payload.plan_code,
            customer_email=payload.customer_email,
            customer_contact=payload.customer_contact,
            start_at=payload.start_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SubscriptionCreateResponse(**result)


@router.get("/subscriptions/me")
def list_subscriptions(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    return {"user_id": user_id, "subscriptions": billing_service.list_subscriptions(user_id)}


@router.get("/subscriptions/summary")
def list_subscription_summary(current_user=Depends(get_current_user)) -> list[SubscriptionSummary]:
    user_id = current_user["user_id"]
    subscriptions = billing_service.list_subscriptions(user_id)
    return [
        SubscriptionSummary(
            id=sub["id"],
            user_id=sub.get("user_id", user_id),
            plan_code=sub.get("plan_code", "monthly"),
            razorpay_plan_id=sub.get("razorpay_plan_id", ""),
            razorpay_subscription_id=sub.get("razorpay_subscription_id", ""),
            status=sub.get("status", "unknown"),
            credits_per_cycle=int(sub.get("credits_per_cycle", 0)),
            next_charge_at=sub.get("charge_at"),
            last_credited_at=sub.get("last_credited_at"),
        )
        for sub in subscriptions
    ]


@router.post("/webhooks/razorpay", response_model=WebhookAck)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
) -> WebhookAck:
    body = await request.body()
    try:
        status_code, payload = billing_service.handle_webhook(body, x_razorpay_signature)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if status_code >= 400:
        raise HTTPException(status_code=status_code, detail=payload["message"])

    return WebhookAck(**payload)
