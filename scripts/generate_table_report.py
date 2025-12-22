"""Generate formatted table report of synthetic test results"""
import json
import csv
from pathlib import Path

# Load test results
data = json.load(open('data/eval_datasets/synthetic_test_report_20251219_180245.json'))

print("=" * 150)
print("SYNTHETIC PERSONA TEST RESULTS - DETAILED TABLE")
print("=" * 150)
print()

# Header
header = f"{'#':<4} | {'Persona':<18} | {'Question':<50} | {'Answer':<45} | {'Total(ms)':<10} | {'LLM(ms)':<8} | {'RAG(ms)':<8} | {'RAG Docs':<8} | {'Status':<6}"
print(header)
print("-" * 150)

# Rows
for r in data['detailed_results']:
    slno = r['test_id']
    persona = r['persona'][:18]
    question = r['input_question'][:48] + ".." if len(r['input_question']) > 50 else r['input_question']
    answer = r['output_response'][:43] + ".." if len(r['output_response']) > 45 else r['output_response']
    total_ms = f"{r['total_time_ms']:.0f}"
    llm_ms = f"{r['llm_time_ms']:.0f}"
    rag_ms = f"{r['rag_time_ms']:.0f}"
    rag_docs = r['rag_results_count']
    status = "PASS" if r['success'] else "FAIL"
    
    row = f"{slno:<4} | {persona:<18} | {question:<50} | {answer:<45} | {total_ms:<10} | {llm_ms:<8} | {rag_ms:<8} | {rag_docs:<8} | {status:<6}"
    print(row)

print("-" * 150)
print()

# Save to CSV
csv_path = Path('data/eval_datasets/synthetic_test_results_table.csv')
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Header
    writer.writerow([
        'SlNo', 'Persona', 'Question', 'Answer (Full)', 
        'Total Time (ms)', 'LLM Time (ms)', 'RAG Time (ms)', 
        'RAG Docs', 'Status', 'Timestamp'
    ])
    # Data rows
    for r in data['detailed_results']:
        writer.writerow([
            r['test_id'],
            r['persona'],
            r['input_question'],
            r['output_response'],
            round(r['total_time_ms'], 2),
            round(r['llm_time_ms'], 2),
            round(r['rag_time_ms'], 2),
            r['rag_results_count'],
            'PASS' if r['success'] else 'FAIL',
            r['timestamp']
        ])

print(f"📄 CSV exported to: {csv_path}")
print()

# Also print full details for markdown
print("\n" + "=" * 100)
print("FULL QUESTION & ANSWER DETAILS")
print("=" * 100)

for r in data['detailed_results']:
    print(f"\n### Test #{r['test_id']} - {r['persona'].upper()}")
    print(f"**Question:** {r['input_question']}")
    print(f"**Answer:** {r['output_response']}")
    print(f"**Metrics:** Total: {r['total_time_ms']:.0f}ms | LLM: {r['llm_time_ms']:.0f}ms | RAG: {r['rag_time_ms']:.0f}ms | Docs: {r['rag_results_count']}")
    print("-" * 80)
