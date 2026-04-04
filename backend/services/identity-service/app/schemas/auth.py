from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=8, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class AuthData(BaseModel):
    user_id: UUID
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class SessionValidationData(BaseModel):
    user_id: UUID
    valid: bool
