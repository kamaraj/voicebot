"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation and defaults."""
    
    # Application
    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_port: int = 8000
    
    # LLM Provider Selection
    # Options: "ollama", "gemini", "openai", "groq"
    # Auto-detects if not set (checks API keys)
    llm_provider: Optional[str] = None
    
    # Ollama (Local LLM)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "tinyllama"  # Changed from llama3.1:8b for faster responses
    
    # Google Gemini
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-1.5-flash"  # Fast and cheap
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Groq (Ultra-fast cloud inference)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.1-8b-instant"
    
    # LangSmith (Tracing)
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: Optional[str] = None
    langchain_project: str = "voicebot-dev"
    
    # Voice Services
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # Telephony
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/voicebot"
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "change_this_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Guardrails
    guardrails_enabled: bool = True
    pii_detection_enabled: bool = True
    toxicity_threshold: float = 0.7
    
    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_port: int = 3000
    phoenix_enabled: bool = True
    phoenix_port: int = 6006
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    
    # Feature Flags
    enable_voice_cloning: bool = False
    enable_function_calling: bool = True
    enable_rag: bool = True
    enable_memory: bool = True
    
    # Costs & Limits
    max_tokens_per_request: int = 2000
    cost_tracking_enabled: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export singleton
settings = get_settings()
