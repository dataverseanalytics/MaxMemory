import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI").replace("neo4j+s://", "neo4j+ssc://")

username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

import logging
import sys

# Disable debug logging for clarity
# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.DEBUG)
# logging.getLogger("neo4j").addHandler(handler)
# logging.getLogger("neo4j").setLevel(logging.DEBUG)

print(f"Connecting to {uri} as {username}")

try:
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    print("Connectivity Verification Successful")
    with driver.session() as session:
        print("\n--- Project Inspection ---")
        result = session.run("""
            MATCH (d:Document) 
            RETURN d.id as id, d.source as source, d.user_id as user_id, d.project_id as project_id
            LIMIT 10
        """)
        records = list(result)
        if not records:
             print("No Documents found in Neo4j.")
        for r in records:
            print(f"Doc: {r['id']} | User: {r['user_id']} | Project: {r['project_id']}")
            
    driver.close()
except Exception as e:
    print(f"Connection Failed: {e}")
