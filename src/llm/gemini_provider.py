"""
Google Gemini LLM Provider
===========================
Cloud LLM provider using Google's Gemini API.

Features:
- Ultra-fast inference (~100-500ms)
- Supports Gemini 1.5 Flash, Pro, etc.
- Native async support
- True streaming
- Multi-modal support (future)

Requirements:
    pip install google-generativeai

Environment:
    GOOGLE_API_KEY=your_api_key
"""

import asyncio
import time
import os
from typing import Dict, Any, AsyncGenerator, Optional

from src.llm.base import LLMProvider, LLMProviderType, LLMResponse
import structlog

logger = structlog.get_logger(__name__)

# Lazy import to avoid dependency issues
genai = None


def _ensure_genai():
    """Lazy load google.generativeai"""
    global genai
    if genai is None:
        try:
            import google.generativeai as _genai
            genai = _genai
        except ImportError:
            raise ImportError(
                "google-generativeai is required for Gemini provider. "
                "Install with: pip install google-generativeai"
            )
    return genai


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM Provider.
    
    Supports:
    - gemini-1.5-flash (fast, cheap)
    - gemini-1.5-pro (powerful)
    - gemini-2.0-flash-exp (experimental, very fast)
    """
    
    # Default models
    MODELS = {
        "flash": "gemini-1.5-flash",
        "pro": "gemini-1.5-pro", 
        "flash-2": "gemini-2.0-flash-exp",
    }
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 256,
        **kwargs
    ):
        # Handle shorthand model names
        if model_name in self.MODELS:
            model_name = self.MODELS[model_name]
            
        super().__init__(model_name, **kwargs)
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        if not self.api_key:
            logger.warning("gemini_no_api_key", message="GOOGLE_API_KEY not set")
            self._initialized = False
            return
        
        # Initialize Gemini
        _genai = _ensure_genai()
        _genai.configure(api_key=self.api_key)
        
        # Create model instance
        self.generation_config = _genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        self.model = _genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
        
        self._initialized = True
        logger.info(
            "gemini_provider_initialized",
            model=self.model_name,
            temperature=temperature
        )
    
    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.GEMINI
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Synchronous generation using Gemini"""
        if not self._initialized:
            raise RuntimeError("Gemini provider not initialized. Check API key.")
        
        start_time = time.time()
        
        try:
            # Generate response
            response = self.model.generate_content(prompt)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract text
            text = response.text if hasattr(response, 'text') else str(response)
            
            # Get token counts if available
            input_tokens = self.count_tokens(prompt)
            output_tokens = self.count_tokens(text)
            
            # Try to get actual token counts from response
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
            
            return LLMResponse(
                text=text,
                provider=self.provider_type.value,
                model=self.model_name,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "unknown",
                metadata={"temperature": self.temperature}
            )
            
        except Exception as e:
            logger.error("gemini_generate_error", error=str(e))
            raise
    
    async def generate_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Asynchronous generation using Gemini"""
        if not self._initialized:
            raise RuntimeError("Gemini provider not initialized. Check API key.")
        
        start_time = time.time()
        
        try:
            # Use async generation
            response = await self.model.generate_content_async(prompt)
            
            latency_ms = (time.time() - start_time) * 1000
            
            text = response.text if hasattr(response, 'text') else str(response)
            
            input_tokens = self.count_tokens(prompt)
            output_tokens = self.count_tokens(text)
            
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                if hasattr(usage, 'prompt_token_count'):
                    input_tokens = usage.prompt_token_count
                if hasattr(usage, 'candidates_token_count'):
                    output_tokens = usage.candidates_token_count
            
            return LLMResponse(
                text=text,
                provider=self.provider_type.value,
                model=self.model_name,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "unknown",
                metadata={"temperature": self.temperature}
            )
            
        except Exception as e:
            logger.error("gemini_async_error", error=str(e))
            raise
    
    async def generate_stream(
        self, 
        prompt: str, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        True streaming generation using Gemini's streaming API.
        """
        if not self._initialized:
            raise RuntimeError("Gemini provider not initialized. Check API key.")
        
        try:
            # Use streaming generation
            response = await self.model.generate_content_async(
                prompt,
                stream=True
            )
            
            async for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            logger.error("gemini_stream_error", error=str(e))
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check Gemini API connectivity"""
        if not self._initialized:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "model": self.model_name,
                "error": "Not initialized - check GOOGLE_API_KEY"
            }
        
        try:
            start = time.time()
            response = self.model.generate_content("Hi")
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "provider": "gemini",
                "model": self.model_name,
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "model": self.model_name,
                "error": str(e)
            }
