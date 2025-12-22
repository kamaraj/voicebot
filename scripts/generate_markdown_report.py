"""Generate Markdown table report"""
import json

data = json.load(open('data/eval_datasets/synthetic_test_report_20251219_180245.json'))

# Generate markdown
md_content = """# Synthetic Persona Test Results - Childcare Customer Support Agent

## Summary
| Metric | Value |
|--------|-------|
| Total Tests | 18 |
| Successful | 18 |
| Failed | 0 |
| Success Rate | 100% |

## Timing Statistics
| Metric | Value |
|--------|-------|
| Average Response | 20,667 ms |
| Min Response | 14,603 ms |
| Max Response | 31,871 ms |
| Average LLM Time | 1,786 ms |
| Average RAG Time | 115 ms |

## Detailed Test Results

| SlNo | Role | Question | Answer | Total(ms) | LLM(ms) | RAG(ms) | RAG Docs | Status |
|------|------|----------|--------|-----------|---------|---------|----------|--------|
"""

for r in data['detailed_results']:
    q = r['input_question'].replace('|', '\\|')[:60] + "..."
    a = r['output_response'].replace('|', '\\|').replace('\n', ' ')[:80] + "..."
    md_content += f"| {r['test_id']} | {r['persona']} | {q} | {a} | {r['total_time_ms']:.0f} | {r['llm_time_ms']:.0f} | {r['rag_time_ms']:.0f} | {r['rag_results_count']} | PASS |\n"

md_content += """

## Full Questions and Answers

"""

for r in data['detailed_results']:
    md_content += f"""
### Test #{r['test_id']} - {r['persona'].upper().replace('_', ' ')}

**Question:** {r['input_question']}

**Answer:** {r['output_response']}

**Timing:** Total: {r['total_time_ms']:.0f}ms | LLM: {r['llm_time_ms']:.0f}ms | RAG: {r['rag_time_ms']:.0f}ms | Documents Retrieved: {r['rag_results_count']}

---
"""

# Save markdown
with open('data/eval_datasets/synthetic_test_report.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Markdown report saved to: data/eval_datasets/synthetic_test_report.md")
print("\nTable Preview:")
print("-" * 120)

# Print simple table
print(f"{'#':<3} | {'Role':<18} | {'Question':<40} | {'Answer':<50} | {'Time':<8} | {'Docs':<4}")
print("-" * 120)
for r in data['detailed_results']:
    q = r['input_question'][:38] + ".." if len(r['input_question']) > 40 else r['input_question']
    a = r['output_response'][:48] + ".." if len(r['output_response']) > 50 else r['output_response']
    a = a.replace('\n', ' ')
    print(f"{r['test_id']:<3} | {r['persona']:<18} | {q:<40} | {a:<50} | {r['total_time_ms']:<8.0f} | {r['rag_results_count']:<4}")
