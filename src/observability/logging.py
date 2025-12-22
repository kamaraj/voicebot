"""
Structured logging configuration using structlog.
Provides context-aware, JSON-formatted logs for production observability.
"""
import logging
import sys
from typing import Any, Dict
import structlog
from structlog.types import EventDict, Processor
from pythonjsonlogger import jsonlogger


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application-wide context to all log events."""
    event_dict["app"] = "voicebot"
    event_dict["environment"] = "production"  # Override from config
    return event_dict


def add_trace_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add trace ID for request correlation."""
    # Will be populated by middleware
    trace_id = structlog.contextvars.get_contextvars().get("trace_id")
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict


def add_user_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add user context for security and debugging."""
    user_id = structlog.contextvars.get_contextvars().get("user_id")
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with JSON output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure structlog processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        add_trace_id,
        add_user_context,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerAdapter:
    """
    Adapter for adding context to all logs within a scope.
    
    Usage:
        with LoggerAdapter(logger, conversation_id="123"):
            logger.info("user_message", text="Hello")
    """
    
    def __init__(self, logger: structlog.stdlib.BoundLogger, **context: Any):
        self.logger = logger
        self.context = context
        
    def __enter__(self) -> structlog.stdlib.BoundLogger:
        """Bind context on enter."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self.logger
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear context on exit."""
        structlog.contextvars.clear_contextvars()


# Example usage and best practices
"""
# Initialize logging
from src.observability.logging import configure_logging, get_logger

configure_logging("INFO")
logger = get_logger(__name__)

# Simple logging
logger.info("api_request_started", method="POST", path="/api/chat")

# With context
logger.info(
    "llm_response_generated",
    model="llama3.1:8b",
    tokens=150,
    latency_ms=234,
    cost_usd=0.0001
)

# With structured data
logger.error(
    "guardrail_violation",
    violation_type="pii_detected",
    entities=["email", "phone"],
    input_text="<redacted>",
    user_id="user_123"
)

# With context manager
from src.observability.logging import LoggerAdapter

with LoggerAdapter(logger, conversation_id="conv_123", user_id="user_456"):
    logger.info("conversation_started")
    logger.info("user_message", text="Hello")
    logger.info("agent_response", text="Hi there!")
"""
