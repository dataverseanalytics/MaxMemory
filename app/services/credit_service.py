from sqlalchemy.orm import Session
from app.models.user import User
from app.models.credit import CreditTransaction
import logging

logger = logging.getLogger(__name__)

class CreditService:
    def __init__(self):
        # Pricing config (Credits per 1000 tokens)
        self.PROMPT_COST_PER_1K = 1.0  
        self.COMPLETION_COST_PER_1K = 2.0
        
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate credit cost based on usage"""
        prompt_cost = (prompt_tokens / 1000) * self.PROMPT_COST_PER_1K
        completion_cost = (completion_tokens / 1000) * self.COMPLETION_COST_PER_1K
        return round(prompt_cost + completion_cost, 4)

    def check_balance(self, user_id: int, db: Session) -> bool:
        """Check if user has positive balance"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        # Allow checking if balance > 0, or maybe a minimum threshold
        return user.credits_balance > 0

    def deduct_credits(self, user_id: int, usage: dict, db: Session) -> dict:
        """
        Deduct credits for usage.
        usage dict must have 'prompt_tokens' and 'completion_tokens'
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        cost = self.calculate_cost(prompt_tokens, completion_tokens)
        
        if cost == 0:
            return {"success": True, "cost": 0, "balance_remaining": 0}
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        # Deduct (we allow negative balance or stop before? User asked to check credit.
        # Assuming we check balance BEFORE generation, but exact cost is known AFTER.
        # So we might go slightly negative, which is fine.)
        
        user.credits_balance -= cost
        
        # Record transaction
        tx = CreditTransaction(
            user_id=user_id,
            amount=-cost,
            transaction_type="USAGE",
            description=f"Chat usage: {prompt_tokens} prompt, {completion_tokens} completion",
            metadata_json=usage
        )
        
        db.add(tx)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Deducted {cost} credits from user {user_id}. New balance: {user.credits_balance}")
        
        return {
            "success": True,
            "cost": cost,
            "balance_remaining": user.credits_balance
        }

    def add_credits(self, user_id: int, amount: float, description: str, db: Session):
        """Add credits to user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
            
        user.credits_balance += amount
        
        tx = CreditTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type="PURCHASE", # Or GRANT
            description=description
        )
        
        db.add(tx)
        db.commit()
        return user.credits_balance

    def get_usage_analytics(self, user_id: int, db: Session):
        """Aggregate usage stats for dashboard"""
        from sqlalchemy import func, extract
        from datetime import datetime, timedelta
        
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Total Credits Used This Month
        # filter for negative amounts (usage) in current month
        used_month = db.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.amount < 0,
            CreditTransaction.created_at >= start_of_month
        ).scalar() or 0.0
        
        # 2. Query Count This Month
        # Count 'USAGE' transactions
        query_count = db.query(func.count(CreditTransaction.id)).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.transaction_type == "USAGE",
            CreditTransaction.created_at >= start_of_month
        ).scalar() or 0
        
        # 3. Daily Credits (Last 7 days for chart)
        # Using simple date truncation. 
        # Note: SQLite date functions are different from Postgres. Assuming standard SA or Postgres/SQLite agnostic if possible.
        # For simplicity in SA generic:
        seven_days_ago = now - timedelta(days=7)
        
        # Group by date
        daily_credits = db.query(
            func.date(CreditTransaction.created_at).label("date"),
            func.sum(CreditTransaction.amount).label("total")
        ).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.amount < 0,
            CreditTransaction.created_at >= seven_days_ago
        ).group_by("date").all()
        
        # 4. Daily Queries
        daily_queries = db.query(
            func.date(CreditTransaction.created_at).label("date"),
            func.count(CreditTransaction.id).label("count")
        ).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.transaction_type == "USAGE",
            CreditTransaction.created_at >= seven_days_ago
        ).group_by("date").all()

        return {
            "used_month": abs(used_month),
            "query_count": query_count,
            "daily_credits": [{"date": str(r[0]), "value": abs(r[1] or 0)} for r in daily_credits],
            "daily_queries": [{"date": str(r[0]), "value": r[1]} for r in daily_queries]
        }

credit_service = CreditService()
