from typing import Any

from pydantic import BaseModel, Field


class BillingPlan(BaseModel):
    code: str
    name: str
    amount: int
    currency: str = "INR"
    period: str = "monthly"
    interval: int = 1
    total_count: int = 12
    credits_per_cycle: int
    razorpay_plan_id: str | None = None


class BillingConfigResponse(BaseModel):
    key_id: str | None = None
    plans: list[BillingPlan]


class CreatePlanRequest(BaseModel):
    plan_code: str = Field(..., min_length=1)


class CreateSubscriptionRequest(BaseModel):
    plan_code: str = Field(..., min_length=1)
    customer_email: str | None = None
    customer_contact: str | None = None
    start_at: int | None = None


class SubscriptionCreateResponse(BaseModel):
    user_id: str
    plan_code: str
    razorpay_plan_id: str
    razorpay_subscription_id: str
    status: str
    key_id: str | None = None
    checkout: dict[str, Any]


class WebhookAck(BaseModel):
    ok: bool
    message: str


class SubscriptionSummary(BaseModel):
    id: str
    user_id: str
    plan_code: str
    razorpay_plan_id: str
    razorpay_subscription_id: str
    status: str
    credits_per_cycle: int
    next_charge_at: int | None = None
    last_credited_at: int | None = None
