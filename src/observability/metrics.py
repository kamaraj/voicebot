"""
Prometheus metrics collection for monitoring AI system performance.
Tracks latency, costs, quality, and business KPIs.
"""
from typing import Dict, Any
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST
)
import structlog

from src.config.settings import settings

logger = structlog.get_logger(__name__)


class MetricsCollector:
    """
    Centralized metrics collection for the AI voice platform.
    """
    
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize all Prometheus metrics."""
        
        # ============= REQUEST METRICS =============
        self.request_count = Counter(
            'voicebot_requests_total',
            'Total number of API requests',
            ['endpoint', 'method', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'voicebot_request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )
        
        # ============= LLM METRICS =============
        self.llm_calls = Counter(
            'voicebot_llm_calls_total',
            'Total LLM API calls',
            ['model', 'provider', 'status'],
            registry=self.registry
        )
        
        self.llm_latency = Histogram(
            'voicebot_llm_latency_seconds',
            'LLM response latency',
            ['model', 'provider'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        self.llm_tokens = Summary(
            'voicebot_llm_tokens',
            'Token usage per LLM call',
            ['model', 'token_type'],  # input, output
            registry=self.registry
        )
        
        self.llm_cost = Counter(
            'voicebot_llm_cost_usd',
            'Total LLM cost in USD',
            ['model', 'provider'],
            registry=self.registry
        )
        
        # ============= AGENT METRICS =============
        self.agent_steps = Counter(
            'voicebot_agent_steps_total',
            'Total agent reasoning steps',
            ['step_type', 'status'],  # reasoning, tool_call, memory_retrieval
            registry=self.registry
        )
        
        self.tool_calls = Counter(
            'voicebot_tool_calls_total',
            'Tool/function calls by agent',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        self.agent_conversation_length = Histogram(
            'voicebot_conversation_turns',
            'Number of turns in conversation',
            buckets=[1, 5, 10, 20, 50, 100],
            registry=self.registry
        )
        
        # ============= GUARDRAIL METRICS =============
        self.guardrail_checks = Counter(
            'voicebot_guardrail_checks_total',
            'Total guardrail checks',
            ['check_type', 'result'],  # pii, toxicity, prompt_injection
            registry=self.registry
        )
        
        self.guardrail_violations = Counter(
            'voicebot_guardrail_violations_total',
            'Guardrail violations detected',
            ['violation_type', 'severity'],
            registry=self.registry
        )
        
        # ============= VOICE METRICS =============
        self.stt_calls = Counter(
            'voicebot_stt_calls_total',
            'Speech-to-text API calls',
            ['provider', 'language', 'status'],
            registry=self.registry
        )
        
        self.stt_latency = Histogram(
            'voicebot_stt_latency_seconds',
            'STT processing latency',
            ['provider'],
            buckets=[0.1, 0.3, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        self.tts_calls = Counter(
            'voicebot_tts_calls_total',
            'Text-to-speech API calls',
            ['provider', 'voice', 'status'],
            registry=self.registry
        )
        
        self.tts_latency = Histogram(
            'voicebot_tts_latency_seconds',
            'TTS processing latency',
            ['provider'],
            buckets=[0.1, 0.3, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        # ============= TELEPHONY METRICS =============
        self.call_count = Counter(
            'voicebot_calls_total',
            'Total phone calls',
            ['direction', 'status'],  # inbound/outbound, completed/failed
            registry=self.registry
        )
        
        self.call_duration = Histogram(
            'voicebot_call_duration_seconds',
            'Call duration',
            buckets=[10, 30, 60, 120, 300, 600, 1800],
            registry=self.registry
        )
        
        self.active_calls = Gauge(
            'voicebot_active_calls',
            'Number of currently active calls',
            registry=self.registry
        )
        
        # ============= QUALITY METRICS =============
        self.response_quality = Histogram(
            'voicebot_response_quality_score',
            'AI response quality score (0-1)',
            buckets=[0.1, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0],
            registry=self.registry
        )
        
        self.user_satisfaction = Counter(
            'voicebot_user_satisfaction_total',
            'User satisfaction ratings',
            ['rating'],  # 1-5 stars
            registry=self.registry
        )
        
        self.task_completion = Counter(
            'voicebot_task_completion_total',
            'Task completion outcomes',
            ['task_type', 'outcome'],  # success, failure, partial
            registry=self.registry
        )
        
        # ============= ERROR METRICS =============
        self.errors = Counter(
            'voicebot_errors_total',
            'Application errors',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )
        
        # ============= BUSINESS METRICS =============
        self.revenue = Counter(
            'voicebot_revenue_usd',
            'Revenue generated',
            ['plan_type'],
            registry=self.registry
        )
        
        logger.info("metrics_initialized", metrics_count=len(self.registry._collector_to_names))
    
    def track_request(self, endpoint: str, method: str, status: int, duration: float):
        """Track HTTP request."""
        self.request_count.labels(endpoint=endpoint, method=method, status=status).inc()
        self.request_duration.labels(endpoint=endpoint, method=method).observe(duration)
    
    def track_llm_call(
        self,
        model: str,
        provider: str,
        latency: float,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        status: str = "success"
    ):
        """Track LLM API call."""
        self.llm_calls.labels(model=model, provider=provider, status=status).inc()
        self.llm_latency.labels(model=model, provider=provider).observe(latency)
        self.llm_tokens.labels(model=model, token_type="input").observe(input_tokens)
        self.llm_tokens.labels(model=model, token_type="output").observe(output_tokens)
        self.llm_cost.labels(model=model, provider=provider).inc(cost)
    
    def track_guardrail(self, check_type: str, result: str, violation: bool = False, severity: str = "low"):
        """Track guardrail check."""
        self.guardrail_checks.labels(check_type=check_type, result=result).inc()
        if violation:
            self.guardrail_violations.labels(violation_type=check_type, severity=severity).inc()
    
    def track_tool_call(self, tool_name: str, status: str = "success"):
        """Track agent tool call."""
        self.tool_calls.labels(tool_name=tool_name, status=status).inc()
    
    def track_call(self, direction: str, status: str, duration: float = None):
        """Track phone call."""
        self.call_count.labels(direction=direction, status=status).inc()
        if duration:
            self.call_duration.observe(duration)
    
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest(self.registry)


# Global metrics instance
metrics = MetricsCollector()


# Example usage
"""
from src.observability.metrics import metrics

# Track API request
async def handle_request(request):
    start_time = time.time()
    response = await process_request(request)
    duration = time.time() - start_time
    
    metrics.track_request(
        endpoint="/api/chat",
        method="POST",
        status=200,
        duration=duration
    )
    return response

# Track LLM call
metrics.track_llm_call(
    model="llama3.1:8b",
    provider="ollama",
    latency=0.543,
    input_tokens=120,
    output_tokens=85,
    cost=0.0  # Free for local
)

# Track guardrail
metrics.track_guardrail(
    check_type="pii_detection",
    result="pass",
    violation=False
)

# Track tool call
metrics.track_tool_call(
    tool_name="calendar_search",
    status="success"
)

# Export for Prometheus scraping
@app.get("/metrics")
async def get_metrics():
    return Response(
        content=metrics.export_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )
"""
