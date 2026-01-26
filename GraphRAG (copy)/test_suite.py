"""
Comprehensive Test Suite for GraphRAG
Tests 100+ use cases to verify accuracy across all possible scenarios
"""

import sys
sys.path.insert(0, '/home/parth/Desktop/Learning/GraphRAG')

from retrieve import QueryRetrieval
from ingest import ingestion
from memory_manager import load_vector_store, clear_all_memories, add_chunk_memory
import json
from datetime import datetime

# Initialize
load_vector_store()
retrieval = QueryRetrieval()

# Test data structure
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "test_categories": {},
    "failures": []
}

def test_case(category, query, expected_keywords, test_num):
    """
    Run a single test case
    
    Args:
        category: Test category (e.g., "friendship", "job", "location")
        query: Question to ask
        expected_keywords: List of keywords that should appear in answer
        test_num: Test number for reference
    """
    global test_results
    
    if category not in test_results["test_categories"]:
        test_results["test_categories"][category] = {"passed": 0, "failed": 0}
    
    test_results["total_tests"] += 1
    
    try:
        # Ask the question
        result = retrieval.ask_question(query, k=5)
        answer = result['answer'].lower()
        
        # Check if expected keywords are in answer
        keywords_found = [kw for kw in expected_keywords if kw.lower() in answer]
        match_percentage = len(keywords_found) / len(expected_keywords) * 100 if expected_keywords else 100
        
        # Test passes if at least 60% of keywords are found
        if match_percentage >= 60:
            test_results["passed"] += 1
            test_results["test_categories"][category]["passed"] += 1
            status = "✅ PASS"
        else:
            test_results["failed"] += 1
            test_results["test_categories"][category]["failed"] += 1
            status = "❌ FAIL"
            test_results["failures"].append({
                "test_num": test_num,
                "category": category,
                "query": query,
                "expected": expected_keywords,
                "found": keywords_found,
                "answer": answer[:100]
            })
        
        print(f"[{test_num}] {status} | {category:15} | {query[:50]:50} | Match: {match_percentage:.0f}%")
        
    except Exception as e:
        test_results["failed"] += 1
        test_results["test_categories"][category]["failed"] += 1
        status = "❌ ERROR"
        test_results["failures"].append({
            "test_num": test_num,
            "category": category,
            "query": query,
            "error": str(e)
        })
        print(f"[{test_num}] {status} | {category:15} | {query[:50]:50} | Error: {str(e)[:40]}")

