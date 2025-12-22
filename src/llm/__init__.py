"""
LLM Provider Module
====================
Modular LLM provider system supporting multiple backends:
- Ollama (local)
- Google Gemini
- OpenAI
- Groq
- Anthropic
- And more...

Usage:
    from src.llm import get_llm_provider
    
    llm = get_llm_provider()  # Uses default from settings
    response = await llm.generate("Hello, world!")
"""

from src.llm.base import LLMProvider, LLMResponse
from src.llm.factory import get_llm_provider, list_available_providers

__all__ = [
    "LLMProvider",
    "LLMResponse", 
    "get_llm_provider",
    "list_available_providers"
]
