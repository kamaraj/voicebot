"""
LLM Provider Factory
=====================
Factory for creating and managing LLM providers.

Usage:
    from src.llm import get_llm_provider
    
    # Use default from settings
    llm = get_llm_provider()
    
    # Specify provider
    llm = get_llm_provider("gemini")
    
    # With custom model
    llm = get_llm_provider("ollama", model="llama3.1:8b")
    
    # Generate response
    response = await llm.generate_async("Hello!")
    print(response.text)
"""

import os
from typing import Optional, Dict, Any, List

from src.llm.base import LLMProvider, LLMProviderType
from src.config.settings import settings
import structlog

logger = structlog.get_logger(__name__)


# Provider registry
_providers: Dict[str, type] = {}
_active_provider: Optional[LLMProvider] = None


def register_provider(name: str, provider_class: type):
    """Register a new provider type"""
    _providers[name.lower()] = provider_class
    logger.debug("provider_registered", name=name)


def _register_default_providers():
    """Register all default providers"""
    global _providers
    
    # Ollama (always available)
    from src.llm.ollama_provider import OllamaProvider
    _providers["ollama"] = OllamaProvider
    
    # Gemini (requires google-generativeai)
    try:
        from src.llm.gemini_provider import GeminiProvider
        _providers["gemini"] = GeminiProvider
    except ImportError:
        logger.debug("gemini_provider_unavailable", reason="google-generativeai not installed")
    
    # OpenAI/Groq (requires openai)
    try:
        from src.llm.openai_provider import OpenAIProvider, GroqProvider
        _providers["openai"] = OpenAIProvider
        _providers["groq"] = GroqProvider
    except ImportError:
        logger.debug("openai_provider_unavailable", reason="openai not installed")


def list_available_providers() -> List[str]:
    """List all available provider types"""
    if not _providers:
        _register_default_providers()
    return list(_providers.keys())


def get_llm_provider(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get or create an LLM provider instance.
    
    Args:
        provider: Provider type ("ollama", "gemini", "openai", "groq")
                  If None, uses LLM_PROVIDER env var or defaults to "ollama"
        model: Model name (provider-specific)
               If None, uses defaults for the provider
        **kwargs: Additional provider-specific configuration
        
    Returns:
        LLMProvider instance
        
    Examples:
        # Default (Ollama)
        llm = get_llm_provider()
        
        # Gemini
        llm = get_llm_provider("gemini", model="gemini-1.5-flash")
        
        # Groq (ultra-fast)
        llm = get_llm_provider("groq", model="llama-3.1-8b-instant")
    """
    global _active_provider
    
    # Ensure providers are registered
    if not _providers:
        _register_default_providers()
    
    # Determine provider type
    provider_name = (
        provider or 
        os.getenv("LLM_PROVIDER") or 
        "ollama"
    ).lower()
    
    # Check if provider is available
    if provider_name not in _providers:
        available = list(_providers.keys())
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {available}"
        )
    
    # Get provider class
    provider_class = _providers[provider_name]
    
    # Build kwargs
    provider_kwargs = {**kwargs}
    if model:
        provider_kwargs["model_name"] = model
    
    # Explicitly inject API keys from settings if not provided
    # This fixes issues where os.getenv doesn't see keys loaded by pydantic
    if provider_name == "groq" and not provider_kwargs.get("api_key"):
        if settings.groq_api_key:
            provider_kwargs["api_key"] = settings.groq_api_key
            
    elif provider_name == "openai" and not provider_kwargs.get("api_key"):
        if settings.openai_api_key:
            provider_kwargs["api_key"] = settings.openai_api_key
            
    elif provider_name == "gemini" and not provider_kwargs.get("api_key"):
        if settings.google_api_key:
            provider_kwargs["api_key"] = settings.google_api_key

    # Create provider instance
    try:
        # Debug logging
        if "api_key" in provider_kwargs:
            masked_key = provider_kwargs["api_key"][:4] + "..." if provider_kwargs["api_key"] else "None"
            logger.info("injecting_api_key", provider=provider_name, key_prefix=masked_key)
            print(f"DEBUG: Injecting API key for {provider_name}: {masked_key}")
        else:
            logger.info("no_api_key_in_kwargs", provider=provider_name)
            print(f"DEBUG: No API key provided for {provider_name}")

        instance = provider_class(**provider_kwargs)
        logger.info(
            "llm_provider_created",
            provider=provider_name,
            model=instance.model_name
        )
        return instance
        
    except Exception as e:
        logger.error(
            "llm_provider_creation_failed",
            provider=provider_name,
            error=str(e)
        )
        raise


def get_default_provider() -> LLMProvider:
    """
    Get the default LLM provider based on settings.
    
    Priority:
    1. LLM_PROVIDER env var
    2. GOOGLE_API_KEY set -> Gemini
    3. GROQ_API_KEY set -> Groq
    4. OPENAI_API_KEY set -> OpenAI
    5. Ollama (local, always available)
    """
    global _active_provider
    
    if _active_provider is not None:
        return _active_provider
    
    # Check env var first
    provider = os.getenv("LLM_PROVIDER")
    if provider:
        _active_provider = get_llm_provider(provider)
        return _active_provider
    
    # Auto-detect based on API keys
    if os.getenv("GOOGLE_API_KEY"):
        try:
            _active_provider = get_llm_provider("gemini")
            return _active_provider
        except Exception:
            pass
    
    if os.getenv("GROQ_API_KEY"):
        try:
            _active_provider = get_llm_provider("groq")
            return _active_provider
        except Exception:
            pass
    
    if os.getenv("OPENAI_API_KEY"):
        try:
            _active_provider = get_llm_provider("openai")
            return _active_provider
        except Exception:
            pass
    
    # Default to Ollama
    _active_provider = get_llm_provider("ollama")
    return _active_provider


def set_default_provider(provider: LLMProvider):
    """Set the default provider instance"""
    global _active_provider
    _active_provider = provider
    logger.info("default_provider_set", provider=provider.name)


def reset_provider():
    """Reset the active provider (forces re-creation on next call)"""
    global _active_provider
    _active_provider = None


# Auto-register providers on import
_register_default_providers()
