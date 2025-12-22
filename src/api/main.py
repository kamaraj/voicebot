"""
FastAPI application with comprehensive instrumentation.
Production-ready API with tracing, metrics, and guardrails.
"""
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST
from pydantic import BaseModel
import structlog

from src.config.settings import settings
from src.observability.logging import configure_logging, get_logger
from src.observability.metrics import metrics
from src.observability.tracing import tracing_manager
from src.agents.voice_agent import VoiceAgent
from src.agents.fast_voice_agent import FastVoiceAgent  # Optimized agent!
from src.guardrails.engine import guardrails_engine
from src.api.voice import router as voice_router  # Now using pywhispercpp!
from src.api.documents import router as documents_router  # Document upload API
from src.api.fastrtc_websocket import router as fastrtc_router  # FastRTC real-time streaming!
from src.health import get_health_checker
from src.validation import ConversationRequest as ValidatedConversationRequest, sanitize_output

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)

# Use validated request model
ConversationRequest = ValidatedConversationRequest



class ConversationResponse(BaseModel):
    """Response model for conversation endpoint."""
    conversation_id: str
    response: str
    tool_results: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    timing: Dict[str, float] = {}  # New field for timing metrics


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model: str
    features: Dict[str, bool]


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info(
        "application_starting",
        env=settings.env,
        model=settings.ollama_model
    )
    
    # Initialize OPTIMIZED agent with token counting!
    app.state.agent = FastVoiceAgent()
    logger.info("using_fast_voice_agent", model=app.state.agent.model_name)
    
    # Initialize FastRTC service with the agent
    from src.services.fastrtc_service import get_fastrtc_service
    app.state.fastrtc = get_fastrtc_service(llm_agent=app.state.agent)
    logger.info("fastrtc_service_initialized")
    
    logger.info("application_ready")
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI app
app = FastAPI(
    title="VoiceBot Agentic AI Platform",
    description="Production-ready voice AI platform with comprehensive observability",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include voice API router (using pywhispercpp!)
app.include_router(voice_router)

# Include documents API router (PDF/TXT/MD uploads)
app.include_router(documents_router)

# Include FastRTC router (real-time voice streaming!)
app.include_router(fastrtc_router)


# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track all HTTP requests with metrics and tracing."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to context
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method
    )
    
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )
    
    # Process request
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Track metrics
        metrics.track_request(
            endpoint=request.url.path,
            method=request.method,
            status=response.status_code,
            duration=duration
        )
        
        logger.info(
            "request_completed",
            request_id=request_id,
            status_code=response.status_code,
            duration_seconds=duration
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(
            "request_failed",
            request_id=request_id,
            error=str(e),
            duration_seconds=duration
        )
        
        metrics.track_request(
            endpoint=request.url.path,
            method=request.method,
            status=500,
            duration=duration
        )
        
        raise
    finally:
        structlog.contextvars.clear_contextvars()




# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        model=settings.ollama_model,
        features={
            "guardrails": settings.guardrails_enabled,
            "tracing": settings.langchain_tracing_v2,
            "metrics": settings.prometheus_enabled,
            "function_calling": settings.enable_function_calling,
            "rag": settings.enable_rag
        }
    )


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=metrics.export_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


# ==============================================
# LLM PROVIDER MANAGEMENT ENDPOINTS
# ==============================================

@app.get("/api/v1/llm/providers")
async def list_llm_providers():
    """
    List all available LLM providers.
    
    Returns:
        List of available providers with status
    """
    from src.llm import list_available_providers, get_llm_provider
    
    providers = list_available_providers()
    current = app.state.agent.provider_name if hasattr(app.state, 'agent') else "unknown"
    
    provider_info = []
    for name in providers:
        info = {
            "name": name,
            "active": name == current,
            "description": {
                "ollama": "Local LLM (free, runs on your machine)",
                "gemini": "Google Gemini API (fast, cheap)",
                "openai": "OpenAI GPT models (powerful)",
                "groq": "Groq ultra-fast inference (free tier available)"
            }.get(name, "Unknown provider")
        }
        provider_info.append(info)
    
    return {
        "current_provider": current,
        "current_model": app.state.agent.model_name if hasattr(app.state, 'agent') else "unknown",
        "available_providers": provider_info
    }


@app.get("/api/v1/llm/current")
async def get_current_llm():
    """Get current LLM provider information."""
    if not hasattr(app.state, 'agent'):
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    agent = app.state.agent
    
    return {
        "provider": agent.provider_name,
        "model": agent.model_name,
        "token_stats": agent.token_counter.get_stats()
    }


class SwitchProviderRequest(BaseModel):
    """Request to switch LLM provider."""
    provider: str  # "ollama", "gemini", "openai", "groq"
    model: Optional[str] = None  # Optional specific model


