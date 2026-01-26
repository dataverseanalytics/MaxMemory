from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.plan import Plan
from app.models.credit import CreditTransaction
from app.schemas.plan import PlanResponse
from app.core.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter()

class UpgradeRequest(BaseModel):
    plan_id: int
    payment_method_id: str # Mock

@router.get("/plans", response_model=List[PlanResponse])
async def list_available_plans(
    db: Session = Depends(get_db)
):
    """List all active plans (Public)"""
    return db.query(Plan).filter(Plan.is_active == True).all()

@router.get("/current", response_model=Optional[PlanResponse])
async def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's plan"""
    if not current_user.plan_id:
        return None
        
    return db.query(Plan).filter(Plan.id == current_user.plan_id).first()

from app.services.payment_service import payment_service
from app.config import settings

class CreateOrderRequest(BaseModel):
    plan_id: int

class VerifyPaymentRequest(BaseModel):
    plan_id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

@router.post("/create-order")
async def create_payment_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a Razorpay order for plan upgrade"""
    # Get Plan
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="Plan is not active")
        
    if plan.price <= 0:
         raise HTTPException(status_code=400, detail="Use standard upgrade for free plans")
    
    # Amount in paise
    amount_paise = int(plan.price * 100)
    
    try:
        order = payment_service.create_order(amount=amount_paise, currency="INR")
        return {
            "order_id": order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key_id": settings.RAZORPAY_KEY_ID,
            "plan_name": plan.name,
            "description": f"Upgrade to {plan.name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify Razorpay payment and upgrade plan"""
    try:
        # Verify Signature
        payment_service.verify_payment_signature(
            request.razorpay_order_id,
            request.razorpay_payment_id,
            request.razorpay_signature
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    
    # If successful, upgrade plan
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    # Update User
    current_user.plan_id = plan.id
    
    # Add credits (Assumed logic: add on top)
    current_user.credits_balance += plan.credits
    
    # Record Transaction
    tx = CreditTransaction(
        user_id=current_user.id,
        amount=plan.credits,
        transaction_type="SUBSCRIPTION_PURCHASE",
        description=f"Purchased plan: {plan.name} (Ref: {request.razorpay_payment_id})"
    )
    db.add(tx)
    db.commit()
    
    return {"status": "success", "message": f"Upgraded to {plan.name}", "new_balance": current_user.credits_balance}

