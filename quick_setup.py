"""
Quick Fix Script for Authentication & Email Issues
This script will set up everything you need to test the API.
"""

from app.database import get_db, engine, Base
from app.models.user import User
from app.models.plan import Plan
from app.core.security import create_access_token, get_password_hash
from app.config import settings

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

def setup_test_user():
    """Create a test user with a known password"""
    db = next(get_db())
    
    # Test user credentials
    email = "test@example.com"
    password = "password123"
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        print(f"✅ Test user already exists: {email}")
        print(f"   User ID: {user.id}")
        print(f"   Active: {user.is_active}")
    else:
        # Create new user
        user = User(
            email=email,
            full_name="Test User",
            hashed_password=get_password_hash(password),
            is_active=True,
            is_verified=True,
            credits_balance=1000.0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Created test user: {email}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
    
    # Generate token
    token = create_access_token({"sub": user.email, "user_id": user.id})
    
    print(f"\n{'='*60}")
    print(f"SWAGGER AUTHENTICATION INSTRUCTIONS")
    print(f"{'='*60}")
    print(f"\n1. Go to: http://localhost:8000/docs")
    print(f"\n2. Click the 'Authorize' button (🔒 icon, top right)")
    print(f"\n3. Paste this token in the 'Value' field:")
    print(f"\n   {token}")
    print(f"\n4. Click 'Authorize' then 'Close'")
    print(f"\n5. Now you can test any protected endpoint!")
    print(f"\n{'='*60}")
    print(f"\nALTERNATIVE: Login via API")
    print(f"{'='*60}")
    print(f"\nUse POST /api/v1/auth/login with:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"{'='*60}\n")
    
    return user, token

def check_email_config():
    """Check email configuration"""
    print(f"\n{'='*60}")
    print(f"EMAIL CONFIGURATION STATUS")
    print(f"{'='*60}")
    
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        print(f"✅ SMTP is configured")
        print(f"   Host: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"   User: {settings.SMTP_USER}")
        print(f"   From: {settings.EMAIL_FROM}")
    else:
        print(f"⚠️  SMTP is NOT configured")
        print(f"   Emails will NOT be sent (this is OK for development)")
        print(f"   Users can still register and login normally")
    print(f"{'='*60}\n")

def create_sample_plans():
    """Create sample subscription plans"""
    db = next(get_db())
    
    plans_data = [
        {"name": "Free", "price": 0.0, "credits": 1000.0, "features": ["Basic Support"], "is_active": True},
        {"name": "Pro", "price": 29.0, "credits": 10000.0, "features": ["Priority Support", "Unlimited Docs"], "is_active": True},
        {"name": "Enterprise", "price": 99.0, "credits": 100000.0, "features": ["24/7 Support", "Custom Integration"], "is_active": True}
    ]
    
    print(f"{'='*60}")
    print(f"SUBSCRIPTION PLANS")
    print(f"{'='*60}\n")
    
    for plan_data in plans_data:
        existing = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
        if not existing:
            plan = Plan(**plan_data)
            db.add(plan)
            db.commit()
            print(f"✅ Created plan: {plan_data['name']} (${plan_data['price']}/mo)")
        else:
            print(f"ℹ️  Plan already exists: {plan_data['name']}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"MAX MEMORY - QUICK SETUP")
    print(f"{'='*60}\n")
    
    try:
        user, token = setup_test_user()
        check_email_config()
        create_sample_plans()
        
        print(f"{'='*60}")
        print(f"✅ SETUP COMPLETE!")
        print(f"{'='*60}\n")
        print(f"You can now:")
        print(f"  1. Test authentication in Swagger (use token above)")
        print(f"  2. Login via API with test@example.com / password123")
        print(f"  3. Access all protected endpoints")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
