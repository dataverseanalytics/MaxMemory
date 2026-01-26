import sqlite3
import os

DB_FILE = "sql_app.db"

def migrate_db():
    print(f"Checking {DB_FILE}...")
    
    if not os.path.exists(DB_FILE):
        print("Database file not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "credits_balance" not in columns:
        print("Adding credits_balance column to users table...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN credits_balance FLOAT DEFAULT 100.0")
            conn.commit()
            print("✅ Column added successfully.")
        except Exception as e:
            print(f"❌ Failed to add column: {e}")
    else:
        print("Column credits_balance already exists.")
        
    conn.close()

if __name__ == "__main__":
    migrate_db()
