import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

# Target User and Project from your specific request
TARGET_USER_ID = "3"
TARGET_PROJECT_ID = "1"

print(f"Connecting to {uri}...")

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    
    with driver.session() as session:
        print(f"Migrating orphan documents to User {TARGET_USER_ID}, Project {TARGET_PROJECT_ID}...")
        
        # Update Documents
        result = session.run("""
            MATCH (d:Document)
            WHERE d.project_id IS NULL OR d.user_id IS NULL
            SET d.project_id = $pid, d.user_id = $uid
            RETURN count(d) as updated_docs
        """, pid=TARGET_PROJECT_ID, uid=TARGET_USER_ID)
        print(f"Updated {result.single()['updated_docs']} documents.")
        
        # Update Memories
        result = session.run("""
            MATCH (m:Memory)
            WHERE m.project_id IS NULL OR m.user_id IS NULL
            SET m.project_id = $pid, m.user_id = $uid
            RETURN count(m) as updated_memories
        """, pid=TARGET_PROJECT_ID, uid=TARGET_USER_ID)
        print(f"Updated {result.single()['updated_memories']} memories.")
        
    driver.close()
    print("Migration complete!")
except Exception as e:
    print(f"Migration Failed: {e}")
