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

    def get_usage_analytics(self, user_id: int, db: Session, period: str = "daily"):
        """Aggregate usage stats for dashboard with filtering"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Billing Info (Mocked based on user creation or fixed logic)
        # Assuming billing cycle starts on the day user was created. 
        # For now, we'll mock it to be the 15th of next month as per design or based on current date.
        
        user = db.query(User).filter(User.id == user_id).first()
        billing_day = user.created_at.day if user and user.created_at else 1
        # Handle edge cases for dates > 28
        billing_day = min(billing_day, 28) 
        
        next_billing_date = now.replace(day=billing_day)
        if next_billing_date < now:
            next_billing_date = next_billing_date + relativedelta(months=1)
            
        next_billing_amount = 29.0 # Standard plan mock
        
        # 2. Total Credits Used This Month & Query Count
        used_month = db.query(func.sum(CreditTransaction.amount)).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.amount < 0,
            CreditTransaction.created_at >= start_of_month
        ).scalar() or 0.0
        
        query_count = db.query(func.count(CreditTransaction.id)).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.transaction_type == "USAGE",
            CreditTransaction.created_at >= start_of_month
        ).scalar() or 0
        
        # Growth calculation (Mock vs last month for now, or implement real comparison)
        # To do real comparison:
        start_of_last_month = start_of_month - relativedelta(months=1)
        query_count_last_month = db.query(func.count(CreditTransaction.id)).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.transaction_type == "USAGE",
            CreditTransaction.created_at >= start_of_last_month,
            CreditTransaction.created_at < start_of_month
        ).scalar() or 0
        
        if query_count_last_month > 0:
            query_growth = ((query_count - query_count_last_month) / query_count_last_month) * 100
        else:
            query_growth = 100 if query_count > 0 else 0

        # 3. Chart Data based on Period
        if period == "weekly":
            # Last 12 weeks
            start_date = now - timedelta(weeks=12)
            # Group by week is tricky in pure SQL across DBs. 
            # We will fetch daily and aggregate in Python for flexibility.
            date_format = "%Y-%W" # Year-Week
            days_back = 84 # 12 weeks
        elif period == "monthly":
            # Last 12 months
            start_date = now - relativedelta(months=12)
            date_format = "%Y-%m" # Year-Month
            days_back = 365
        else:
            # Daily (Default) - Last 30 days
            start_date = now - timedelta(days=30)
            date_format = "%Y-%m-%d"
            days_back = 30
            
        # Fetch all relevant txs
        txs = db.query(CreditTransaction).filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.created_at >= start_date
        ).all()
        
        # Aggregate in Python
        credits_data = {}
        queries_data = {}
        
        # Initialize periods (to show 0s) - simplified
        # For a perfect chart we would pre-fill all dates/weeks/months
        
        for tx in txs:
            if period == "daily":
                key = tx.created_at.strftime("%a") # Mon, Tue... as per design? 
                # Design shows "Mon", "Tue" etc. But that's ambiguous for 30 days.
                # Design image shows about 7 points. "Queries Over Time".
                # If "Daily" filter means "Last 7 days" -> Mon, Tue...
                # If "Daily" means "Last 30 days" -> Date string.
                # Let's align with the image which shows ~7 days.
                # If the user selects "Daily", maybe we show Last 7 days?
                # But typically "Daily" view might show 30 days. 
                # Let's stick to the implementation plan: 
                # Daily = Last 30 days (Plan said 30).
                # But Image shows 7 days (Mon-Sun).
                # Let's adjust "Daily" to be Last 7 Days to match the specific "Mon...Sun" labels in the mockup?
                # No, the mockup labels might be just specific to that view.
                # Let's stick to a robust format: YYYY-MM-DD for keys, frontend handles display labels.
                key = tx.created_at.strftime("%Y-%m-%d")
            elif period == "weekly":
                key = tx.created_at.strftime("%Y-W%U")
            elif period == "monthly":
                key = tx.created_at.strftime("%Y-%m")
            
            if tx.amount < 0:
                credits_data[key] = credits_data.get(key, 0) + abs(tx.amount)
            
            if tx.transaction_type == "USAGE":
                queries_data[key] = queries_data.get(key, 0) + 1

        # Sort and Format
        credits_chart = [{"date": k, "value": v} for k, v in sorted(credits_data.items())]
        queries_chart = [{"date": k, "value": v} for k, v in sorted(queries_data.items())]
        
        return {
            "summary": {
                "credits_used_this_month": abs(used_month),
                "month_query_count": query_count,
                "query_growth_percent": round(query_growth, 1),
                "total_credit_limit": 10000.0
            },
            "credits_daily": credits_chart,
            "queries_daily": queries_chart,
            "usage_trend": queries_chart, # Reusing queries for trend for now
            "next_billing_date": next_billing_date.strftime("%B %d, %Y"),
            "next_billing_amount": next_billing_amount,
            "period": period
        }



credit_service = CreditService()
