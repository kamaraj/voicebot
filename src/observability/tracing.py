"""
Distributed tracing for Agentic AI workflows using LangSmith and Phoenix.
Captures full conversation traces, LLM calls, tool usage, and performance metrics.
"""
from typing import Any, Dict, Optional, Callable
from functools import wraps
import time
import uuid
from contextlib import contextmanager

from langsmith import Client as LangSmithClient
from langsmith.run_helpers import traceable
import structlog

from src.config.settings import settings

logger = structlog.get_logger(__name__)


class TracingManager:
    """
    Manages distributed tracing across LangSmith and Phoenix.
    """
    
    def __init__(self):
        self.langsmith_client = None
        self.phoenix_enabled = settings.phoenix_enabled
        
        if settings.langchain_tracing_v2 and settings.langchain_api_key:
            try:
                self.langsmith_client = LangSmithClient(
                    api_key=settings.langchain_api_key
                )
                logger.info("langsmith_initialized", project=settings.langchain_project)
            except Exception as e:
                logger.error("langsmith_init_failed", error=str(e))
    
    def create_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return f"trace_{uuid.uuid4().hex[:16]}"
    
    @contextmanager
    def trace_conversation(self, conversation_id: str, metadata: Optional[Dict] = None):
        """
        Context manager for tracing entire conversations.
        
        Args:
            conversation_id: Unique conversation identifier
            metadata: Additional metadata to attach
            
        Yields:
            Trace context
        """
        trace_id = self.create_trace_id()
        start_time = time.time()
        
        trace_data = {
            "trace_id": trace_id,
            "conversation_id": conversation_id,
            "start_time": start_time,
            **(metadata or {})
        }
        
        logger.info("trace_started", **trace_data)
        
        try:
            yield trace_data
        except Exception as e:
            logger.error(
                "trace_error",
                trace_id=trace_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        finally:
            duration = time.time() - start_time
            logger.info(
                "trace_completed",
                trace_id=trace_id,
                duration_seconds=duration
            )


def trace_llm_call(
    model: str,
    provider: str = "ollama"
) -> Callable:
    """
    Decorator for tracing LLM calls with comprehensive metrics.
    
    Args:
        model: Model name
        provider: LLM provider (ollama, openai, etc.)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            trace_id = f"llm_{uuid.uuid4().hex[:12]}"
            
            # Extract prompt from kwargs
            prompt = kwargs.get("prompt", "")
            max_tokens = kwargs.get("max_tokens", settings.max_tokens_per_request)
            
            logger.info(
                "llm_call_started",
                trace_id=trace_id,
                model=model,
                provider=provider,
                prompt_length=len(prompt),
                max_tokens=max_tokens
            )
            
            try:
                # Execute LLM call
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                duration = time.time() - start_time
                output_tokens = len(result.get("text", "")) // 4  # Rough estimate
                
                logger.info(
                    "llm_call_completed",
                    trace_id=trace_id,
                    model=model,
                    duration_seconds=duration,
                    output_tokens=output_tokens,
                    latency_ms=duration * 1000
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "llm_call_failed",
                    trace_id=trace_id,
                    model=model,
                    error=str(e),
                    duration_seconds=duration
                )
                raise
                
        return wrapper
    return decorator


def trace_agent_step(
    step_name: str,
    step_type: str = "reasoning"
) -> Callable:
    """
    Decorator for tracing individual agent steps (reasoning, tool calls, etc.).
    
    Args:
        step_name: Name of the step
        step_type: Type of step (reasoning, tool_call, memory_retrieval, etc.)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            step_id = f"step_{uuid.uuid4().hex[:12]}"
            
            logger.info(
                "agent_step_started",
                step_id=step_id,
                step_name=step_name,
                step_type=step_type
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    "agent_step_completed",
                    step_id=step_id,
                    step_name=step_name,
                    duration_seconds=duration
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "agent_step_failed",
                    step_id=step_id,
                    step_name=step_name,
                    error=str(e),
                    duration_seconds=duration
                )
                raise
                
        return wrapper
    return decorator


def trace_tool_call(tool_name: str) -> Callable:
    """
    Decorator for tracing tool/function calls by the agent.
    
    Args:
        tool_name: Name of the tool being called
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            tool_id = f"tool_{uuid.uuid4().hex[:12]}"
            
            logger.info(
                "tool_call_started",
                tool_id=tool_id,
                tool_name=tool_name,
                args=str(args)[:100],  # Truncate for logging
                kwargs=str(kwargs)[:100]
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    "tool_call_completed",
                    tool_id=tool_id,
                    tool_name=tool_name,
                    duration_seconds=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "tool_call_failed",
                    tool_id=tool_id,
                    tool_name=tool_name,
                    error=str(e),
                    duration_seconds=duration
                )
                raise
                
        return wrapper
    return decorator


# Global tracing manager instance
tracing_manager = TracingManager()


# Example usage
"""
from src.observability.tracing import (
    tracing_manager,
    trace_llm_call,
    trace_agent_step,
    trace_tool_call
)

# Trace entire conversation
async def handle_conversation(conversation_id: str):
    with tracing_manager.trace_conversation(
        conversation_id=conversation_id,
        metadata={"user_id": "user_123", "channel": "phone"}
    ):
        # Your conversation logic here
        await process_user_input()
        await generate_response()

# Trace LLM calls
@trace_llm_call(model="llama3.1:8b", provider="ollama")
async def call_llm(prompt: str, max_tokens: int = 500):
    # LLM call logic
    return {"text": "Response"}

# Trace agent steps
@trace_agent_step(step_name="intent_recognition", step_type="reasoning")
async def recognize_intent(user_input: str):
    # Intent recognition logic
    return {"intent": "book_appointment"}

# Trace tool calls
@trace_tool_call(tool_name="calendar_search")
async def search_calendar(date: str):
    # Calendar search logic
    return {"available_slots": ["10am", "2pm"]}
"""
