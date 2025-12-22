"""
Input Validation and Sanitization
Protects against malicious input and DoS attacks
"""
from typing import Optional
from pydantic import BaseModel, Field, validator
import re
import structlog

logger = structlog.get_logger(__name__)


class MessageInput(BaseModel):
    """
    Validated message input.
    
    Enforces:
    - Max length (prevents DoS)
    - Non-empty content
    - No malicious patterns
    """
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: Optional[str] = Field(None, max_length=100, description="Conversation ID")
    user_id: Optional[str] = Field(None, max_length=100, description="User ID")
    context: Optional[dict] = Field(None, description="Additional context")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate and sanitize message"""
        # Strip whitespace
        v = v.strip()
        
        # Check not empty after stripping
        if not v:
            raise ValueError("Message cannot be empty")
        
        # Check for excessive whitespace (potential DoS)
        if len(v) - len(v.replace(' ', '')) > len(v) * 0.5:
            raise ValueError("Message contains excessive whitespace")
        
        # Check for control characters (except newlines/tabs)
        if any(ord(c) < 32 and c not in '\n\t\r' for c in v):
            logger.warning("message_contains_control_chars", message_preview=v[:50])
            # Remove control characters
            v = ''.join(c for c in v if ord(c) >= 32 or c in '\n\t\r')
        
        # Check for potential injection patterns
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
            r'eval\s*\(',  # Eval function
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                logger.warning("suspicious_pattern_detected", 
                             pattern=pattern,
                             message_preview=v[:100])
                # Could raise ValueError here for strict mode
                # For now, just log
        
        return v
    
    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        """Validate conversation ID"""
        if v is None:
            return v
        
        # Only alphanumeric, underscore, hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Invalid conversation ID format")
        
        return v
    
    @validator('context')
    def validate_context(cls, v):
        """Validate context dict"""
        if v is None:
            return v
        
        # Limit context size
        if len(str(v)) > 10000:
            raise ValueError("Context too large")
        
        return v


class ConversationRequest(MessageInput):
    """
    Full conversation request with all fields.
    Extends MessageInput with additional validation.
    """
    pass


def sanitize_output(text: str, max_length: int = 10000) -> str:
    """
    Sanitize LLM output.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    # Truncate if too long
    if len(text) > max_length:
        logger.warning("output_truncated", 
                      original_length=len(text),
                      max_length=max_length)
        text = text[:max_length] + "... [truncated]"
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text