@app.post("/api/v1/llm/switch")
async def switch_llm_provider(request: SwitchProviderRequest):
    """
    Switch to a different LLM provider at runtime.
    
    Args:
        provider: Provider name ("ollama", "gemini", "openai", "groq")
        model: Optional model name
        
    Returns:
        New provider information
    """
    from src.llm import get_llm_provider, list_available_providers
    
    available = list_available_providers()
    if request.provider not in available:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown provider: {request.provider}. Available: {available}"
        )
    
    try:
        # Create new agent with specified provider
        new_agent = FastVoiceAgent(
            provider=request.provider,
            model_name=request.model
        )
        
        # Replace the current agent
        app.state.agent = new_agent
        
        # Update FastRTC service with new agent
        app.state.fastrtc.llm_agent = new_agent
        
        logger.info(
            "llm_provider_switched",
            provider=new_agent.provider_name,
            model=new_agent.model_name
        )
        
        return {
            "success": True,
            "provider": new_agent.provider_name,
            "model": new_agent.model_name,
            "message": f"Switched to {new_agent.provider_name}:{new_agent.model_name}"
        }
        
    except Exception as e:
        logger.error("llm_switch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/llm/health")
async def check_llm_health():
    """Check health of current LLM provider."""
    if not hasattr(app.state, 'agent'):
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        health = app.state.agent.llm.health_check()
        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Main conversation endpoint
@app.post("/api/v1/conversation", response_model=ConversationResponse)
async def handle_conversation(
    request: ConversationRequest,
    agent: VoiceAgent = Depends(lambda: app.state.agent)
):
    """
    Process a conversation message through the AI agent.
    
    Args:
        request: Conversation request with message and context
        agent: VoiceAgent instance (injected)
        
    Returns:
        AI response with metadata
    """
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:16]}"
    
    logger.info(
        "conversation_request",
        conversation_id=conversation_id,
        user_id=request.user_id,
        message_length=len(request.message)
    )
    
    # Trace conversation
    with tracing_manager.trace_conversation(
        conversation_id=conversation_id,
        metadata={
            "user_id": request.user_id,
            "endpoint": "/api/v1/conversation"
        }
    ):
        try:
            # Process through agent
            start_time = time.time()
            
            # FastVoiceAgent uses process_message_fast instead of process_message
            result = await agent.process_message_fast(
                user_message=request.message,
                conversation_id=conversation_id,
                user_id=request.user_id,
                context=request.context
            )
            
            duration = time.time() - start_time
            
            logger.info(
                "conversation_completed",
                conversation_id=conversation_id,
                duration_seconds=duration,
                response_length=len(result["response"])
            )
            
            return ConversationResponse(
                conversation_id=conversation_id,
                response=result["response"],
                tool_results=result.get("tool_results", {}),
                metadata={
                    **result.get("metadata", {}),
                    "duration_seconds": duration
                },
                timing=result.get("timing", {})  # Include timing data
            )
            
        except Exception as e:
            logger.error(
                "conversation_error",
                conversation_id=conversation_id,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error processing conversation: {str(e)}"
            )


# Guardrails test endpoint
@app.post("/api/v1/guardrails/check")
async def check_guardrails(text: str):
    """
    Test guardrails on input text.
    
    Args:
        text: Text to check
        
    Returns:
        Guardrail check results
    """
    input_checks = guardrails_engine.check_input(text)
    
    results = {
        check_name: {
            "passed": check.passed,
            "violations": check.violations,
            "metadata": check.metadata
        }
        for check_name, check in input_checks.items()
    }
    
    return {
        "all_passed": all(check.passed for check in input_checks.values()),
        "checks": results
    }


# Agent capabilities endpoint
@app.get("/api/v1/agent/capabilities")
async def get_agent_capabilities(
    agent: VoiceAgent = Depends(lambda: app.state.agent)
):
    """Get agent capabilities and available tools."""
    return {
        "model": agent.model_name,
        "tools": list(agent.tools.keys()),
        "features": {
            "multi_step_reasoning": True,
            "function_calling": settings.enable_function_calling,
            "memory": settings.enable_memory,
            "rag": settings.enable_rag
        }
    }


# Token usage statistics endpoint
@app.get("/api/v1/token-stats")
async def get_token_stats(
    agent: VoiceAgent = Depends(lambda: app.state.agent)
):
    """Get token usage statistics."""
    try:
        # Check if agent has token_counter attribute (FastVoiceAgent has it)
        if hasattr(agent, 'token_counter'):
            return agent.token_counter.get_stats()
        else:
            # Fallback for VoiceAgent without token counting
            return {
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "avg_tokens_per_request": 0,
                "estimated_cost": {
                    "ollama": 0.0,
                    "gpt-4-turbo": 0.0,
                    "gpt-3.5-turbo": 0.0,
                    "claude-3-sonnet": 0.0
                },
                "note": "Token counting not available with current agent. Switch to FastVoiceAgent."
            }
    except Exception as e:
        logger.error("token_stats_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error getting token stats: {str(e)}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path
    )
    
    metrics.errors.labels(
        error_type=type(exc).__name__,
        component="api",
        severity="high"
    ).inc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Chat UI endpoint (Unified: Voice + Text)
