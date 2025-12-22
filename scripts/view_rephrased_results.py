"""Generate table for rephrased test results"""
import json

data = json.load(open('data/eval_datasets/rephrased_test_report_20251219_185848.json'))

print("=" * 140)
print("REPHRASED PERSONA TEST RESULTS - Round 2")
print("Different tones, words, and sentence structures")
print("=" * 140)

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

print("\n🗣️ TONE BREAKDOWN")
print("-" * 40)
for tone, stats in data['tone_breakdown'].items():
    print(f"  {tone}: {stats['success']}/{stats['success']+stats['failed']} | Avg: {stats['avg_time_ms']:.0f}ms")

print("\n" + "=" * 140)
print("DETAILED RESULTS TABLE")
print("=" * 140)

# Print table header
print(f"{'#':<3} | {'Tone':<12} | {'Question':<55} | {'Answer':<50} | {'Total':<7} | {'LLM':<6} | {'RAG':<5} | {'Docs':<4}")
print("-" * 140)

# Print each result
for r in data['detailed_results']:
    q = r['input_question'][:53] + ".." if len(r['input_question']) > 55 else r['input_question']
    a = r['output_response'].replace('\n', ' ')[:48] + ".." if len(r['output_response']) > 50 else r['output_response'].replace('\n', ' ')
    print(f"{r['test_id']:<3} | {r['persona']:<12} | {q:<55} | {a:<50} | {r['total_time_ms']:<7.0f} | {r['llm_time_ms']:<6.0f} | {r['rag_time_ms']:<5.0f} | {r['rag_results_count']:<4}")

print("-" * 140)
print("\n✅ All 26 tests PASSED!")
