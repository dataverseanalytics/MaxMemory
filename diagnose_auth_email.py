"""
Authentication and Email Diagnostic Script
Run this to test if your authentication and email are working correctly.
"""

import sys
from app.database import get_db
from app.models.user import User
from app.models.plan import Plan  # Import Plan to ensure table exists
from app.core.security import create_access_token, decode_token, get_password_hash
from app.utils.email import send_verification_email
from app.config import settings

def test_authentication():
    print("\n" + "="*60)
    print("AUTHENTICATION DIAGNOSTICS")
    print("="*60)
    
    db = next(get_db())
    
    # 1. Check if test user exists
    test_email = "test@example.com"
    user = db.query(User).filter(User.email == test_email).first()
    
    if not user:
        print(f"\n[1] Creating test user: {test_email}")
        user = User(
            email=test_email,
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Test user created (ID: {user.id})")
    else:
        print(f"\n[1] Test user exists (ID: {user.id}, Active: {user.is_active})")
    
    # 2. Generate token
    print(f"\n[2] Generating access token...")
    token = create_access_token({"sub": user.email, "user_id": user.id})
    print(f"✅ Token generated successfully")
    print(f"Token (first 50 chars): {token[:50]}...")
    
    # 3. Decode token
    print(f"\n[3] Decoding token...")
    payload = decode_token(token)
    if payload:
        print(f"✅ Token decoded successfully")
        print(f"   - Email: {payload.get('sub')}")
        print(f"   - User ID: {payload.get('user_id')}")
        print(f"   - Type: {payload.get('type')}")
    else:
        print(f"❌ Token decode failed!")
        return False
    
    # 4. Test Swagger usage
    print(f"\n[4] Swagger Authentication Instructions:")
    print(f"   1. Go to http://localhost:8000/docs")
    print(f"   2. Click 'Authorize' button (top right)")
    print(f"   3. In the 'Value' field, enter: {token}")
    print(f"   4. Click 'Authorize' then 'Close'")
    print(f"   5. Try any protected endpoint")
    
    return True

def test_email():
    print("\n" + "="*60)
    print("EMAIL DIAGNOSTICS")
    print("="*60)
    
    # Check SMTP configuration
    print(f"\n[1] Checking SMTP Configuration...")
    print(f"   SMTP_HOST: {settings.SMTP_HOST}")
    print(f"   SMTP_PORT: {settings.SMTP_PORT}")
    print(f"   SMTP_USER: {settings.SMTP_USER if settings.SMTP_USER else '❌ NOT SET'}")
    print(f"   SMTP_PASSWORD: {'✅ SET' if settings.SMTP_PASSWORD else '❌ NOT SET'}")
    print(f"   EMAIL_FROM: {settings.EMAIL_FROM}")
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"\n⚠️  SMTP is NOT configured!")
        print(f"   Emails will NOT be sent.")
        print(f"\n   To fix:")
        print(f"   1. Update .env file with valid SMTP credentials")
        print(f"   2. Restart the server")
        return False
    
    # Test sending email
    print(f"\n[2] Testing email send...")
    try:
        result = send_verification_email(
            "test@example.com",
            "test_token_123",
            "Test User"
        )
        if result:
            print(f"✅ Email sent successfully!")
        else:
            print(f"❌ Email send failed (check logs)")
        return result
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("MAX MEMORY - DIAGNOSTICS")
    print("="*60)
    
    auth_ok = test_authentication()
    email_ok = test_email()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Authentication: {'✅ WORKING' if auth_ok else '❌ FAILED'}")
    print(f"Email Service:  {'✅ WORKING' if email_ok else '⚠️  NOT CONFIGURED'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
