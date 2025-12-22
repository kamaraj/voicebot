"""
KPI Dashboard - Real-time metrics and analytics.
Displays key performance indicators for the AI system.
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
import structlog

logger = structlog.get_logger(__name__)


class KPIDashboard:
    """
    Tracks and reports KPIs for the voice AI platform.
    """
    
    def __init__(self):
        self.metrics_history = []
        logger.info("kpi_dashboard_initialized")
    
    def record_conversation_metrics(self, metrics: Dict[str, Any]):
        """Record metrics from a conversation."""
        metrics["timestamp"] = datetime.now().isoformat()
        self.metrics_history.append(metrics)
    
    def get_performance_kpis(self, time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """
        Get performance KPIs for the specified time window.
        
        Returns:
            Dictionary of KPIs
        """
        cutoff = datetime.now() - time_window
        
        # Filter recent metrics
        recent = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not recent:
            return {"error": "No data in time window"}
        
        # Calculate KPIs
        latencies = [m.get("latency", 0) for m in recent]
        token_counts = [m.get("tokens", 0) for m in recent]
        costs = [m.get("cost", 0) for m in recent]
        
        kpis = {
            # Performance Metrics
            "performance": {
                "total_requests": len(recent),
                "avg_latency_ms": sum(latencies) / len(latencies) * 1000 if latencies else 0,
                "p50_latency_ms": sorted(latencies)[len(latencies) // 2] * 1000 if latencies else 0,
                "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] * 1000 if latencies else 0,
                "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)] * 1000 if latencies else 0,
            },
            
            # Quality Metrics
            "quality": {
                "avg_response_quality": self._avg_metric(recent, "quality_score"),
                "guardrail_pass_rate": self._pass_rate(recent, "guardrails_passed"),
                "hallucination_rate": self._avg_metric(recent, "hallucination_score"),
                "toxicity_rate": self._avg_metric(recent, "toxicity_score"),
            },
            
            # Usage Metrics
            "usage": {
                "total_tokens": sum(token_counts),
                "avg_tokens_per_request": sum(token_counts) / len(token_counts) if token_counts else 0,
                "total_conversations": len(set(m.get("conversation_id") for m in recent if m.get("conversation_id"))),
            },
            
            # Cost Metrics
            "cost": {
                "total_cost_usd": sum(costs),
                "avg_cost_per_request": sum(costs) / len(costs) if costs else 0,
                "cost_per_1k_requests": (sum(costs) / len(costs) * 1000) if costs else 0,
            },
            
            # Business Metrics
            "business": {
                "task_completion_rate": self._pass_rate(recent, "task_completed"),
                "user_satisfaction": self._avg_metric(recent, "satisfaction_score"),
                "avg_conversation_length": self._avg_metric(recent, "conversation_turns"),
                "transfer_rate": self._pass_rate(recent, "transferred"),
            },
            
            # Reliability Metrics
            "reliability": {
                "success_rate": self._pass_rate(recent, "success"),
                "error_rate": 1 - self._pass_rate(recent, "success"),
                "timeout_rate": self._pass_rate(recent, "timeout"),
            }
        }
        
        return kpis
    
    def _avg_metric(self, data: List[Dict], key: str) -> float:
        """Calculate average for a metric."""
        values = [d.get(key) for d in data if d.get(key) is not None]
        return sum(values) / len(values) if values else 0.0
    
    def _pass_rate(self, data: List[Dict], key: str) -> float:
        """Calculate pass/true rate for a boolean metric."""
        values = [d.get(key) for d in data if d.get(key) is not None]
        if not values:
            return 0.0
        return sum(1 for v in values if v) / len(values)
    
    def generate_report(self, time_window: timedelta = timedelta(hours=24)) -> str:
        """
        Generate a human-readable KPI report.
        
        Args:
            time_window: Time window for metrics
            
        Returns:
            Formatted report string
        """
        kpis = self.get_performance_kpis(time_window)
        
        if "error" in kpis:
            return kpis["error"]
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║          VOICEBOT AI - KPI DASHBOARD REPORT                  ║
║          {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                          ║
╚══════════════════════════════════════════════════════════════╝

📊 PERFORMANCE METRICS
  ├─ Total Requests: {kpis['performance']['total_requests']:,}
  ├─ Avg Latency: {kpis['performance']['avg_latency_ms']:.0f}ms
  ├─ P95 Latency: {kpis['performance']['p95_latency_ms']:.0f}ms
  └─ P99 Latency: {kpis['performance']['p99_latency_ms']:.0f}ms

✅ QUALITY METRICS
  ├─ Response Quality: {kpis['quality']['avg_response_quality']:.2%}
  ├─ Guardrail Pass Rate: {kpis['quality']['guardrail_pass_rate']:.2%}
  ├─ Hallucination Rate: {kpis['quality']['hallucination_rate']:.2%}
  └─ Toxicity Rate: {kpis['quality']['toxicity_rate']:.2%}

📈 USAGE METRICS
  ├─ Total Tokens: {kpis['usage']['total_tokens']:,}
  ├─ Avg Tokens/Request: {kpis['usage']['avg_tokens_per_request']:.0f}
  └─ Total Conversations: {kpis['usage']['total_conversations']:,}

💰 COST METRICS
  ├─ Total Cost: ${kpis['cost']['total_cost_usd']:.4f}
  ├─ Avg Cost/Request: ${kpis['cost']['avg_cost_per_request']:.6f}
  └─ Cost per 1K Requests: ${kpis['cost']['cost_per_1k_requests']:.2f}

🎯 BUSINESS METRICS
  ├─ Task Completion: {kpis['business']['task_completion_rate']:.2%}
  ├─ User Satisfaction: {kpis['business']['user_satisfaction']:.2%}
  ├─ Avg Conv Length: {kpis['business']['avg_conversation_length']:.1f} turns
  └─ Transfer Rate: {kpis['business']['transfer_rate']:.2%}

🔧 RELIABILITY METRICS
  ├─ Success Rate: {kpis['reliability']['success_rate']:.2%}
  ├─ Error Rate: {kpis['reliability']['error_rate']:.2%}
  └─ Timeout Rate: {kpis['reliability']['timeout_rate']:.2%}

═══════════════════════════════════════════════════════════════
"""
        return report
    
    def export_json(self, filepath: str = "data/kpi_report.json"):
        """Export KPIs to JSON file."""
        kpis = self.get_performance_kpis()
        
        with open(filepath, "w") as f:
            json.dump(kpis, f, indent=2)
        
        logger.info("kpi_report_exported", filepath=filepath)


# Global KPI dashboard
kpi_dashboard = KPIDashboard()


# Example usage
"""
from src.observability.kpi_dashboard import kpi_dashboard

# Record metrics from a conversation
kpi_dashboard.record_conversation_metrics({
    "conversation_id": "conv_123",
    "latency": 0.543,
    "tokens": 150,
    "cost": 0.0001,
    "quality_score": 0.85,
    "guardrails_passed": True,
    "task_completed": True,
    "satisfaction_score": 0.9,
    "success": True
})

# Generate report
report = kpi_dashboard.generate_report()
print(report)

# Export to JSON
kpi_dashboard.export_json()
"""
