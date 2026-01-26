import sys
import os
from app.database import SessionLocal
from app.models.user import User
from app.models.plan import Plan

def promote_user(email: str):
    # Ensure tables exist
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    print(f"ℹ️  Database: {engine.url}")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"⚠️  User with email '{email}' not found.")
            # Create the user
            from app.core.security import get_password_hash
            user = User(
                email=email,
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            db.add(user)
            db.commit()
            print(f"✅ Created new Admin user '{email}' with password 'admin123'.")
            return

        if user.is_superuser:
            print(f"ℹ️  User '{email}' is already an admin.")
        else:
            user.is_superuser = True
            db.commit()
            print(f"✅ Successfully promoted '{email}' to Admin.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email>")
        # Default fallback for ease of use if they edit the file
        print("Please provide an email argument.")
    else:
        promote_user(sys.argv[1])
