"""
Health Check Module
Provides liveness and readiness probes for monitoring
"""
from typing import Dict, Any
import structlog
import time
from datetime import datetime

logger = structlog.get_logger(__name__)


class HealthChecker:
    """
    Health check manager for monitoring system components.
    
    Provides:
    - Liveness probe (is the service running?)
    - Readiness probe (is the service ready to handle requests?)
    - Component health checks
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_check_time = None
        self.component_status: Dict[str, Dict[str, Any]] = {}
        logger.info("health_checker_initialized")
    
    def check_liveness(self) -> Dict[str, Any]:
        """
        Liveness probe - is the application running?
        
        Returns:
            Health status with uptime
        """
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_human": self._format_uptime(uptime_seconds)
        }
    
    def check_readiness(
        self,
        llm_client=None,
        cache=None,
        memory=None,
        rag=None
    ) -> Dict[str, Any]:
        """
        Readiness probe - is the application ready to serve requests?
        
        Checks all critical components.
        
        Returns:
            Health status with component details
        """
        checks = {}
        overall_ready = True
        
        # Check LLM
        if llm_client:
            try:
                # Quick ping to Ollama
                import requests
                response = requests.get(
                    "http://localhost:11434/api/tags",
                    timeout=2
                )
                checks["llm"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                checks["llm"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_ready = False
        
        # Check cache
        if cache:
            try:
                stats = cache.get_stats()
                checks["cache"] = {
                    "status": "healthy",
                    "size": stats.get("size", 0),
                    "thread_safe": stats.get("thread_safe", False)
                }
            except Exception as e:
                checks["cache"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_ready = False
        
        # Check memory
        if memory:
            try:
                stats = memory.get_stats()
                checks["memory"] = {
                    "status": "healthy",
                    "active_conversations": stats.get("active_conversations", 0),
                    "thread_safe": stats.get("thread_safe", False)
                }
            except Exception as e:
                checks["memory"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_ready = False
        
        # Check RAG
        if rag:
            try:
                stats = rag.get_stats()
                checks["rag"] = {
                    "status": "healthy",
                    "documents": stats.get("total_documents", 0)
                }
            except Exception as e:
                checks["rag"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                # RAG is optional, don't mark as not ready
        
        self.last_check_time = datetime.now()
        
        return {
            "status": "ready" if overall_ready else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "ready": overall_ready
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)


# Global instance
_health_checker = None

def get_health_checker() -> HealthChecker:
    """Get or create health checker singleton"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
