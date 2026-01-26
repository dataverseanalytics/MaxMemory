import sys
import os
from sqlalchemy import text
from app.database import engine, Base
from app.models.plan import Plan

def migrate():
    print("🔄 Starting generic migration...")
    
    # 1. Create new tables (like plans)
    Base.metadata.create_all(bind=engine)
    print("✅ Created new tables (if missing)")
    
    # 2. Alter existing tables (sqlite specific for simplicity)
    with engine.connect() as conn:
        # Check is_superuser
        try:
            conn.execute(text("SELECT is_superuser FROM users LIMIT 1"))
            print("ℹ️  Column 'is_superuser' already exists")
        except Exception:
            print("➕ Adding column 'is_superuser'")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT 0"))
                conn.commit()
            except Exception as e:
                print(f"⚠️  Could not add is_superuser: {e}")

        # Check plan_id
        try:
            conn.execute(text("SELECT plan_id FROM users LIMIT 1"))
            print("ℹ️  Column 'plan_id' already exists")
        except Exception:
            print("➕ Adding column 'plan_id'")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN plan_id INTEGER REFERENCES plans(id)"))
                conn.commit()
            except Exception as e:
                print(f"⚠️  Could not add plan_id: {e}")

    print("✅ Migration complete")

if __name__ == "__main__":
    migrate()
