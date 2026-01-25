from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class ProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None


class ChangePassword(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ProfileResponse(BaseModel):
    """Schema for profile response"""
    id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    is_verified: bool
    is_google_user: bool
    is_active: bool
    
    class Config:
        from_attributes = True
