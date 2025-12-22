"""
Ollama LLM Provider
====================
Local LLM provider using Ollama.

Features:
- Local inference (no API costs)
- Supports all Ollama models
- Connection pooling
- Streaming support
"""

import asyncio
import time
from typing import Dict, Any, AsyncGenerator

from langchain_community.llms import Ollama

from src.llm.base import LLMProvider, LLMProviderType, LLMResponse
from src.config.settings import settings
import structlog

logger = structlog.get_logger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama LLM Provider for local inference.
    
    Uses Ollama running locally for fast, free inference.
    Supports models like: llama3.1, tinyllama, mistral, etc.
    """
    
    def __init__(
        self, 
        model_name: str = None,
        base_url: str = None,
        timeout: int = 30,
        num_ctx: int = 2048,
        num_predict: int = 256,
        **kwargs
    ):
        model_name = model_name or settings.ollama_model
        super().__init__(model_name, **kwargs)
        
        self.base_url = base_url or settings.ollama_base_url
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.num_predict = num_predict
        
        # Initialize Ollama client
        self.client = Ollama(
            model=self.model_name,
            base_url=self.base_url,
            timeout=timeout,
            num_ctx=num_ctx,
            num_predict=num_predict,
        )
        
        self._initialized = True
        logger.info(
            "ollama_provider_initialized",
            model=self.model_name,
            base_url=self.base_url
        )
    
    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.OLLAMA
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Synchronous generation using Ollama"""
        start_time = time.time()
        
        try:
            # Override defaults with kwargs
            response = self.client.invoke(prompt)
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate tokens
            input_tokens = self.count_tokens(prompt)
            output_tokens = self.count_tokens(response)
            
            return LLMResponse(
                text=response,
                provider=self.provider_type.value,
                model=self.model_name,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                finish_reason="stop",
                metadata={"base_url": self.base_url}
            )
            
        except Exception as e:
            logger.error("ollama_generate_error", error=str(e))
            raise
    
    async def generate_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Asynchronous generation using Ollama"""
        # Ollama LangChain doesn't have native async, use thread pool
        return await asyncio.to_thread(self.generate, prompt, **kwargs)
    
    async def generate_stream(
        self, 
        prompt: str, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streaming generation (simulated for Ollama LangChain).
        
        Note: For true streaming, use Ollama's native API directly.
        """
        # For now, fall back to non-streaming
        response = await self.generate_async(prompt, **kwargs)
        
        # Simulate streaming by yielding words
        words = response.text.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)  # Small delay to simulate streaming
    
    def health_check(self) -> Dict[str, Any]:
        """Check Ollama connectivity"""
        try:
            start = time.time()
            response = self.client.invoke("Hi")
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "provider": "ollama",
                "model": self.model_name,
                "base_url": self.base_url,
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "ollama",
                "model": self.model_name,
                "error": str(e)
            }
