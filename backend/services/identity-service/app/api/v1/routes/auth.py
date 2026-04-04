from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_authorization_header, get_current_user
from app.db.session import get_db
from app.schemas.auth import AuthData, LoginRequest, LogoutRequest, RefreshRequest, RegisterRequest, SessionValidationData
from app.schemas.common import StandardResponse
from app.services.auth_service import AuthService
from app.utils.responses import success_response


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    user_id, access_token, refresh_token = service.register_user(
        name=payload.name,
        phone=payload.phone,
        email=payload.email,
        password=payload.password,
    )
    data = AuthData(user_id=user_id, access_token=access_token, refresh_token=refresh_token).model_dump()
    return success_response(data)


@router.post("/login", response_model=StandardResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    user_id, access_token, refresh_token = service.login_user(phone=payload.phone, password=payload.password)
    data = AuthData(user_id=user_id, access_token=access_token, refresh_token=refresh_token).model_dump()
    return success_response(data)


@router.post("/refresh", response_model=StandardResponse)
def refresh_session(payload: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    user_id, access_token, refresh_token = service.refresh_session(payload.refresh_token)
    data = AuthData(user_id=user_id, access_token=access_token, refresh_token=refresh_token).model_dump()
    return success_response(data)


@router.post("/logout", response_model=StandardResponse)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> dict:
    service = AuthService(db)
    service.logout(payload.refresh_token)
    data = {"status": "logged_out"}
    return success_response(data)


@router.get("/validate", response_model=StandardResponse)
def validate_session(
    _: str = Depends(get_authorization_header),
    current_user=Depends(get_current_user),
) -> dict:
    data = SessionValidationData(user_id=current_user.id, valid=True).model_dump()
    return success_response(data)
