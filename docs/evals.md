# Evaluation & Testing Guide

## Overview

This guide covers the comprehensive evaluation and testing framework for the VoiceBot AI platform.

## Evaluation Framework

### 1. Automated Evaluations

#### DeepEval Metrics

We use DeepEval for automated LLM evaluation:

```python
from src.evals.framework import EvaluationFramework
from src.agents.voice_agent import VoiceAgent

agent = VoiceAgent()
eval_framework = EvaluationFramework(agent)

# Run evaluation
results = await eval_framework.eval_test_suite(
    test_cases=test_cases,
    suite_name="smoke_tests"
)
```

**Metrics Tracked:**
- **Answer Relevancy**: Is the response relevant to the query?
- **Faithfulness**: Is the response faithful to the context?
- **Hallucination**: Does the model hallucinate facts?
- **Toxicity**: Is the response toxic or harmful?

#### Custom Metrics

```python
from src.evals.framework import (
    ConversationalQualityEvaluator,
    LatencyEvaluator
)

# Coherence
coherence = ConversationalQualityEvaluator.evaluate_coherence(messages)

# Latency distribution
latency_stats = LatencyEvaluator.evaluate_response_time(latencies)
```

### 2. Test Suites

#### Basic Functionality Tests
```python
SAMPLE_TEST_CASES = [
    {
        "input": "What time is it?",
        "expected_output": "The current time is",
        "tags": ["time", "simple"]
    },
    # ... more cases
]
```

#### Persona-Based Tests
```python
from src.tests.personas import PersonaGenerator

generator = PersonaGenerator()
personas = generator.generate_persona_suite(count=20)

# Each persona has different behaviors
for persona in personas:
    test_with_persona(persona)
```

**Persona Types:**
- Cooperative (clear communication)
- Confused (needs clarification)
- Impatient (wants quick resolution)
- Verbose (provides too much detail)
- Technical (uses jargon)
- Casual (informal, slang)
- Adversarial (tests edge cases, security)

#### Edge Case Tests
- Very long inputs (>1000 chars)
- Empty inputs
- Special characters
- Multiple languages
- Emojis
- Prompt injection attempts
- PII in input

### 3. Running Evaluations

```bash
# Run all evaluations
python scripts/run_evals.py

# Run specific test suite
pytest tests/e2e/ -m persona

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### 4. Evaluation Results

Results are saved to `data/eval_datasets/`:
```json
{
  "eval_id": "eval_20241204_123456",
  "model": "llama3.1:8b",
  "test_suite": "basic_functionality",
  "total_tests": 10,
  "passed": 8,
  "failed": 2,
  "pass_rate": 0.80,
  "metrics": {
    "relevancy_avg": 0.85,
    "faithfulness_avg": 0.78,
    "hallucination_avg": 0.12
  }
}
```

## Testing Strategy

### 1. Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_guardrails.py
def test_pii_detection():
    guardrail = PIIGuardrail()
    result = guardrail.check("Email: john@example.com")
    assert not result.passed
```

**Coverage:**
- Guardrails (PII, toxicity, injection)
- Individual tools
- Utility functions

### 2. Integration Tests

Test component interactions:

```python
# tests/integration/test_agent.py
@pytest.mark.asyncio
async def test_agent_with_guardrails():
    agent = VoiceAgent()
    response = await agent.process_message(
        user_message="My SSN is 123-45-6789",
        conversation_id="test_123"
    )
    # Should sanitize PII
    assert "123-45-6789" not in response["response"]
```

**Coverage:**
- Agent workflow
- Tool execution
- Guardrails integration
- Tracing & logging

### 3. End-to-End Tests

Test complete user journeys:

```python
# tests/e2e/test_personas.py
@pytest.mark.asyncio
async def test_full_conversation_flow():
    # Simulate complete conversation
    # From phone call → STT → Agent → TTS → response
    pass
```

### 4. Load Testing

Using Locust for load testing:

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class VoiceBotUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def chat(self):
        self.client.post("/api/v1/conversation", json={
            "message": "Hello",
            "conversation_id": "load_test"
        })
```

Run load test:
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Quality Metrics

### 1. AI Quality

| Metric | Target | Description |
|--------|--------|-------------|
| Relevancy | >0.8 | Response relevance to query |
| Faithfulness | >0.7 | Factual accuracy |
| Hallucination Rate | <0.2 | False information rate |
| Toxicity Rate | <0.05 | Harmful content rate |

### 2. Performance

| Metric | Target | Description |
|--------|--------|-------------|
| P95 Latency | <1s | 95th percentile response time |
| Success Rate | >99% | Request completion rate |
| Availability | >99.9% | System uptime |

### 3. Safety

| Metric | Target | Description |
|--------|--------|-------------|
| Guardrail Pass Rate | >95% | Inputs passing safety checks |
| PII Leak Rate | <0.01% | PII in responses |
| Injection Block Rate | 100% | Blocked prompt injections |

## Regression Testing

### 1. Automated Regression Suite

```bash
# Run before each deployment
pytest tests/ --regression
```

### 2. Version Comparison

```python
# Compare model versions
compare_models(
    model_a="llama3.1:8b",
    model_b="llama3.2:8b",
    test_suite=regression_suite
)
```

### 3. Golden Dataset

Maintain a golden dataset of expected outputs:
```json
{
  "version": "1.0.0",
  "test_cases": [
    {
      "input": "What time is it?",
      "expected_output": "The current time is 3:45 PM",
      "expected_tool_calls": ["get_current_time"]
    }
  ]
}
```

## Human-in-the-Loop Evaluation

### 1. Manual Review

Sample 1% of conversations for manual quality review:
```python
# Sample conversations
sampled = sample_conversations(percentage=0.01)

# Review interface
review_interface.present(sampled)
```

### 2. A/B Testing

Compare different prompts, models, or configurations:
```python
ab_test = ABTest(
    variant_a="prompt_v1",
    variant_b="prompt_v2",
    traffic_split=0.5
)

results = ab_test.run(duration=timedelta(days=7))
```

### 3. User Feedback Collection

```python
# After each conversation
collect_feedback(
    conversation_id="conv_123",
    rating=5,  # 1-5 stars
    feedback_text="Very helpful!"
)
```

## Continuous Evaluation

### 1. Production Monitoring

Monitor quality in production:
```python
# Real-time evaluation
for conversation in production_stream:
    quality_score = evaluate_quality(conversation)
    if quality_score < threshold:
        alert_team()
```

### 2. Drift Detection

Detect model drift:
```python
drift_detector.check(
    baseline_metrics=baseline,
    current_metrics=current,
    threshold=0.1  # 10% degradation triggers alert
)
```

## Best Practices

### 1. Test Early and Often
- Write tests alongside code
- Run tests before commits
- Automated CI/CD testing

### 2. Diverse Test Data
- Multiple languages
- Various demographics
- Edge cases
- Adversarial examples

### 3. Realistic Scenarios
- Use synthetic personas
- Simulate real conversations
- Test full user journeys

### 4. Track Metrics Over Time
- Store evaluation results
- Track trends
- Compare versions
- Monitor regressions

### 5. Balance Automation and Human Review
- Automate repetitive checks
- Human review for quality
- Combine both approaches

## Reporting

### 1. Daily Reports
```bash
python scripts/generate_daily_report.py
```

### 2. Weekly Summaries
- Model performance trends
- Quality metrics
- Cost analysis
- Incident reports

### 3. Release Reports
Before each release:
- Full regression test results
- Performance benchmarks
- Security audit
- A/B test results
