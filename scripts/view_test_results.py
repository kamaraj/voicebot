"""View synthetic test results"""
import json

data = json.load(open('data/eval_datasets/synthetic_test_report_20251219_180245.json'))

print("=" * 80)
print("SYNTHETIC PERSONA TEST RESULTS - Childcare Customer Support Agent")
print("=" * 80)

print("\n📊 SUMMARY")
print("-" * 40)
print(f"Total Tests: {data['summary']['total_tests']}")
print(f"Successful: {data['summary']['successful']}")
print(f"Failed: {data['summary']['failed']}")
print(f"Success Rate: {data['summary']['success_rate']}")

print("\n⏱️ TIMING STATISTICS")
print("-" * 40)
print(f"Average Response: {data['timing_stats']['average_response_ms']:.0f}ms")
print(f"Min Response: {data['timing_stats']['min_response_ms']:.0f}ms")
print(f"Max Response: {data['timing_stats']['max_response_ms']:.0f}ms")
print(f"Average LLM Time: {data['timing_stats']['average_llm_ms']:.0f}ms")
print(f"Average RAG Time: {data['timing_stats']['average_rag_ms']:.0f}ms")

print("\n📚 RAG STATISTICS")
print("-" * 40)
print(f"Tests with RAG: {data['rag_stats']['tests_with_rag']}")
print(f"Avg Documents Retrieved: {data['rag_stats']['avg_rag_docs_retrieved']}")

print("\n👥 PERSONA BREAKDOWN")
print("-" * 40)
for persona, stats in data['persona_breakdown'].items():
    print(f"{persona}: {stats['success']}/{stats['success']+stats['failed']} tests | Avg: {stats['avg_time_ms']:.0f}ms")

print("\n" + "=" * 80)
print("📝 DETAILED TEST RESULTS")
print("=" * 80)

for r in data['detailed_results']:
    print(f"\n[Test {r['test_id']}] Persona: {r['persona']}")
    print(f"INPUT: {r['input_question']}")
    print(f"OUTPUT: {r['output_response'][:300]}...")
    print(f"TIMING: Total={r['total_time_ms']:.0f}ms | LLM={r['llm_time_ms']:.0f}ms | RAG={r['rag_time_ms']:.0f}ms")
    print(f"RAG: {r['rag_results_count']} documents retrieved")
    print("-" * 60)
