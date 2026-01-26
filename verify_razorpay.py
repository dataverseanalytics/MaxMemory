import sys
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.plan import Plan
from app.core.security import create_access_token
from app.services.payment_service import payment_service
from unittest.mock import MagicMock

client = TestClient(app)

def log(msg):
    with open("verification_result_razorpay.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def verify_razorpay_flow():
    if os.path.exists("verification_result_razorpay.txt"):
        os.remove("verification_result_razorpay.txt")
        
    db = next(get_db())
    try:
        # 1. Setup User
        user_email = "razorpay_test@example.com"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, full_name="Razorpay Test User")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        token = create_access_token({"sub": user.email, "user_id": user.id})
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Ensure Plans Exist
        pro_plan = db.query(Plan).filter(Plan.name == "Pro").first()
        if not pro_plan:
            pro_plan = Plan(name="Pro", price=29.0, credits=10000.0)
            db.add(pro_plan)
            db.commit()
            db.refresh(pro_plan)
            
        # 3. Test Create Order
        log("\n[1] Testing Create Order")
        
        # Mocking the actual Razorpay client call to avoid external dependency in this script
        # Alternatively, we could let it call if keys are valid, but it might fail without network or if keys are invalid.
        # Given we have keys, let's try real call? 
        # But for robustness, let's mock the service method in the app or use real call if safe.
        # The user provided keys, so likely wants real integration test.
        # However, verifying signature usually requires a real order ID + payment ID (from checkout).
        # We can simulate the verification part by generating a valid signature manually using the secret.
        
        # Call API
        resp = client.post("/api/v1/subscriptions/create-order", json={"plan_id": pro_plan.id}, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            log(f"✅ Order Created: {data.get('order_id')}")
            order_id = data.get('order_id')
            
            # 4. Test Verify Payment (Simulated)
            log("\n[2] Testing Verify Payment (Simulating Success)")
            
            # Generate valid signature
            # signature = hmac_sha256(order_id + "|" + payment_id, secret)
            import hmac
            import hashlib
            from app.config import settings
            
            payment_id = "pay_mock_123456"
            msg = f"{order_id}|{payment_id}".encode()
            signature = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), msg, hashlib.sha256).hexdigest()
            
            verify_payload = {
                "plan_id": pro_plan.id,
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
            
            initial_balance = user.credits_balance
            
            resp_verify = client.post("/api/v1/subscriptions/verify-payment", json=verify_payload, headers=headers)
            
            if resp_verify.status_code == 200:
                verify_data = resp_verify.json()
                log("✅ Payment Verified Successfully")
                log(f"New Balance: {verify_data['new_balance']}")
                
                # Check DB
                db.refresh(user)
                if user.credits_balance >= initial_balance + pro_plan.credits:
                     log("✅ Credits added correctly")
                else:
                     log("❌ Credits mismatch")
            else:
                log(f"❌ Payment Verification Failed: {resp_verify.text}")
                
        else:
             log(f"❌ Create Order Failed: {resp.text}")
             if "Use standard upgrade" in resp.text:
                 log("ℹ️  Skipping create order for free plan (expected)")

    except Exception as e:
        import traceback
        log(f"Exception: {e}")
        log(traceback.format_exc())

if __name__ == "__main__":
    verify_razorpay_flow()