@app.get("/chat")
async def chat_ui():
    """Serve the unified voice + text chat interface."""
    return FileResponse("static/index.html")


# Voice Chat UI endpoint (Unified: Voice + Text)
@app.get("/voice")
async def voice_chat_ui():
    """Serve the voice chat interface."""
    return FileResponse("static/voice_chat.html")


# Help page - lists all knowledge base documents
@app.get("/help")
async def help_page():
    """Serve the help page with knowledge base info."""
    return FileResponse("static/help.html")


# About page - application information
@app.get("/about")
async def about_page():
    """Serve the about page."""
    return FileResponse("static/about.html")


# Voice Test endpoint
@app.get("/test")
async def voice_test():
    """Serve the working voice test page."""
    return FileResponse("static/voice_test.html")


# Microphone Test endpoint
@app.get("/mictest")
async def mic_test():
    """Serve the microphone test page."""
    return FileResponse("static/mic_test.html")


# FastRTC Voice AI endpoint
@app.get("/fastrtc")
async def fastrtc_voice():
    """Serve the FastRTC real-time voice AI interface."""
    return FileResponse("static/fastrtc_voice.html")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "VoiceBot Agentic AI Platform",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": {
            "liveness": "/health/live",
            "readiness": "/health/ready",
            "full": "/health"
        },
        "metrics": "/metrics",
        "interfaces": {
            "chat": "/chat",
            "voice": "/voice",
            "fastrtc": "/fastrtc",  # NEW: Ultra-fast <2s voice AI
            "upload": "/static/upload_documents.html",
            "documents": "/documents"
        },
        "features": {
            "fastrtc": "Real-time voice streaming with <2 second latency",
            "websocket": "/api/v1/rtc/stream",
            "rag": "Retrieval Augmented Generation",
            "caching": "Response caching for instant replies"
        }
    }


# Documents List UI endpoint
@app.get("/documents")
async def documents_list_ui():
    """Serve the documents list interface."""
    return FileResponse("static/documents_list.html")


@app.get("/health/live")
async def health_liveness():
    """
    Liveness probe - is the application running?
    
    Returns 200 if application is alive.
    Used by Kubernetes/Docker for liveness checks.
    """
    health_checker = get_health_checker()
    result = health_checker.check_liveness()
    
    logger.debug("liveness_check", status=result["status"])
    return result


@app.get("/health/ready")
async def health_readiness():
    """
    Readiness probe - is the application ready to serve traffic?
    
    Returns 200 if all components are healthy.
    Returns 503 if any critical component is unhealthy.
    Used by Kubernetes/Docker for readiness checks.
    """
    health_checker = get_health_checker()
    
    # Get all components
    result = health_checker.check_readiness(
        llm_client=app.state.agent.llm,
        cache=app.state.agent.cache,
        memory=app.state.agent.memory,
        rag=app.state.agent.rag
    )
    
    logger.debug("readiness_check", 
                status=result["status"],
                ready=result["ready"])
    
    # Return 503 if not ready
    if not result["ready"]:
        return JSONResponse(
            status_code=503,
            content=result
        )
    
    return result


@app.get("/health")
async def health_full():
    """
    Full health check - comprehensive system health.
    
    Returns detailed health information about all components.
    """
    health_checker = get_health_checker()
    
    # Liveness
    liveness = health_checker.check_liveness()
    
    # Readiness
    readiness = health_checker.check_readiness(
        llm_client=app.state.agent.llm,
        cache=app.state.agent.cache,
        memory=app.state.agent.memory,
        rag=app.state.agent.rag
    )
    
    # Component stats
    cache_stats = app.state.agent.cache.get_stats() if app.state.agent.cache else {}
    memory_stats = app.state.agent.memory.get_stats() if app.state.agent.memory else {}
    rag_stats = app.state.agent.rag.get_stats() if app.state.agent.rag else {}
    token_stats = app.state.agent.token_counter.get_stats() if hasattr(app.state.agent, 'token_counter') else {}
    
    result = {
        "status": "healthy" if readiness["ready"] else "degraded",
        "liveness": liveness,
        "readiness": readiness,
        "components": {
            "cache": cache_stats,
            "memory": memory_stats,
            "rag": rag_stats,
            "tokens": token_stats
        },
        "features": {
            "guardrails": settings.guardrails_enabled,
            "rag": settings.enable_rag,
            "caching": True,
            "memory": True,
            "async": True
        }
    }
    
    logger.info("full_health_check", status=result["status"])
    
    return result



if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        log_config=None  # Use our custom logging
    )
