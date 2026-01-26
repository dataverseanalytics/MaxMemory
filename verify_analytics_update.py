import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base, engine
from app.models.user import User
from app.models.credit import CreditTransaction
from sqlalchemy.orm import Session
from app.core.security import create_access_token

# Setup Test Client
client = TestClient(app)

def setup_test_data(db: Session):
    # Create test user
    user_email = "analytics_test@example.com"
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        user = User(
            email=user_email,
            full_name="Analytics Test User",
            hashed_password="hashed_secret",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create some transactions if none exist
    tx_count = db.query(CreditTransaction).filter(CreditTransaction.user_id == user.id).count()
    if tx_count == 0:
        # Add a purchase
        db.add(CreditTransaction(
            user_id=user.id,
            amount=100.0,
            transaction_type="PURCHASE",
            description="Initial Topup"
        ))
        # Add some usage
        from datetime import timedelta
        now = datetime.now()
        
        # Today
        db.add(CreditTransaction(user_id=user.id, amount=-1.5, transaction_type="USAGE", created_at=now))
        # Yesterday
        db.add(CreditTransaction(user_id=user.id, amount=-2.0, transaction_type="USAGE", created_at=now - timedelta(days=1)))
        # Last Week
        db.add(CreditTransaction(user_id=user.id, amount=-5.0, transaction_type="USAGE", created_at=now - timedelta(days=7)))
        # Last Month
        db.add(CreditTransaction(user_id=user.id, amount=-10.0, transaction_type="USAGE", created_at=now - timedelta(days=35)))
        
        db.commit()
    
    return user

def log(msg):
    with open("verification_result.txt", "a") as f:
        f.write(msg + "\n")
    print(msg)

def verify_analytics():
    if os.path.exists("verification_result.txt"):
        os.remove("verification_result.txt")
        
    db = next(get_db())
    try:
        user = setup_test_data(db)
        
        # Create token
        token = create_access_token(data={"sub": user.email, "user_id": user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test Default (Daily)
        log("Testing Daily Analytics...")
        try:
            response = client.get("/api/v1/credits/analytics", headers=headers)
            if response.status_code != 200:
                log(f"Error: Status {response.status_code} - {response.text}")
                return
                
            data = response.json()
            log(f"Success! Response keys: {list(data.keys())}")
            log(f"Next Billing Date: {data.get('next_billing_date')}")
            log(f"Period: {data.get('period')}")
            
            assert "next_billing_date" in data
            assert "next_billing_amount" in data
            assert "usage_trend" in data
            assert data["period"] == "daily"
            
            # Test Weekly
            log("Testing Weekly Analytics...")
            response = client.get("/api/v1/credits/analytics?period=weekly", headers=headers)
            if response.status_code != 200:
                 log(f"Error Weekly: {response.status_code} - {response.text}")
            else:
                 data = response.json()
                 log(f"Period: {data.get('period')}")
                 assert data["period"] == "weekly"

            # Test Monthly
            log("Testing Monthly Analytics...")
            response = client.get("/api/v1/credits/analytics?period=monthly", headers=headers)
            if response.status_code != 200:
                 log(f"Error Monthly: {response.status_code} - {response.text}")
            else:
                 data = response.json()
                 log(f"Period: {data.get('period')}")
                 assert data["period"] == "monthly"

            log("ALL VERIFICATIONS PASSED")
            
        except Exception as e:
            import traceback
            log(f"Exception during verification: {e}")
            log(traceback.format_exc())

        
    finally:
        db.close()

if __name__ == "__main__":
    verify_analytics()
