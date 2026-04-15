from typing import Any

from pydantic import BaseModel, Field

from src.schemas.auth import UserPublic


class AccountOverview(BaseModel):
    user: UserPublic
    credits: int
    research_sessions: int
    transactions: int
    subscriptions: int
    files: int


class AccountHistoryResponse(BaseModel):
    user_id: str
    sessions: list[dict[str, Any]]


class TransactionHistoryResponse(BaseModel):
    user_id: str
    transactions: list[dict[str, Any]]


class SubscriptionHistoryResponse(BaseModel):
    user_id: str
    subscriptions: list[dict[str, Any]]


class FileHistoryResponse(BaseModel):
    user_id: str
    files: list[dict[str, Any]]


class DeleteAccountResponse(BaseModel):
    ok: bool
    message: str
