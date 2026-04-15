from fastapi import APIRouter, Depends, HTTPException

from src.core.dependencies import get_current_user
from src.core.security import create_access_token
from src.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserPublic,
)
from src.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])
user_service = UserService()


def _to_public_user(user: dict) -> UserPublic:
    return UserPublic(**user)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    try:
        user = user_service.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
        token = create_access_token(
            {
                "sub": user["user_id"],
                "email": user.get("email"),
                "token_version": user.get("token_version", 0),
            }
        )
        return AuthResponse(access_token=token, user=_to_public_user(user))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    try:
        user = user_service.authenticate(email=payload.email, password=payload.password)
        token = create_access_token(
            {
                "sub": user["user_id"],
                "email": user.get("email"),
                "token_version": user.get("token_version", 0),
            }
        )
        return AuthResponse(access_token=token, user=_to_public_user(user))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/me", response_model=UserPublic)
def me(current_user=Depends(get_current_user)) -> UserPublic:
    return _to_public_user(current_user)


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
) -> UserPublic:
    try:
        user = user_service.update_profile(current_user["user_id"], name=payload.name)
        return _to_public_user(user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/change-password", response_model=TokenResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
) -> TokenResponse:
    try:
        user_service.change_password(
            current_user["user_id"],
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        fresh_user = user_service.get_user_by_id(current_user["user_id"])
        new_token = create_access_token(
            {
                "sub": current_user["user_id"],
                "email": current_user.get("email"),
                "token_version": fresh_user.get("token_version", 0) if fresh_user else 0,
            }
        )
        return TokenResponse(access_token=new_token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
