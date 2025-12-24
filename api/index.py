"""
Vercel Serverless Handler for VoiceBot API.
Uses the api/ directory pattern for proper ASGI recognition.
"""
import sys
import os

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import uuid

# Create a lightweight FastAPI app for Vercel
app = FastAPI(
    title="VoiceBot API (Vercel)",
    description="Serverless VoiceBot API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConversationRequest(BaseModel):
    """Request model for conversation endpoint."""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = {}


class ConversationResponse(BaseModel):
    """Response model for conversation endpoint."""
    conversation_id: str
    response: str
    metadata: Dict[str, Any] = {}
    timing: Dict[str, float] = {}


# Global LLM client (lazy initialization)
_llm_client = None


def get_llm_client():
    """Get or create LLM client."""
    global _llm_client
    if _llm_client is None:
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                _llm_client = Groq(api_key=api_key)
            else:
                raise ValueError("GROQ_API_KEY not set")
        except Exception as e:
            print(f"Failed to initialize Groq client: {e}")
            _llm_client = None
    return _llm_client


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "VoiceBot API (Vercel Serverless)",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "endpoints": {
            "health": "/api/health",
            "conversation": "/api/conversation",
            "providers": "/api/llm/providers"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "vercel",
        "features": {
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "gemini": bool(os.getenv("GOOGLE_API_KEY"))
        }
    }


@app.get("/llm/providers")
async def list_providers():
    """List available LLM providers."""
    providers = []
    
    if os.getenv("GROQ_API_KEY"):
        providers.append({
            "name": "groq",
            "active": True,
            "description": "Groq ultra-fast inference"
        })
    
    if os.getenv("GOOGLE_API_KEY"):
        providers.append({
            "name": "gemini",
            "active": False,
            "description": "Google Gemini API"
        })
    
    return {
        "current_provider": "groq" if os.getenv("GROQ_API_KEY") else "none",
        "available_providers": providers
    }


@app.post("/conversation", response_model=ConversationResponse)
async def handle_conversation(request: ConversationRequest):
    """Process a conversation message."""
    conversation_id = request.conversation_id or f"conv_{uuid.uuid4().hex[:16]}"
    start_time = time.time()
    
    try:
        client = get_llm_client()
        if not client:
            raise HTTPException(
                status_code=500,
                detail="LLM client not available. Please check GROQ_API_KEY."
            )
        
        # System prompt for customer support
        system_prompt = """You are a helpful customer support assistant for a childcare center.
You answer questions about admissions, fees, programs, schedules, and policies.
Be friendly, professional, and concise in your responses.
If you don't know the answer, say so honestly and offer to help in other ways."""
        
        # Call Groq API
        llm_start = time.time()
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024
        )
        llm_time = time.time() - llm_start
        
        response_text = chat_completion.choices[0].message.content
        total_time = time.time() - start_time
        
        return ConversationResponse(
            conversation_id=conversation_id,
            response=response_text,
            metadata={
                "model": "llama-3.3-70b-versatile",
                "provider": "groq",
                "tokens": {
                    "input": chat_completion.usage.prompt_tokens if chat_completion.usage else 0,
                    "output": chat_completion.usage.completion_tokens if chat_completion.usage else 0
                }
            },
            timing={
                "total_ms": round(total_time * 1000, 2),
                "llm_ms": round(llm_time * 1000, 2)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing conversation: {str(e)}"
        )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


# Export the app for Vercel
# Vercel looks for 'app' or 'handler' in the module
handler = app
