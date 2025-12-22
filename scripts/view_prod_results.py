import json
data = json.load(open('data/eval_datasets/production_test_report_20251219_192905.json', encoding='utf-8'))
print('=== PRODUCTION TEST SUMMARY ===')
print(json.dumps(data['summary'], indent=2))
print('\n=== TIMING ===')
print(json.dumps(data['timing'], indent=2))
print('\n=== CATEGORY BREAKDOWN ===')
print(json.dumps(data['category_breakdown'], indent=2))
print('\n=== FAILED TESTS ===')
for t in data.get('failed_tests', []):
    print(f"  [{t['category']}] {t['test_name']}: {t['actual_behavior']}")

# Print cache effectiveness
print('\n=== CACHE EFFECTIVENESS ===')
cache_tests = [r for r in data['detailed_results'] if r['category'] == 'Cache']
for t in cache_tests:
    print(f"  {t['test_name']}: {t['total_time_ms']:.0f}ms")
