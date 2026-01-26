import sys
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.models.user import User
from app.core.security import create_access_token

client = TestClient(app)

def verify_delete_account():
    db = next(get_db())
    
    # 1. Create a dummy user
    email = "delete_me@example.com"
    user = db.query(User).filter(User.email == email).first()
    if user:
        db.delete(user) # Clean start
        db.commit()
        
    user = User(email=email, full_name="To Be Deleted", is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    user_id = user.id
    token = create_access_token({"sub": user.email, "user_id": user.id})
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Created user {email} (ID: {user_id})")
    
    # 2. Call Delete Endpoint
    print("Calling DELETE /api/v1/profile/me")
    resp = client.delete("/api/v1/profile/me", headers=headers)
    
    if resp.status_code == 200:
        print("✅ Response 200 OK")
        print(resp.json())
        
        # 3. Verify User is gone
        deleted_user = db.query(User).filter(User.id == user_id).first()
        if not deleted_user:
            print("✅ User successfully removed from DB")
        else:
            print("❌ User still exists in DB!")
    else:
        print(f"❌ Delete failed: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    verify_delete_account()
