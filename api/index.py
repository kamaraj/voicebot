"""
Vercel Serverless Handler for VoiceBot API.
Uses the api/ directory pattern for proper ASGI recognition.
"""
import os
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
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "conversation": "/conversation",
            "providers": "/llm/providers"
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


# Duplicate endpoint for compatibility with different URL patterns
@app.post("/api/v1/conversation", response_model=ConversationResponse)
async def handle_conversation_v1(request: ConversationRequest):
    """Process a conversation message (v1 API path)."""
    return await handle_conversation(request)


# Knowledge Base Documents (Static FAQ info for Vercel deployment)
FAQ_DOCUMENTS = [
    {
        "id": "1",
        "name": "System Usage FAQ",
        "filename": "1_System_Usage_FAQ.md",
        "topic": "System Usage",
        "questions_count": 10,
        "size_kb": 6.1,
        "status": "indexed"
    },
    {
        "id": "2",
        "name": "Admission & Enrollment FAQ",
        "filename": "2_Admission_Enrollment_FAQ.md",
        "topic": "Admission",
        "questions_count": 10,
        "size_kb": 8.4,
        "status": "indexed"
    },
    {
        "id": "3",
        "name": "Fees & Payment FAQ",
        "filename": "3_Fees_Payment_FAQ.md",
        "topic": "Fees",
        "questions_count": 10,
        "size_kb": 10.2,
        "status": "indexed"
    },
    {
        "id": "4",
        "name": "Hours & Schedule FAQ",
        "filename": "4_Hours_Schedule_FAQ.md",
        "topic": "Schedule",
        "questions_count": 10,
        "size_kb": 7.4,
        "status": "indexed"
    },
    {
        "id": "5",
        "name": "Safety & Security FAQ",
        "filename": "5_Safety_Security_FAQ.md",
        "topic": "Safety",
        "questions_count": 10,
        "size_kb": 8.3,
        "status": "indexed"
    },
    {
        "id": "6",
        "name": "Food & Nutrition FAQ",
        "filename": "6_Food_Nutrition_FAQ.md",
        "topic": "Nutrition",
        "questions_count": 10,
        "size_kb": 9.7,
        "status": "indexed"
    },
    {
        "id": "7",
        "name": "Health & Wellness FAQ",
        "filename": "7_Health_Wellness_FAQ.md",
        "topic": "Health",
        "questions_count": 10,
        "size_kb": 9.4,
        "status": "indexed"
    },
    {
        "id": "8",
        "name": "Daily Activities FAQ",
        "filename": "8_Daily_Activities_FAQ.md",
        "topic": "Activities",
        "questions_count": 10,
        "size_kb": 9.8,
        "status": "indexed"
    },
    {
        "id": "9",
        "name": "Staff Information FAQ",
        "filename": "9_Staff_Info_FAQ.md",
        "topic": "Staff",
        "questions_count": 10,
        "size_kb": 2.6,
        "status": "indexed"
    },
    {
        "id": "10",
        "name": "Policies Guide FAQ",
        "filename": "10_Policies_Guide_FAQ.md",
        "topic": "Policies",
        "questions_count": 10,
        "size_kb": 2.7,
        "status": "indexed"
    }
]


@app.get("/api/v1/documents/list")
async def list_documents():
    """List all knowledge base documents."""
    return {
        "success": True,
        "documents": FAQ_DOCUMENTS,
        "total": len(FAQ_DOCUMENTS),
        "message": "Knowledge base documents (Vercel serverless mode)"
    }


@app.get("/api/v1/documents/stats")
async def get_document_stats():
    """Get knowledge base statistics."""
    total_questions = sum(doc["questions_count"] for doc in FAQ_DOCUMENTS)
    total_size_kb = sum(doc["size_kb"] for doc in FAQ_DOCUMENTS)
    
    return {
        "success": True,
        "stats": {
            "total_documents": len(FAQ_DOCUMENTS),
            "total_questions": total_questions,
            "total_size_kb": round(total_size_kb, 1),
            "topics": [doc["topic"] for doc in FAQ_DOCUMENTS],
            "text_chunks": total_questions * 3,  # Approximate chunks per question
            "embedding_model": "LLM (Groq) - No local embeddings in serverless mode",
            "vector_db": "N/A - Using LLM directly in serverless mode"
        },
        "mode": "serverless",
        "note": "This deployment uses Groq LLM directly. Full RAG with ChromaDB requires local deployment."
    }


@app.get("/api/v1/knowledge-base/info")
async def get_knowledge_base_info():
    """Get comprehensive knowledge base information."""
    total_questions = sum(doc["questions_count"] for doc in FAQ_DOCUMENTS)
    
    return {
        "success": True,
        "knowledge_base": {
            "name": "Childcare Center FAQ Knowledge Base",
            "version": "1.0.0",
            "documents": len(FAQ_DOCUMENTS),
            "text_chunks": total_questions * 3,
            "faq_topics": len(FAQ_DOCUMENTS),
            "questions_covered": total_questions,
            "topics": [
                {"name": doc["topic"], "questions": doc["questions_count"]} 
                for doc in FAQ_DOCUMENTS
            ],
            "sample_questions": [
                "How do I mark daily attendance?",
                "What are the enrollment requirements?",
                "What is the fee structure?",
                "What are the operating hours?",
                "How is my child's safety ensured?",
                "What meals are provided?",
                "What is the sick child policy?",
                "What activities do children do?",
                "What are the staff qualifications?",
                "What is the discipline policy?"
            ]
        },
        "deployment": {
            "type": "Vercel Serverless",
            "llm_provider": "Groq",
            "model": "llama-3.3-70b-versatile",
            "rag_enabled": False,
            "note": "Full RAG with vector search requires local deployment with ChromaDB"
        }
    }
