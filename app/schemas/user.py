from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    is_verified: bool
    is_google_user: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class ForgotPassword(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class ResetPassword(BaseModel):
    """Schema for password reset"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth"""
    token: str  # Google ID token
