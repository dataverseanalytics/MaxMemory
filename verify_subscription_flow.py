import sys
import os
import requests
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.user import User
from app.core.security import create_access_token
from app.models.plan import Plan

client = TestClient(app)

def setup():
    # Run migration if needed (can call the function directly or assume run)
    pass

def log(msg):
    with open("verification_result_sub.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def verify_flow():
    if os.path.exists("verification_result_sub.txt"):
        os.remove("verification_result_sub.txt")
        
    db = next(get_db())
    try:
        # 1. Setup Admin
        admin_email = "admin@example.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(email=admin_email, full_name="Admin", is_active=True, is_superuser=True)
            db.add(admin)
            db.commit()
            db.refresh(admin)
        else:
            admin.is_superuser = True
            db.commit()
            
        # 2. Setup User
        user_email = "user@example.com"
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, full_name="Test User", credits_balance=0.0)
            db.add(user)
            db.commit()
        
        # Tokens
        admin_token = create_access_token({"sub": admin.email, "user_id": admin.id})
        user_token = create_access_token({"sub": user.email, "user_id": user.id})
        
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        log("\n[1] Create Plans (Admin)")
        plans_data = [
            {"name": "Free", "price": 0.0, "credits": 1000.0, "features": ["Basic Support"]},
            {"name": "Pro", "price": 29.0, "credits": 10000.0, "features": ["Priority Support", "Unlimited Docs"]},
            {"name": "Enterprise", "price": 99.0, "credits": 100000.0, "features": ["24/7 Support"]}
        ]
        
        for p_data in plans_data:
            # Check if exists to avoid dupe error in test loop
            exists = db.query(Plan).filter(Plan.name == p_data["name"]).first()
            if not exists:
                resp = client.post("/api/v1/admin/plans", json=p_data, headers=admin_headers)
                if resp.status_code == 200:
                    log(f"✅ Created plan: {p_data['name']}")
                else:
                    log(f"❌ Failed to create plan {p_data['name']}: {resp.text}")
            else:
                 log(f"ℹ️  Plan {p_data['name']} already exists")
                 
        # 3. List Plans (User)
        log("\n[2] List Plans (User)")
        resp = client.get("/api/v1/subscriptions/plans", headers=user_headers)
        if resp.status_code == 200:
            plans = resp.json()
            log(f"✅ User listed {len(plans)} plans")
            assert len(plans) >= 3
        else:
            log(f"❌ User failed to list plans: {resp.text}")
            return
    
        # 4. Upgrade Plan (User)
        log("\n[3] Upgrade to Pro (User)")
        pro_plan = next(p for p in plans if p['name'] == "Pro")
        initial_balance = user.credits_balance
        
        resp = client.post("/api/v1/subscriptions/upgrade", 
                           json={"plan_id": pro_plan['id'], "payment_method_id": "tok_visa"}, 
                           headers=user_headers)
        
        if resp.status_code == 200:
            data = resp.json()
            log(f"✅ Upgraded to Pro. New Balance: {data['new_balance']}")
            # Verify DB
            db.refresh(user)
            assert user.plan_id == pro_plan['id']
            assert user.credits_balance >= initial_balance + pro_plan['credits']
        else:
            log(f"❌ Upgrade failed: {resp.text}")
            
        # 5. Assign Plan (Admin)
        log("\n[4] Assign Enterprise (Admin)")
        ent_plan = next(p for p in plans if p['name'] == "Enterprise")
        current_balance = user.credits_balance
        
        resp = client.post(f"/api/v1/admin/users/{user.id}/assign-plan", 
                           json={"plan_id": ent_plan['id']},
                           headers=admin_headers)
                           
        if resp.status_code == 200:
            data = resp.json()
            log(f"✅ Assigned Enterprise. New Balance: {data['new_balance']}")
            db.refresh(user)
            assert user.plan_id == ent_plan['id']
            assert user.credits_balance == current_balance + ent_plan['credits']
        else:
            log(f"❌ Assignment failed: {resp.text}")
    
        log("\n🎉 Verification Complete")
        
    except Exception as e:
        import traceback
        log(f"Exception: {e}")
        log(traceback.format_exc())


if __name__ == "__main__":
    verify_flow()
