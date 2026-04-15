from fastapi import APIRouter, Depends, HTTPException

from src.core.dependencies import get_current_user
from src.schemas.account import (
    AccountHistoryResponse,
    AccountOverview,
    FileHistoryResponse,
    DeleteAccountResponse,
    SubscriptionHistoryResponse,
    TransactionHistoryResponse,
)
from src.schemas.auth import UserPublic
from src.services.billing_service import BillingService
from src.services.credit_service import CreditService
from src.services.file_asset_service import FileAssetService
from src.services.research_session_service import ResearchSessionService
from src.services.user_service import UserService

router = APIRouter(prefix="/account", tags=["account"])

user_service = UserService()
credit_service = CreditService()
session_service = ResearchSessionService()
billing_service = BillingService()
file_asset_service = FileAssetService()


def _public_user(user: dict) -> UserPublic:
    return UserPublic(**user)


@router.get("/me", response_model=UserPublic)
def get_me(current_user=Depends(get_current_user)) -> UserPublic:
    return _public_user(current_user)


@router.get("/overview", response_model=AccountOverview)
def overview(current_user=Depends(get_current_user)) -> AccountOverview:
    user_id = current_user["user_id"]
    return AccountOverview(
        user=_public_user(current_user),
        credits=credit_service.get_balance(user_id),
        research_sessions=len(session_service.list_sessions_by_user(user_id, limit=1000)),
        transactions=len(credit_service.list_transactions_by_user(user_id, limit=1000)),
        subscriptions=len(billing_service.list_subscriptions(user_id)),
        files=len(file_asset_service.list_assets_by_user(user_id, limit=1000)),
    )


@router.get("/research", response_model=AccountHistoryResponse)
def research_history(current_user=Depends(get_current_user)) -> AccountHistoryResponse:
    user_id = current_user["user_id"]
    return AccountHistoryResponse(
        user_id=user_id,
        sessions=session_service.list_sessions_by_user(user_id, limit=100),
    )


@router.get("/transactions", response_model=TransactionHistoryResponse)
def transaction_history(current_user=Depends(get_current_user)) -> TransactionHistoryResponse:
    user_id = current_user["user_id"]
    return TransactionHistoryResponse(
        user_id=user_id,
        transactions=credit_service.list_transactions_by_user(user_id, limit=100),
    )


@router.get("/subscriptions", response_model=SubscriptionHistoryResponse)
def subscription_history(current_user=Depends(get_current_user)) -> SubscriptionHistoryResponse:
    user_id = current_user["user_id"]
    return SubscriptionHistoryResponse(
        user_id=user_id,
        subscriptions=billing_service.list_subscriptions(user_id),
    )


@router.get("/files", response_model=FileHistoryResponse)
def file_history(current_user=Depends(get_current_user)) -> FileHistoryResponse:
    user_id = current_user["user_id"]
    return FileHistoryResponse(
        user_id=user_id,
        files=file_asset_service.list_assets_by_user(user_id, limit=100),
    )


@router.post("/disable", response_model=DeleteAccountResponse)
def disable_account(current_user=Depends(get_current_user)) -> DeleteAccountResponse:
    try:
        user_service.disable_user(current_user["user_id"])
        return DeleteAccountResponse(ok=True, message="Account disabled")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
