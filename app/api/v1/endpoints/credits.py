from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.credit import CreditTransaction
from app.core.dependencies import get_current_user
from app.services.credit_service import credit_service

router = APIRouter()

class TransactionResponse(BaseModel):
    id: int
    amount: float
    transaction_type: str
    description: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class BalanceResponse(BaseModel):
    current_balance: float
    recent_transactions: List[TransactionResponse]

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current credit balance and recent transactions"""
    recent_txs = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).order_by(CreditTransaction.created_at.desc()).limit(10).all()
    
    return {
        "current_balance": current_user.credits_balance,
        "recent_transactions": recent_txs
    }

class TopUpRequest(BaseModel):
    amount: float
    description: str = "Manual Top-up"

@router.post("/topup", response_model=Dict[str, float])
async def top_up_credits(
    request: TopUpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add credits manually (Mock implementation for demo)"""
    new_balance = credit_service.add_credits(
        user_id=current_user.id,
        amount=request.amount,
        description=request.description,
        db=db
    )
    
    return {"new_balance": new_balance}

from app.schemas.analytics import AnalyticsResponse, UsageSummary, ChartPoint

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    period: str = "daily",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage analytics for dashboard
    period: 'daily', 'weekly', 'monthly'
    """
    return credit_service.get_usage_analytics(current_user.id, db, period)

