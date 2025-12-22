"""
Conversation Memory Manager
Maintains conversation history for context-aware responses
Thread-safe implementation with proper limits
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
import structlog

logger = structlog.get_logger(__name__)


class ConversationMemory:
    """
    Thread-safe conversation history manager with sliding window.
    
    Features:
    - Maintains last N messages
    - Automatic cleanup of old conversations
    - Context formatting for LLM
    - Thread-safe operations
    - Bounded memory usage
    """
    
    def __init__(
        self, 
        max_messages: int = 10, 
        conversation_ttl_hours: int = 24,
        max_conversations: int = 1000
    ):
        """
        Initialize conversation memory.
        
        Args:
            max_messages: Max messages to keep per conversation
            conversation_ttl_hours: Hours before conversation expires
            max_conversations: Maximum number of concurrent conversations
        """
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.max_messages = max_messages
        self.max_conversations = max_conversations
        self.ttl = timedelta(hours=conversation_ttl_hours)
        self._lock = Lock()  # Thread safety
        
        logger.info("memory_initialized",
                   max_messages=max_messages,
                   ttl_hours=conversation_ttl_hours,
                   max_conversations=max_conversations,
                   thread_safe=True)
    
    def add_message(self, conversation_id: str, role: str, content: str):
        """
        Add a message to conversation history (thread-safe).
        
        Args:
            conversation_id: Conversation identifier
            role: 'user' or 'assistant'
            content: Message content
        """
        with self._lock:  # Thread-safe access
            # Enforce conversation limit
            if conversation_id not in self.conversations:
                while len(self.conversations) >= self.max_conversations:
                    self._evict_oldest_conversation_unsafe()
                
                self.conversations[conversation_id] = {
                    'messages': deque(maxlen=self.max_messages),
                    'created_at': datetime.now(),
                    'last_updated': datetime.now()
                }
            
            conv = self.conversations[conversation_id]
            
            # Add message
            conv['messages'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now()
            })
            
            conv['last_updated'] = datetime.now()
            
            logger.debug("message_added",
                        conversation_id=conversation_id,
                        role=role,
                        message_count=len(conv['messages']))
    
    def get_history(self, conversation_id: str, max_messages: int = None) -> List[Dict[str, str]]:
        """
        Get conversation history (thread-safe).
        
        Args:
            conversation_id: Conversation identifier
            max_messages: Optional limit on messages to return
        
        Returns:
            List of messages in format [{'role': 'user', 'content': '...'}, ...]
        """
        with self._lock:
            if conversation_id not in self.conversations:
                return []
            
            conv = self.conversations[conversation_id]
            messages = list(conv['messages'])
            
            # Limit if requested
            if max_messages:
                messages = messages[-max_messages:]
            
            # Format for LLM (remove timestamps)
            return [
                {'role': msg['role'], 'content': msg['content']}
                for msg in messages
            ]
    
    def get_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """
        Get formatted conversation context for LLM prompt.
        
        Args:
            conversation_id: Conversation identifier
            max_messages: Number of recent messages to include
        
        Returns:
            Formatted conversation history
        """
        history = self.get_history(conversation_id, max_messages)
        
        if not history:
            return ""
        
        # Format as conversation
        context_lines = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def clear_conversation(self, conversation_id: str):
        """Clear a specific conversation (thread-safe)"""
        with self._lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                logger.info("conversation_cleared", conversation_id=conversation_id)
    
    def _evict_oldest_conversation_unsafe(self):
        """Evict oldest conversation (MUST be called within lock!)"""
        if not self.conversations:
            return
        
        oldest_id = min(
            self.conversations.keys(),
            key=lambda k: self.conversations[k]['created_at']
        )
        del self.conversations[oldest_id]
        logger.debug("conversation_evicted", conversation_id=oldest_id)
    
    def cleanup_expired(self):
        """Remove expired conversations (thread-safe)"""
        with self._lock:
            now = datetime.now()
            expired_ids = []
            
            for conv_id, conv_data in self.conversations.items():
                if now - conv_data['last_updated'] > self.ttl:
                    expired_ids.append(conv_id)
            
            for conv_id in expired_ids:
                del self.conversations[conv_id]
            
            if expired_ids:
                logger.info("conversations_expired", count=len(expired_ids))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics (thread-safe)"""
        with self._lock:
            total_messages = sum(
                len(conv['messages'])
                for conv in self.conversations.values()
            )
            
            return {
                "active_conversations": len(self.conversations),
                "total_messages": total_messages,
                "max_messages_per_conversation": self.max_messages,
                "max_conversations": self.max_conversations,
                "ttl_hours": self.ttl.total_seconds() / 3600,
                "thread_safe": True
            }


# Global singleton instance
_memory_instance = None

def get_conversation_memory() -> ConversationMemory:
    """Get or create memory singleton"""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory(max_messages=10, conversation_ttl_hours=24)
    return _memory_instance
