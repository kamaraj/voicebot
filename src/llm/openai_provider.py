"""
OpenAI-Compatible LLM Provider
===============================
Provider for OpenAI API and OpenAI-compatible endpoints.

Supports:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Groq (Llama, Mixtral - ultra fast!)
- Azure OpenAI
- Any OpenAI-compatible API (Ollama, LocalAI, etc.)

Requirements:
    pip install openai

Environment:
    OPENAI_API_KEY=your_api_key
    GROQ_API_KEY=your_groq_key (for Groq)
"""

import asyncio
import time
import os
from typing import Dict, Any, AsyncGenerator, Optional

from src.llm.base import LLMProvider, LLMProviderType, LLMResponse
import structlog

logger = structlog.get_logger(__name__)

# Lazy import
openai_client = None


def _ensure_openai():
    """Lazy load openai"""
    global openai_client
    if openai_client is None:
        try:
            from openai import OpenAI, AsyncOpenAI
            return OpenAI, AsyncOpenAI
        except ImportError:
            raise ImportError(
                "openai is required for this provider. "
                "Install with: pip install openai"
            )
    return openai_client


class OpenAIProvider(LLMProvider):
    """
    OpenAI and OpenAI-compatible LLM Provider.
    
    Works with:
    - OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
    - Groq: llama-3.1-70b-versatile, mixtral-8x7b-32768
    - Any OpenAI-compatible API
    """
    
    # Common model shortcuts
    MODELS = {
        # OpenAI
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4": "gpt-4-turbo-preview",
        "gpt-3.5": "gpt-3.5-turbo",
        # Groq shortcuts
        "groq-llama": "llama-3.1-70b-versatile",
        "groq-llama-8b": "llama-3.1-8b-instant",
        "groq-mixtral": "mixtral-8x7b-32768",
    }
    
    # Preset configurations for different providers
    PRESETS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "default_model": "gpt-4o-mini"
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "api_key_env": "GROQ_API_KEY",
            "default_model": "llama-3.1-8b-instant"
        },
        "together": {
            "base_url": "https://api.together.xyz/v1",
            "api_key_env": "TOGETHER_API_KEY",
            "default_model": "meta-llama/Llama-3-70b-chat-hf"
        }
    }
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        preset: Optional[str] = None,  # "openai", "groq", "together"
        temperature: float = 0.7,
        max_tokens: int = 256,
        **kwargs
    ):
        # Apply preset if specified
        if preset and preset in self.PRESETS:
            config = self.PRESETS[preset]
            base_url = base_url or config["base_url"]
            api_key = api_key or os.getenv(config["api_key_env"])
            if model_name == "gpt-4o-mini":  # default not overridden
                model_name = config["default_model"]
        
        # Handle model shortcuts
        if model_name in self.MODELS:
            model_name = self.MODELS[model_name]
        
        super().__init__(model_name, **kwargs)
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or "https://api.openai.com/v1"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.preset = preset
        
        if not self.api_key:
            logger.warning("openai_no_api_key", message="API key not set")
            self._initialized = False
            return
        
        # Initialize clients
        OpenAI, AsyncOpenAI = _ensure_openai()
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self._initialized = True
        logger.info(
            "openai_provider_initialized",
            model=self.model_name,
            base_url=self.base_url,
            preset=preset
        )
    
    @property
    def provider_type(self) -> LLMProviderType:
        if self.preset == "groq":
            return LLMProviderType.GROQ
        return LLMProviderType.OPENAI
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Synchronous generation"""
        if not self._initialized:
            raise RuntimeError("Provider not initialized. Check API key.")
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            text = response.choices[0].message.content
            usage = response.usage
            
            return LLMResponse(
                text=text,
                provider=self.provider_type.value,
                model=self.model_name,
                latency_ms=latency_ms,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                finish_reason=response.choices[0].finish_reason,
                metadata={"base_url": self.base_url}
            )
            
        except Exception as e:
            logger.error("openai_generate_error", error=str(e))
            raise
    
    async def generate_async(self, prompt: str, **kwargs) -> LLMResponse:
        """Asynchronous generation"""
        if not self._initialized:
            raise RuntimeError("Provider not initialized. Check API key.")
        
        start_time = time.time()
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            text = response.choices[0].message.content
            usage = response.usage
            
            return LLMResponse(
                text=text,
                provider=self.provider_type.value,
                model=self.model_name,
                latency_ms=latency_ms,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                finish_reason=response.choices[0].finish_reason,
                metadata={"base_url": self.base_url}
            )
            
        except Exception as e:
            logger.error("openai_async_error", error=str(e))
            raise
    
    async def generate_stream(
        self, 
        prompt: str, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """True streaming generation"""
        if not self._initialized:
            raise RuntimeError("Provider not initialized. Check API key.")
        
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check API connectivity"""
        if not self._initialized:
            return {
                "status": "unhealthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "error": "Not initialized - check API key"
            }
        
        try:
            start = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "base_url": self.base_url,
                "latency_ms": round(latency, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "error": str(e)
            }


# Convenience aliases
class GroqProvider(OpenAIProvider):
    """Groq-specific provider with defaults"""
    
    def __init__(self, model_name: str = "llama-3.1-8b-instant", **kwargs):
        super().__init__(
            model_name=model_name,
            preset="groq",
            **kwargs
        )