def run_comprehensive_tests():
    """Run 100+ comprehensive test cases"""
    
    print("\n" + "="*120)
    print("GRAPHRAG COMPREHENSIVE TEST SUITE - 100+ USE CASES")
    print("="*120 + "\n")
    
    test_num = 1
    
    # CATEGORY 1: FRIENDSHIP QUERIES (15 tests)
    print("\n--- CATEGORY 1: FRIENDSHIP QUERIES ---\n")
    
    test_case("friendship", "who is my good friend?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "who are my good friends?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "Is Raju your friend?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("friendship", "Is Adil your friend?", ["adil", "friend"], test_num)
    test_num += 1
    
    test_case("friendship", "tell me about my friends", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "who is your best friend?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "my frends are?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "raju is my good friend or not?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("friendship", "Is Raju a good friend of mine?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("friendship", "Tell me all my friends", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "Who are people I am friends with?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "List my close friends", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "Who do you consider as your friend?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "Name your friends", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("friendship", "how many friends do you have?", ["raju", "adil"], test_num)
    test_num += 1
    
    # CATEGORY 2: JOB/WORK QUERIES (15 tests)
    print("\n--- CATEGORY 2: JOB/WORK QUERIES ---\n")
    
    test_case("job", "What is your job?", ["software engineer", "drc"], test_num)
    test_num += 1
    
    test_case("job", "What do you do?", ["software engineer", "work"], test_num)
    test_num += 1
    
    test_case("job", "Where do you work?", ["drc systems"], test_num)
    test_num += 1
    
    test_case("job", "Tell me about your job", ["software engineer", "drc"], test_num)
    test_num += 1
    
    test_case("job", "Are you a software engineer?", ["software engineer", "yes"], test_num)
    test_num += 1
    
    test_case("job", "Do you work at DRC?", ["drc", "yes"], test_num)
    test_num += 1
    
    test_case("job", "What's your profession?", ["software engineer"], test_num)
    test_num += 1
    
    test_case("job", "Where is your workplace?", ["drc systems"], test_num)
    test_num += 1
    
    test_case("job", "Who is your employer?", ["drc"], test_num)
    test_num += 1
    
    test_case("job", "Tell me about your work", ["software engineer"], test_num)
    test_num += 1
    
    test_case("job", "What position do you hold?", ["engineer", "software"], test_num)
    test_num += 1
    
    test_case("job", "Describe your career", ["software", "engineer"], test_num)
    test_num += 1
    
    test_case("job", "What company do you work for?", ["drc", "systems"], test_num)
    test_num += 1
    
    test_case("job", "Are you employed?", ["drc", "yes"], test_num)
    test_num += 1
    
    test_case("job", "Tell me your occupation", ["software engineer"], test_num)
    test_num += 1
    
    # CATEGORY 3: PERSONAL PREFERENCES (15 tests)
    print("\n--- CATEGORY 3: PERSONAL PREFERENCES ---\n")
    
    test_case("preferences", "What do you like?", ["ai", "reading", "python", "coffee", "sunny"], test_num)
    test_num += 1
    
    test_case("preferences", "Tell me your likes and dislikes", ["like", "dislike"], test_num)
    test_num += 1
    
    test_case("preferences", "Do you like AI?", ["ai", "yes"], test_num)
    test_num += 1
    
    test_case("preferences", "What are your hobbies?", ["reading", "python", "ai"], test_num)
    test_num += 1
    
    test_case("preferences", "Do you enjoy reading?", ["reading", "yes"], test_num)
    test_num += 1
    
    test_case("preferences", "What programming language do you prefer?", ["python"], test_num)
    test_num += 1
    
    test_case("preferences", "Do you like cats?", ["cats", "yes"], test_num)
    test_num += 1
    
    test_case("preferences", "What weather do you prefer?", ["sunny", "weather"], test_num)
    test_num += 1
    
    test_case("preferences", "Do you hate rainy days?", ["rainy", "hate"], test_num)
    test_num += 1
    
    test_case("preferences", "What do you enjoy?", ["sunny", "cats", "coffee", "reading"], test_num)
    test_num += 1
    
    test_case("preferences", "Tell me your interests", ["ai", "reading", "python"], test_num)
    test_num += 1
    
    test_case("preferences", "What things do you like?", ["ai", "reading", "coffee"], test_num)
    test_num += 1
    
    test_case("preferences", "Do you like technology?", ["technology", "ai", "python"], test_num)
    test_num += 1
    
    test_case("preferences", "What makes you happy?", ["reading", "ai", "coffee"], test_num)
    test_num += 1
    
    test_case("preferences", "Describe what you enjoy", ["sunny", "cats", "coffee"], test_num)
    test_num += 1
    
    # CATEGORY 4: RAJU INFORMATION (15 tests)
    print("\n--- CATEGORY 4: RAJU INFORMATION QUERIES ---\n")
    
    test_case("raju_info", "Who is Raju?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("raju_info", "Tell me about Raju", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Does Raju still work at DRC?", ["raju", "no", "left"], test_num)
    test_num += 1
    
    test_case("raju_info", "What does Raju do now?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Is Raju still working at DRC Systems?", ["raju", "no"], test_num)
    test_num += 1
    
    test_case("raju_info", "When did Raju leave DRC?", ["raju", "month", "left"], test_num)
    test_num += 1
    
    test_case("raju_info", "What is Raju's current job?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Is Raju your colleague?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("raju_info", "Tell me everything about Raju", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Where is Raju working now?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "What happened to Raju?", ["left", "drc"], test_num)
    test_num += 1
    
    test_case("raju_info", "Is Raju employed?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "How is Raju doing?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Raju's current status?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("raju_info", "Tell me Raju's story", ["raju", "freelance"], test_num)
    test_num += 1
    
    # CATEGORY 5: TYPO/MISSPELLING HANDLING (10 tests)
    print("\n--- CATEGORY 5: TYPO/MISSPELLING HANDLING ---\n")
    
    test_case("typo_handling", "raju is my good fidn or not ?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("typo_handling", "who is my frend?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("typo_handling", "do you wrk at drc?", ["drc", "yes"], test_num)
    test_num += 1
    
    test_case("typo_handling", "are you a softwre engineer?", ["engineer", "software"], test_num)
    test_num += 1
    
    test_case("typo_handling", "what is your ocupation?", ["engineer", "software"], test_num)
    test_num += 1
    
    test_case("typo_handling", "who are your frends?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("typo_handling", "tell me ur likes", ["ai", "reading"], test_num)
    test_num += 1
    
    test_case("typo_handling", "do you like pyton?", ["python"], test_num)
    test_num += 1
    
    test_case("typo_handling", "whos your employer?", ["drc"], test_num)
    test_num += 1
    
    test_case("typo_handling", "raaju still at drc?", ["raju", "no"], test_num)
    test_num += 1
    
    # CATEGORY 6: RELATIONSHIP QUERIES (10 tests)
    print("\n--- CATEGORY 6: RELATIONSHIP QUERIES ---\n")
    
    test_case("relationships", "Who works with you?", ["raju", "drc"], test_num)
    test_num += 1
    
    test_case("relationships", "Who are your colleagues?", ["raju"], test_num)
    test_num += 1
    
    test_case("relationships", "Are Raju and you friends?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("relationships", "Do you know Raju?", ["raju", "yes"], test_num)
    test_num += 1
    
    test_case("relationships", "Tell me about your relationships", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("relationships", "Who do you work with?", ["raju"], test_num)
    test_num += 1
    
    test_case("relationships", "Are you and Raju close?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("relationships", "List your connections", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("relationships", "Who are the people in your network?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("relationships", "Tell me about people you know", ["raju", "adil"], test_num)
    test_num += 1
    
    # CATEGORY 7: MULTIPLE CHOICE QUESTIONS (10 tests)
    print("\n--- CATEGORY 7: YES/NO AND MULTIPLE CHOICE ---\n")
    
    test_case("yes_no", "Do you work?", ["yes", "software"], test_num)
    test_num += 1
    
    test_case("yes_no", "Are you a software engineer?", ["yes", "software"], test_num)
    test_num += 1
    
    test_case("yes_no", "Do you have friends?", ["yes", "raju"], test_num)
    test_num += 1
    
    test_case("yes_no", "Do you like AI?", ["yes", "ai"], test_num)
    test_num += 1
    
    test_case("yes_no", "Is DRC Systems your workplace?", ["yes", "drc"], test_num)
    test_num += 1
    
    test_case("yes_no", "Does Raju work at DRC?", ["no", "raju"], test_num)
    test_num += 1
    
    test_case("yes_no", "Do you prefer Python?", ["yes", "python"], test_num)
    test_num += 1
    
    test_case("yes_no", "Are you a freelancer?", ["no", "engineer"], test_num)
    test_num += 1
    
    test_case("yes_no", "Have you left your job?", ["no", "working"], test_num)
    test_num += 1
    
    test_case("yes_no", "Is Adil your friend?", ["yes", "adil"], test_num)
    test_num += 1
    
    # CATEGORY 8: COMPLEX MULTI-PART QUESTIONS (10 tests)
    print("\n--- CATEGORY 8: COMPLEX MULTI-PART QUESTIONS ---\n")
    
    test_case("complex", "Who is Raju and is he your friend?", ["raju", "friend"], test_num)
    test_num += 1
    
    test_case("complex", "What do you do and where do you work?", ["engineer", "drc"], test_num)
    test_num += 1
    
    test_case("complex", "Tell me about your friends and your job", ["raju", "engineer"], test_num)
    test_num += 1
    
    test_case("complex", "Does Raju still work at DRC and are you friends?", ["raju", "freelance"], test_num)
    test_num += 1
    
    test_case("complex", "What do you like and what do you dislike?", ["like", "dislike"], test_num)
    test_num += 1
    
    test_case("complex", "Who are your friends and where do they work?", ["raju", "adil"], test_num)
    test_num += 1
    
    test_case("complex", "Tell me about yourself - job, friends, interests", ["engineer", "raju", "ai"], test_num)
    test_num += 1
    
    test_case("complex", "What has changed with Raju? Is he still at DRC?", ["raju", "no"], test_num)
    test_num += 1
    
    test_case("complex", "Who works with you and do you like them?", ["raju"], test_num)
    test_num += 1
    
    test_case("complex", "Tell me your complete background", ["engineer", "raju"], test_num)
    test_num += 1
    
    # CATEGORY 9: CASUAL/CONVERSATIONAL (5 tests)
    print("\n--- CATEGORY 9: CASUAL/CONVERSATIONAL ---\n")
    
    test_case("casual", "Hey, tell me about yourself", ["engineer", "raju"], test_num)
    test_num += 1
    
    test_case("casual", "So what's up with you?", ["engineer", "friend"], test_num)
    test_num += 1
    
    test_case("casual", "Give me the lowdown", ["engineer", "raju"], test_num)
    test_num += 1
    
    test_case("casual", "What's new with you?", ["working", "engineer"], test_num)
    test_num += 1
    
    test_case("casual", "How you doin?", ["good", "friend"], test_num)
    test_num += 1
    
    # CATEGORY 10: NEGATION/COMPARISON QUERIES (5 tests)
    print("\n--- CATEGORY 10: NEGATION/COMPARISON QUERIES ---\n")
    
    test_case("negation", "Are you NOT a software engineer?", ["no", "engineer"], test_num)
    test_num += 1
    
    test_case("negation", "Is Raju still employed at DRC?", ["no", "left"], test_num)
    test_num += 1
    
    test_case("negation", "You don't like rainy weather, right?", ["rainy", "no"], test_num)
    test_num += 1
    
    test_case("negation", "Raju is NOT your friend?", ["yes", "friend"], test_num)
    test_num += 1
    
    test_case("negation", "You're not a freelancer?", ["no", "engineer"], test_num)
    test_num += 1
    
    return test_num

def print_summary():
    """Print test summary and statistics"""
    
    print("\n" + "="*120)
    print("TEST SUMMARY")
    print("="*120 + "\n")
    
    total = test_results["total_tests"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests Run: {total}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Accuracy: {accuracy:.1f}%")
    
    print("\n" + "-"*120)
    print("RESULTS BY CATEGORY")
    print("-"*120 + "\n")
    
    for category, results in sorted(test_results["test_categories"].items()):
        cat_total = results["passed"] + results["failed"]
        cat_accuracy = (results["passed"] / cat_total * 100) if cat_total > 0 else 0
        print(f"{category:20} | Passed: {results['passed']:2} | Failed: {results['failed']:2} | Accuracy: {cat_accuracy:5.1f}%")
    
    if test_results["failures"]:
        print("\n" + "-"*120)
        print(f"FAILED TESTS ({len(test_results['failures'])} total)")
        print("-"*120 + "\n")
        
        for failure in test_results["failures"][:20]:  # Show first 20 failures
            print(f"Test #{failure['test_num']} - {failure['category']}")
            print(f"  Query: {failure['query']}")
            if "error" in failure:
                print(f"  Error: {failure['error']}")
            else:
                print(f"  Expected: {failure['expected']}")
                print(f"  Found: {failure['found']}")
                print(f"  Answer: {failure['answer'][:80]}...")
            print()
    
    # Save results to file
    with open('/home/parth/Desktop/Learning/GraphRAG/test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n✅ Full results saved to: test_results.json")
    
    # Return summary string
    return f"\n{'='*120}\nFINAL RESULT: {accuracy:.1f}% ACCURACY ({passed}/{total} tests passed)\n{'='*120}"

if __name__ == "__main__":
    print("\n⏳ Loading GraphRAG system...")
    print("📚 Preparing test suite with 100+ use cases...\n")
    
    try:
        test_num = run_comprehensive_tests()
        summary = print_summary()
        print(summary)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        summary = print_summary()
        print(summary)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
