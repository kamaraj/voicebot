"""Speed test with TinyLlama"""
import requests
import time

BASE_URL = "http://127.0.0.1:9011"

# Test queries
queries = [
    "What are the fees?",
    "What are your operating hours?",
    "How do I enroll my child?",
    "What documents do I need?",
    "Do you provide meals?",
]

print("=" * 60)
print("SPEED TEST - TinyLlama")
print("=" * 60)

# Check current model
r = requests.get(f"{BASE_URL}/api/v1/llm/current")
print(f"Model: {r.json()['model']}")
print()

results = []
for i, query in enumerate(queries, 1):
    start = time.time()
    r = requests.post(
        f"{BASE_URL}/api/v1/conversation",
        json={"message": query, "conversation_id": f"speed_test_{i}"},
        timeout=120
    )
    elapsed = (time.time() - start) * 1000
    
    if r.status_code == 200:
        data = r.json()
        rag_count = data.get("metadata", {}).get("rag_results_count", 0)
        resp_len = len(data.get("response", ""))
        print(f"[{i}] {query}")
        print(f"    Time: {elapsed:.0f}ms | RAG: {rag_count} docs | Response: {resp_len} chars")
        results.append(elapsed)
    else:
        print(f"[{i}] {query} - ERROR: {r.status_code}")
        results.append(elapsed)

print()
print("-" * 60)
print(f"Average Response Time: {sum(results)/len(results):.0f}ms")
print(f"Min: {min(results):.0f}ms | Max: {max(results):.0f}ms")
print("=" * 60)

# Now test cache (same query twice)
print("\n💾 CACHE TEST")
print("-" * 40)

query = "What are the enrollment requirements?"

# First query (cache miss)
start = time.time()
r = requests.post(f"{BASE_URL}/api/v1/conversation", json={"message": query, "conversation_id": "cache_test_1"})
time1 = (time.time() - start) * 1000
print(f"First query (cache miss): {time1:.0f}ms")

# Second query (should be cache hit)
start = time.time()
r = requests.post(f"{BASE_URL}/api/v1/conversation", json={"message": query, "conversation_id": "cache_test_2"})
time2 = (time.time() - start) * 1000
print(f"Second query (cache hit): {time2:.0f}ms")

speedup = time1 / time2 if time2 > 0 else 0
print(f"Cache speedup: {speedup:.0f}x faster!")
