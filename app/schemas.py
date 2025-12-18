from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class GoogleLoginRequest(BaseModel):
    """Request model for Google OAuth callback"""
    code: str
    state: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    picture_url: Optional[str]
    provider: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ResetPasswordResponse(BaseModel):
    message: str
