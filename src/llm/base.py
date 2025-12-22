"""
Base LLM Provider Interface
============================
Abstract base class for all LLM providers.
Implement this interface to add new LLM backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, AsyncGenerator
from enum import Enum
import time


class LLMProviderType(Enum):
    """Supported LLM provider types"""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    CUSTOM = "custom"


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    text: str
    provider: str
    model: str
    
    # Performance metrics
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Optional metadata
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second"""
        if self.latency_ms > 0:
            return (self.output_tokens / self.latency_ms) * 1000
        return 0.0


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Implement this interface to add support for new LLM backends.
    All providers must implement:
    - generate(): Synchronous generation
    - generate_async(): Asynchronous generation
    - generate_stream(): Streaming generation
    """
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
        self._initialized = False
    
    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """Return the provider type"""
        pass
    
    @property
    def name(self) -> str:
        """Human-readable provider name"""
        return f"{self.provider_type.value}:{self.model_name}"
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Synchronous text generation.
        
        Args:
            prompt: The input prompt
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with generated text and metrics
        """
        pass
    
    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Asynchronous text generation.
        
        Args:
            prompt: The input prompt
            **kwargs: Provider-specific parameters
            
        Returns:
            LLMResponse with generated text and metrics
        """
        pass
    
    async def generate_stream(
        self, 
        prompt: str, 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streaming text generation (yields tokens as they're generated).
        
        Default implementation falls back to non-streaming.
        Override for true streaming support.
        
        Args:
            prompt: The input prompt
            **kwargs: Provider-specific parameters
            
        Yields:
            Generated text tokens
        """
        # Default: non-streaming fallback
        response = await self.generate_async(prompt, **kwargs)
        yield response.text
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            Dict with status and details
        """
        try:
            start = time.time()
            response = self.generate("Say 'OK' if you're working.", max_tokens=10)
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "latency_ms": round(latency, 2),
                "message": response.text[:50]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_type.value,
                "model": self.model_name,
                "error": str(e)
            }
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Override for accurate counting per provider.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Default: ~4 characters per token (rough estimate)
        return len(text) // 4
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model_name}>"
