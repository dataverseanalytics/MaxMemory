from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AccountDetails(BaseModel):
    """Schema for account details response"""
    member_since: datetime
    account_status: str  # "Active" or "Inactive"
    total_days: int  # Days since account creation
    is_verified: bool
    is_google_user: bool
    
    class Config:
        from_attributes = True
