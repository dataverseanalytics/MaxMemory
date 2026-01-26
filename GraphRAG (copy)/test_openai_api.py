#!/usr/bin/env python3
"""
Test OpenAI API Connection
Checks if API key is valid and services are working
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import time

# Load environment
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

print("╔═══════════════════════════════════════════════════════════╗")
print("║          OPENAI API CONNECTION TEST                      ║")
print("╚═══════════════════════════════════════════════════════════╝")

# Check API key
print(f"\n[1] Checking API Key...")
if api_key:
    print(f"✓ API Key found: {api_key[:20]}...{api_key[-10:]}")
else:
    print("✗ API Key NOT found in .env file!")
    exit(1)

# Test Chat API
print(f"\n[2] Testing Chat API (gpt-4o-mini)...")
try:
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
    print(f"✓ Chat API initialized")
    
    # Simple test
    print(f"  → Sending test message...")
    start = time.time()
    response = llm.invoke("Say 'API is working' in one sentence")
    elapsed = time.time() - start
    
    print(f"✓ Response received in {elapsed:.2f}s")
    print(f"  Answer: {response.content}")
    
except Exception as e:
    print(f"✗ Chat API FAILED: {str(e)[:100]}")
    if "401" in str(e) or "unauthorized" in str(e).lower():
        print("  → Invalid or expired API key")
    elif "429" in str(e) or "rate" in str(e).lower():
        print("  → Rate limit exceeded")
    elif "timeout" in str(e).lower() or "connection" in str(e).lower():
        print("  → Network connection issue")

# Test Embeddings API
print(f"\n[3] Testing Embeddings API (text-embedding-3-small)...")
try:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    print(f"✓ Embeddings API initialized")
    
    # Simple test
    print(f"  → Creating embedding for test text...")
    start = time.time()
    embedding = embeddings.embed_query("Parth Kumar works at DRC Systems")
    elapsed = time.time() - start
    
    print(f"✓ Embedding created in {elapsed:.2f}s")
    print(f"  Dimension: {len(embedding)} (expected 1536)")
    print(f"  First 5 values: {embedding[:5]}")
    
except Exception as e:
    print(f"✗ Embeddings API FAILED: {str(e)[:100]}")
    if "401" in str(e) or "unauthorized" in str(e).lower():
        print("  → Invalid or expired API key")
    elif "429" in str(e) or "rate" in str(e).lower():
        print("  → Rate limit exceeded")
    elif "timeout" in str(e).lower() or "connection" in str(e).lower():
        print("  → Network connection issue")

print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)
print("""
✓ If both tests passed:
  → Your OpenAI API is working correctly
  → You can run queries normally
  → The system should work without issues

✗ If Chat API failed:
  → Check your internet connection
  → Verify API key in .env file
  → Check if account has credits
  → Try: https://platform.openai.com/account/api-keys

✗ If Embeddings API failed:
  → Similar steps as Chat API
  → Also check if embeddings model is available

Common Issues:
  401 Unauthorized → Invalid API key or expired
  429 Too Many Requests → Rate limit hit (wait and retry)
  Connection Error → No internet or network issue
  Timeout → OpenAI servers slow, try again
""")
