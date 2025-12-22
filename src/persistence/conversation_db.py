"""
Persistent Conversation Memory with SQLite Backend
Hybrid approach: In-memory cache + database persistence
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
import structlog

from src.database import get_database_manager, Conversation

logger = structlog.get_logger(__name__)


class PersistentConversationMemory:
    """
    Hybrid conversation memory with SQLite persistence.
    
    Features:
    - In-memory cache for fast access
    - Automatic database persistence
    - Survives restarts
    - Thread-safe operations
    - Bounded memory usage
    """
    
    def __init__(
        self, 
        max_messages: int = 10, 
        conversation_ttl_hours: int = 24,
        max_conversations: int = 1000,
        use_database: bool = True
    ):
        """
        Initialize persistent conversation memory.
        
        Args:
            max_messages: Max messages to keep per conversation in memory
            conversation_ttl_hours: Hours before conversation expires
            max_conversations: Maximum number of concurrent conversations in memory
            use_database: Whether to persist to database (default: True)
        """
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.max_messages = max_messages
        self.max_conversations = max_conversations
        self.ttl = timedelta(hours=conversation_ttl_hours)
        self.use_database = use_database
        self._lock = Lock()
        
        # Database manager
        if self.use_database:
            self.db_manager = get_database_manager()
        
        logger.info("persistent_memory_initialized",
                   max_messages=max_messages,
                   ttl_hours=conversation_ttl_hours,
                   max_conversations=max_conversations,
                   persistent=use_database,
                   thread_safe=True)
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        user_id: Optional[str] = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        duration_ms: float = 0
    ):
        """
        Add message to conversation (persists to database).
        
        Args:
            conversation_id: Conversation identifier
            role: 'user' or 'assistant'
            content: Message content
            user_id: Optional user identifier
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            duration_ms: Processing duration in milliseconds
        """
        with self._lock:
            # Enforce conversation limit in memory
            if conversation_id not in self.conversations:
                while len(self.conversations) >= self.max_conversations:
                    self._evict_oldest_conversation_unsafe()
                
                self.conversations[conversation_id] = {
                    'messages': deque(maxlen=self.max_messages),
                    'created_at': datetime.utcnow(),
                    'last_updated': datetime.utcnow(),
                    'message_count': 0
                }
            
            conv = self.conversations[conversation_id]
            message_index = conv['message_count']
            
            # Add to in-memory cache
            conv['messages'].append({
                'role': role,
                'content': content,
                'timestamp': datetime.utcnow(),
                'message_index': message_index
            })
            
            conv['last_updated'] = datetime.utcnow()
            conv['message_count'] += 1
            
            logger.debug("message_added_memory",
                        conversation_id=conversation_id,
                        role=role,
                        message_index=message_index)
        
        # Persist to database (outside lock for performance)
        if self.use_database:
            self._persist_message(
                conversation_id=conversation_id,
                role=role,
                content=content,
                user_id=user_id,
                message_index=message_index,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                duration_ms=duration_ms
            )
    
    def _persist_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        user_id: Optional[str],
        message_index: int,
        tokens_input: int,
        tokens_output: int,
        duration_ms: float
    ):
        """Persist message to database"""
        try:
            with self.db_manager.get_session() as session:
                message = Conversation(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    user_id=user_id,
                    message_index=message_index,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    duration_ms=duration_ms
                )
                session.add(message)
                
            logger.debug("message_persisted",
                        conversation_id=conversation_id,
                        message_index=message_index)
        except Exception as e:
            logger.error("failed_to_persist_message",
                        conversation_id=conversation_id,
                        error=str(e))
            # Don't fail the request if persistence fails
    
    def get_history(
        self, 
        conversation_id: str, 
        max_messages: int = None,
        from_database: bool = False
    ) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation identifier
            max_messages: Optional limit on messages to return
            from_database: Force load from database (default: use memory)
        
        Returns:
            List of messages in format [{'role': 'user', 'content': '...'}, ...]
        """
        if from_database and self.use_database:
            return self._load_from_database(conversation_id, max_messages)
        
        with self._lock:
            if conversation_id not in self.conversations:
                # Try loading from database
                if self.use_database:
                    return self._load_from_database(conversation_id, max_messages)
                return []
            
            conv = self.conversations[conversation_id]
            messages = list(conv['messages'])
            
            # Limit if requested
            if max_messages:
                messages = messages[-max_messages:]
            
            # Format for LLM (remove timestamps and index)
            return [
                {'role': msg['role'], 'content': msg['content']}
                for msg in messages
            ]
    
    def _load_from_database(
        self, 
        conversation_id: str, 
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Load conversation history from database"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Conversation)\
                    .filter(Conversation.conversation_id == conversation_id)\
                    .order_by(Conversation.message_index)
                
                if max_messages:
                    # Get last N messages
                    total = query.count()
                    if total > max_messages:
                        query = query.offset(total - max_messages)
                
                messages = query.all()
                
                logger.debug("loaded_from_database",
                            conversation_id=conversation_id,
                            count=len(messages))
                
                return [
                    {'role': msg.role, 'content': msg.content}
                    for msg in messages
                ]
        except Exception as e:
            logger.error("failed_to_load_from_database",
                        conversation_id=conversation_id,
                        error=str(e))
            return []
    
    def get_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Get formatted conversation context for LLM prompt (thread-safe)"""
        history = self.get_history(conversation_id, max_messages)
        
        if not history:
            return ""
        
        # Format as conversation
        context_lines = []
        for msg in history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def clear_conversation(self, conversation_id: str, from_database: bool = False):
        """Clear a specific conversation (thread-safe)"""
        with self._lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]
                logger.info("conversation_cleared_memory", 
                           conversation_id=conversation_id)
        
        # Also clear from database if requested
        if from_database and self.use_database:
            try:
                with self.db_manager.get_session() as session:
                    count = session.query(Conversation)\
                        .filter(Conversation.conversation_id == conversation_id)\
                        .delete()
                    logger.info("conversation_cleared_database",
                               conversation_id=conversation_id,
                               messages_deleted=count)
            except Exception as e:
                logger.error("failed_to_clear_from_database",
                            conversation_id=conversation_id,
                            error=str(e))
    
    def _evict_oldest_conversation_unsafe(self):
        """Evict oldest conversation from memory (MUST be called within lock!)"""
        if not self.conversations:
            return
        
        oldest_id = min(
            self.conversations.keys(),
            key=lambda k: self.conversations[k]['created_at']
        )
        del self.conversations[oldest_id]
        logger.debug("conversation_evicted_memory", conversation_id=oldest_id)
    
    def cleanup_expired(self):
        """Remove expired conversations from memory (thread-safe)"""
        with self._lock:
            now = datetime.utcnow()
            expired_ids = []
            
            for conv_id, conv_data in self.conversations.items():
                if now - conv_data['last_updated'] > self.ttl:
                    expired_ids.append(conv_id)
            
            for conv_id in expired_ids:
                del self.conversations[conv_id]
            
            if expired_ids:
                logger.info("conversations_expired_memory", count=len(expired_ids))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics (thread-safe)"""
        with self._lock:
            total_messages = sum(
                len(conv['messages'])
                for conv in self.conversations.values()
            )
            
            stats = {
                "active_conversations_memory": len(self.conversations),
                "total_messages_memory": total_messages,
                "max_messages_per_conversation": self.max_messages,
                "max_conversations": self.max_conversations,
                "ttl_hours": self.ttl.total_seconds() / 3600,
                "thread_safe": True,
                "persistent": self.use_database
            }
        
        # Add database stats if available
        if self.use_database:
            try:
                with self.db_manager.get_session() as session:
                    total_db_conversations = session.query(Conversation.conversation_id)\
                        .distinct().count()
                    total_db_messages = session.query(Conversation).count()
                    
                    stats["total_conversations_database"] = total_db_conversations
                    stats["total_messages_database"] = total_db_messages
            except Exception as e:
                logger.error("failed_to_get_db_stats", error=str(e))
        
        return stats


# Global singleton instance
_persistent_memory_instance = None

def get_persistent_conversation_memory() -> PersistentConversationMemory:
    """Get or create persistent memory singleton"""
    global _persistent_memory_instance
    if _persistent_memory_instance is None:
        _persistent_memory_instance = PersistentConversationMemory(
            max_messages=10,
            conversation_ttl_hours=24,
            max_conversations=1000,
            use_database=True  # Enable persistence
        )
    return _persistent_memory_instance
