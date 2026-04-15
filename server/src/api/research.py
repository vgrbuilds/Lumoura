from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.dependencies import get_current_user
from src.core.config import RESEARCH_CREDIT_COST
from src.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    ResearchSessionSummary,
    UserCreditsResponse,
)
from src.services.credit_service import CreditService
from src.services.file_asset_service import FileAssetService
from src.services.research_export_service import ResearchExportService
from src.services.pipeline_service import ResearchPipeline
from src.services.research_session_service import ResearchSessionService

router = APIRouter(prefix="/research", tags=["research"])

pipeline = ResearchPipeline()
credit_service = CreditService()
session_service = ResearchSessionService()
export_service = ResearchExportService()
file_asset_service = FileAssetService()


def _run_research(query: str, user_id: str, preferences: dict | None = None) -> ResearchResponse:
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    preferences = preferences or {}
    session_id: str | None = None
    debit_transaction_id: str | None = None

    try:
        session_id = session_service.create_pending_session(
            user_id=user_id,
            query=query,
            preferences=preferences,
            credits_cost=RESEARCH_CREDIT_COST,
            debit_transaction_id=None,
        )

        credits_remaining, debit_transaction_id = credit_service.reserve_credits(
            user_id,
            RESEARCH_CREDIT_COST,
            reason="research_run",
            metadata={"query": query},
            session_id=session_id,
        )

        credit_service.attach_session_to_transaction(debit_transaction_id, session_id)
        session_service.attach_debit_transaction(session_id, debit_transaction_id)

        result = pipeline.run(query, preferences)

        export_asset = export_service.export(
            user_id=user_id,
            session_id=session_id,
            query=query,
            answer=result["answer"],
            sources=result["sources"],
            preferences=result["preferences"],
        )

        session_service.complete_session(
            session_id,
            answer=result["answer"],
            sources=result["sources"],
            search_results=result["search_results"],
            preferences=result["preferences"],
            export=export_asset,
        )

        return ResearchResponse(
            session_id=session_id,
            transaction_id=debit_transaction_id,
            export=export_asset,
            user_id=user_id,
            query=result["query"],
            answer=result["answer"],
            sources_used=result["sources_used"],
            credits_remaining=credits_remaining,
            preferences=result["preferences"],
            sources=result["sources"],
            search_results=result["search_results"],
        )
    except ValueError as exc:
        if session_id:
            session_service.fail_session(session_id, str(exc))
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except RuntimeError as exc:
        if session_id and debit_transaction_id:
            try:
                credits_remaining, refund_transaction_id = credit_service.refund_credits(
                    user_id,
                    RESEARCH_CREDIT_COST,
                    reason="research_failed_refund",
                    metadata={"query": query, "error": str(exc)},
                    session_id=session_id,
                )
                session_service.attach_refund_transaction(session_id, refund_transaction_id)
                session_service.fail_session(session_id, str(exc))
                # keep the session failure state; credits were refunded
            except Exception:
                session_service.fail_session(session_id, str(exc))
        elif session_id:
            session_service.fail_session(session_id, str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("", response_model=ResearchResponse)
def get_research(
    payload: ResearchRequest,
    current_user=Depends(get_current_user),
) -> ResearchResponse:
    user_id = current_user["user_id"]
    if payload.user_id and payload.user_id != user_id:
        raise HTTPException(status_code=403, detail="User mismatch")
    return _run_research(payload.query, user_id, payload.preferences.model_dump())


@router.get("", response_model=ResearchResponse)
def get_research_by_query(
    current_user=Depends(get_current_user),
    query: str = Query(..., min_length=2),
) -> ResearchResponse:
    return _run_research(query, current_user["user_id"])


@router.get("/credits/me", response_model=UserCreditsResponse)
def get_credits(current_user=Depends(get_current_user)) -> UserCreditsResponse:
    try:
        credits = credit_service.get_balance(current_user["user_id"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return UserCreditsResponse(user_id=current_user["user_id"], credits=credits)


@router.get("/sessions/{session_id}", response_model=ResearchSessionSummary)
def get_session(session_id: str, current_user=Depends(get_current_user)) -> ResearchSessionSummary:
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="User mismatch")

    return ResearchSessionSummary(
        id=session["id"],
        user_id=session["user_id"],
        query=session["query"],
        answer=session.get("answer") or "",
        credits_cost=int(session.get("credits_cost", 0)),
        status=session.get("status", "unknown"),
        preferences=session.get("preferences", {}),
        export=session.get("export"),
    )


@router.get("/sessions")
def list_sessions(
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
):
    user_id = current_user["user_id"]
    sessions = session_service.list_sessions_by_user(user_id, limit=limit)
    return {"user_id": user_id, "sessions": sessions}


@router.get("/sessions/{session_id}/export")
def get_session_export(session_id: str, current_user=Depends(get_current_user)):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="User mismatch")

    asset = file_asset_service.get_asset_by_session(session_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Export file not found")

    return asset
