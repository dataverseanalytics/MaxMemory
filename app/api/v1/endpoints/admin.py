from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.plan import Plan
from app.models.credit import CreditTransaction
from app.schemas.plan import PlanCreate, PlanResponse, PlanAssign
from app.core.dependencies import get_current_user

router = APIRouter()

def check_admin(current_user: User):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

@router.post("/plans", response_model=PlanResponse)
async def create_plan(
    plan: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription plan (Admin only)"""
    check_admin(current_user)
    
    db_plan = Plan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all plans (Admin only - or maybe public? keeping admin restriction for now as per task)"""
    check_admin(current_user)
    return db.query(Plan).all()

@router.post("/users/{user_id}/assign-plan")
async def assign_plan(
    user_id: int,
    assignment: PlanAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a plan to a user and add credits (Admin only)"""
    check_admin(current_user)
    
    # Get User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get Plan
    plan = db.query(Plan).filter(Plan.id == assignment.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    # Update User Plan
    user.plan_id = plan.id
    
    # Add Credits
    if plan.credits > 0:
        user.credits_balance += plan.credits
        
        # Record Transaction
        tx = CreditTransaction(
            user_id=user.id,
            amount=plan.credits,
            transaction_type="PLAN_ASSIGNMENT",
            description=f"Assigned to plan: {plan.name}"
        )
        db.add(tx)
        
    db.commit()
    
    return {"message": f"Plan {plan.name} assigned to user", "new_balance": user.credits_balance}
