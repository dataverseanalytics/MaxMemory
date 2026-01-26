
# Verification Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install httpx  # Required for verification script
   ```

2. **Configure Environment**:
   - Ensure `.env` has valid `OPENAI_API_KEY` and Neo4j credentials.
   - Example:
     ```
     OPENAI_API_KEY=sk-...
     NEO4J_URI=bolt://localhost:7687
     NEO4J_USERNAME=neo4j
     NEO4J_PASSWORD=password
     ```

3. **Run Verification Script**:
   ```bash
   python verify_implementation.py
   ```
   - This script tests the API endpoints (Upload, Chat, Search) using mocked services.

4. **Run Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   - Access API Docs: http://localhost:8000/docs

## Troubleshooting
- If you see `pydantic` errors, ensure you have Pydantic v2 installed (`pip install "pydantic>=2.0"`).
- If `verify_implementation.py` fails due to missing `httpx`, run `pip install httpx`.
