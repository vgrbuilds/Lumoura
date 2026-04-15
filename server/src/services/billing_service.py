from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

from src.core.config import (
    RAZORPAY_KEY_SECRET,
    RAZORPAY_SUBSCRIPTION_PLAN_ID,
    RAZORPAY_TEST_KEY_ID,
    RAZORPAY_WEBHOOK_SECRET,
    SUBSCRIPTION_CURRENCY,
    SUBSCRIPTION_PLAN_AMOUNT,
    SUBSCRIPTION_PLAN_CREDITS,
    SUBSCRIPTION_PLAN_INTERVAL,
    SUBSCRIPTION_PLAN_NAME,
    SUBSCRIPTION_PLAN_PERIOD,
    SUBSCRIPTION_TOTAL_COUNT,
)
from src.core.database import get_database
from src.services.credit_service import CreditService
from src.services.user_service import UserService


class BillingService:
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.credit_service = CreditService()
        self.user_service = UserService()
        self.db = None
        self.billing_plans = None
        self.billing_subscriptions = None
        self.webhook_events = None

    def _ensure_collections(self):
        if self.db is None:
            self.db = get_database()
            self.billing_plans = self.db.billing_plans
            self.billing_subscriptions = self.db.billing_subscriptions
            self.webhook_events = self.db.billing_webhook_events

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def get_plan_template(self) -> dict[str, Any]:
        return {
            "code": "monthly",
            "name": SUBSCRIPTION_PLAN_NAME,
            "amount": SUBSCRIPTION_PLAN_AMOUNT,
            "currency": SUBSCRIPTION_CURRENCY,
            "period": SUBSCRIPTION_PLAN_PERIOD,
            "interval": SUBSCRIPTION_PLAN_INTERVAL,
            "total_count": SUBSCRIPTION_TOTAL_COUNT,
            "credits_per_cycle": SUBSCRIPTION_PLAN_CREDITS,
            "razorpay_plan_id": RAZORPAY_SUBSCRIPTION_PLAN_ID,
        }

    def list_plans(self) -> list[dict[str, Any]]:
        try:
            self._ensure_collections()
            plan = self.billing_plans.find_one({"code": "monthly"})
            if not plan:
                plan = self.get_plan_template()
                self.billing_plans.insert_one({**plan, "created_at": self._now(), "updated_at": self._now()})
            else:
                plan["id"] = str(plan.pop("_id"))
            return [plan]
        except Exception:
            return [self.get_plan_template()]

    def get_plan(self, plan_code: str) -> dict[str, Any]:
        if plan_code != "monthly":
            raise ValueError("Unknown plan code")

        try:
            self._ensure_collections()
            plan = self.billing_plans.find_one({"code": plan_code})
            if not plan:
                plan = self.get_plan_template()
                self.billing_plans.insert_one({**plan, "created_at": self._now(), "updated_at": self._now()})
                return plan

            plan["id"] = str(plan.pop("_id"))
            return plan
        except Exception:
            return self.get_plan_template()

    def _require_secret(self) -> None:
        if not RAZORPAY_KEY_SECRET:
            raise RuntimeError("RAZORPAY_KEY_SECRET is not configured")

    def _auth(self) -> HTTPBasicAuth:
        self._require_secret()
        if not RAZORPAY_TEST_KEY_ID:
            raise RuntimeError("RAZORPAY_TEST_KEY_ID is not configured")
        return HTTPBasicAuth(RAZORPAY_TEST_KEY_ID, RAZORPAY_KEY_SECRET)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            f"{self.BASE_URL}{path}",
            json=payload,
            auth=self._auth(),
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def sync_plan_to_razorpay(self, plan_code: str) -> dict[str, Any]:
        plan = self.get_plan(plan_code)
        if plan.get("razorpay_plan_id"):
            return plan

        payload = {
            "period": plan["period"],
            "interval": plan["interval"],
            "item": {
                "name": plan["name"],
                "amount": plan["amount"],
                "currency": plan["currency"],
                "description": f"{plan['credits_per_cycle']} research credits per cycle",
            },
            "notes": {
                "plan_code": plan["code"],
                "credits_per_cycle": str(plan["credits_per_cycle"]),
            },
        }
        result = self._post("/plans", payload)
        plan["razorpay_plan_id"] = result["id"]
        self.billing_plans.update_one(
            {"code": plan_code},
            {
                "$set": {
                    "razorpay_plan_id": result["id"],
                    "updated_at": self._now(),
                }
            },
            upsert=True,
        )
        return plan

    def create_subscription(
        self,
        *,
        user_id: str,
        plan_code: str,
        customer_email: str | None = None,
        customer_contact: str | None = None,
        start_at: int | None = None,
    ) -> dict[str, Any]:
        self._ensure_collections()
        plan = self.get_plan(plan_code)
        if not plan.get("razorpay_plan_id"):
            plan = self.sync_plan_to_razorpay(plan_code)

        subscription_record = {
            "user_id": user_id,
            "plan_code": plan_code,
            "razorpay_plan_id": plan["razorpay_plan_id"],
            "status": "initiated",
            "credits_per_cycle": plan["credits_per_cycle"],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        record_id = self.billing_subscriptions.insert_one(subscription_record).inserted_id

        payload = {
            "plan_id": plan["razorpay_plan_id"],
            "total_count": plan["total_count"],
            "customer_notify": True,
            "notes": {
                "billing_record_id": str(record_id),
                "user_id": user_id,
                "plan_code": plan_code,
                "credits_per_cycle": str(plan["credits_per_cycle"]),
            },
        }
        if start_at:
            payload["start_at"] = start_at
        if customer_email:
            payload["customer_email"] = customer_email
        if customer_contact:
            payload["customer_contact"] = customer_contact

        try:
            result = self._post("/subscriptions", payload)
            self.billing_subscriptions.update_one(
                {"_id": record_id},
                {
                    "$set": {
                        "razorpay_subscription_id": result["id"],
                        "status": result.get("status", "created"),
                        "updated_at": self._now(),
                    }
                },
            )
            self.user_service.update_billing_status(
                user_id,
                plan_status="pending",
                subscription_status=result.get("status", "created"),
                plan_code=plan_code,
                subscription_id=result["id"],
            )
            return {
                "billing_record_id": str(record_id),
                "user_id": user_id,
                "plan_code": plan_code,
                "razorpay_plan_id": plan["razorpay_plan_id"],
                "razorpay_subscription_id": result["id"],
                "status": result.get("status", "created"),
                "key_id": RAZORPAY_TEST_KEY_ID,
                "checkout": {
                    "key": RAZORPAY_TEST_KEY_ID,
                    "subscription_id": result["id"],
                    "name": plan["name"],
                    "description": plan["name"],
                    "theme": {"color": "#1f2937"},
                },
            }
        except Exception as exc:
            self.billing_subscriptions.update_one(
                {"_id": record_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(exc),
                        "updated_at": self._now(),
                    }
                },
            )
            self.user_service.update_billing_status(
                user_id,
                plan_status="failed",
                subscription_status="failed",
                plan_code=plan_code,
            )
            raise

    def _verify_webhook_signature(self, body: bytes, signature: str | None) -> bool:
        if not RAZORPAY_WEBHOOK_SECRET:
            raise RuntimeError("RAZORPAY_WEBHOOK_SECRET is not configured")
        if not signature:
            return False
        digest = hmac.new(
            RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(digest, signature)

    def _dedupe_webhook(self, event_id: str | None, body: bytes) -> bool:
        self._ensure_collections()
        dedupe_key = event_id or hashlib.sha256(body).hexdigest()
        existing = self.webhook_events.find_one({"event_id": dedupe_key})
        if existing:
            return False
        self.webhook_events.insert_one(
            {"event_id": dedupe_key, "created_at": self._now()}
        )
        return True

    def _update_subscription_record(self, subscription_id: str, updates: dict[str, Any]) -> None:
        self._ensure_collections()
        self.billing_subscriptions.update_one(
            {"razorpay_subscription_id": subscription_id},
            {"$set": {**updates, "updated_at": self._now()}},
            upsert=True,
        )

    def _apply_subscription_charge(self, payload: dict[str, Any]) -> None:
        subscription = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        notes = subscription.get("notes") or {}
        user_id = notes.get("user_id")
        plan_code = notes.get("plan_code", "monthly")
        credits_per_cycle = int(notes.get("credits_per_cycle", SUBSCRIPTION_PLAN_CREDITS))
        subscription_id = subscription.get("id")

        if not user_id or not subscription_id:
            return

        credits_remaining, transaction_id = self.credit_service.grant_credits(
            user_id,
            credits_per_cycle,
            reason="subscription_charge",
            metadata={
                "plan_code": plan_code,
                "razorpay_subscription_id": subscription_id,
                "event": payload.get("event"),
            },
            session_id=subscription_id,
        )
        self._update_subscription_record(
            subscription_id,
            {
                "user_id": user_id,
                "plan_code": plan_code,
                "credits_per_cycle": credits_per_cycle,
                "status": subscription.get("status", "active"),
                "last_credited_at": int(self._now().timestamp()),
                "last_credit_transaction_id": transaction_id,
                "credits_remaining_after_charge": credits_remaining,
            },
        )
        self.user_service.update_billing_status(
            user_id,
            plan_status="active",
            subscription_status=subscription.get("status", "active"),
            plan_code=plan_code,
            subscription_id=subscription_id,
        )

    def handle_webhook(self, body: bytes, signature: str | None) -> tuple[int, dict[str, Any]]:
        if not self._verify_webhook_signature(body, signature):
            return 401, {"ok": False, "message": "Invalid webhook signature"}

        payload = json.loads(body.decode("utf-8"))
        event = payload.get("event")
        event_id = payload.get("event_id") or payload.get("entity", {}).get("id")

        if not self._dedupe_webhook(event_id, body):
            return 200, {"ok": True, "message": "Duplicate webhook ignored"}

        subscription = payload.get("payload", {}).get("subscription", {}).get("entity", {})
        subscription_id = subscription.get("id")

        if event == "subscription.charged":
            self._apply_subscription_charge(payload)
        elif event in {"subscription.activated", "subscription.authenticated", "subscription.pending", "subscription.halted", "subscription.cancelled", "subscription.completed"}:
            self._update_subscription_record(
                subscription_id,
                {
                    "user_id": subscription.get("notes", {}).get("user_id"),
                    "plan_code": subscription.get("notes", {}).get("plan_code", "monthly"),
                    "credits_per_cycle": int(subscription.get("notes", {}).get("credits_per_cycle", SUBSCRIPTION_PLAN_CREDITS)),
                    "status": subscription.get("status", event.split(".")[-1]),
                    "razorpay_plan_id": subscription.get("plan_id"),
                    "razorpay_subscription_id": subscription_id,
                    "customer_id": subscription.get("customer_id"),
                    "current_start": subscription.get("current_start"),
                    "current_end": subscription.get("current_end"),
                    "ended_at": subscription.get("ended_at"),
                    "paid_count": subscription.get("paid_count"),
                    "charge_at": subscription.get("charge_at"),
                },
            )
            if user_id := subscription.get("notes", {}).get("user_id"):
                self.user_service.update_billing_status(
                    user_id,
                    plan_status=subscription.get("status", event.split(".")[-1]),
                    subscription_status=subscription.get("status", event.split(".")[-1]),
                    plan_code=subscription.get("notes", {}).get("plan_code", "monthly"),
                    subscription_id=subscription_id,
                )
        else:
            self._update_subscription_record(
                subscription_id,
                {
                    "status": subscription.get("status", "unknown"),
                    "event": event,
                },
            )
            if user_id := subscription.get("notes", {}).get("user_id"):
                self.user_service.update_billing_status(
                    user_id,
                    subscription_status=subscription.get("status", "unknown"),
                    subscription_id=subscription_id,
                )

        return 200, {"ok": True, "message": "Webhook processed"}

    def list_subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        self._ensure_collections()
        rows = list(self.billing_subscriptions.find({"user_id": user_id}).sort("created_at", -1))
        for row in rows:
            row["id"] = str(row.pop("_id"))
        return rows

    def get_public_config(self) -> dict[str, Any]:
        return {
            "key_id": RAZORPAY_TEST_KEY_ID,
            "plans": self.list_plans(),
        }
