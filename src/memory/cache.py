"""
Response Caching Layer
Caches LLM responses to avoid redundant API calls
Thread-safe implementation with proper locking
"""
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from threading import Lock
import structlog

logger = structlog.get_logger(__name__)


class ResponseCache:
    """
    Thread-safe in-memory cache for LLM responses.
    
    Benefits:
    - Instant responses for repeated queries (~1ms vs 300-500ms)
    - Reduced LLM load
    - Better user experience
    - Thread-safe operations
    """
    
    def __init__(self, ttl_minutes: int = 60, max_size: int = 1000):
        """
        Initialize cache.
        
        Args:
            ttl_minutes: Time-to-live for cache entries
            max_size: Maximum number of entries
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._lock = Lock()  # Thread safety
        
        logger.info("cache_initialized", 
                   ttl_minutes=ttl_minutes,
                   max_size=max_size,
                   thread_safe=True)
    
    def _generate_key(self, query: str, context: Dict = None) -> str:
        """Generate cache key from query and context"""
        # Normalize query
        normalized = query.lower().strip()
        
        # Include context in key if provided
        if context:
            cache_data = {
                "query": normalized,
                "context": context
            }
        else:
            cache_data = {"query": normalized}
        
        # Hash to create key
        key = hashlib.md5(
            json.dumps(cache_data, sort_keys=True).encode()
        ).hexdigest()
        
        return key
    
    def get(self, query: str, context: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired (thread-safe).
        
        Args:
            query: User query
            context: Optional context for cache key
        
        Returns:
            Cached response or None
        """
        key = self._generate_key(query, context)
        
        with self._lock:  # Thread-safe access
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if datetime.now() - entry['timestamp'] < self.ttl:
                    self.hits += 1
                    logger.debug("cache_hit", 
                               query=query[:50],
                               age_seconds=(datetime.now() - entry['timestamp']).total_seconds())
                    return entry['response']
                else:
                    # Expired - remove
                    del self.cache[key]
                    logger.debug("cache_expired", query=query[:50])
            
            self.misses += 1
            return None
    
    def set(self, query: str, response: Dict[str, Any], context: Dict = None):
        """
        Cache a response (thread-safe with proper eviction).
        
        Args:
            query: User query
            response: LLM response to cache
            context: Optional context for cache key
        """
        key = self._generate_key(query, context)
        
        with self._lock:  # Thread-safe access
            # Evict BEFORE adding if at capacity (prevents race condition)
            while len(self.cache) >= self.max_size:
                self._evict_oldest_unsafe()  # Already inside lock
            
            self.cache[key] = {
                'response': response,
                'timestamp': datetime.now(),
                'query': query[:100]  # Store for debugging
            }
            
            logger.debug("cache_set", 
                        query=query[:50],
                        cache_size=len(self.cache))
    
    def _evict_oldest_unsafe(self):
        """Evict the oldest cache entry (MUST be called within lock!)"""
        if not self.cache:
            return
        
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['timestamp']
        )
        del self.cache[oldest_key]
        logger.debug("cache_evicted", key=oldest_key)
    
    def _evict_oldest(self):
        """Evict the oldest cache entry (thread-safe)"""
        with self._lock:
            self._evict_oldest_unsafe()
    
    def clear(self):
        """Clear all cache entries (thread-safe)"""
        with self._lock:
            self.cache.clear()
        logger.info("cache_cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics (thread-safe)"""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "ttl_minutes": self.ttl.total_seconds() / 60,
                "thread_safe": True
            }


# Global singleton instance
_cache_instance = None

def get_response_cache() -> ResponseCache:
    """Get or create cache singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache(ttl_minutes=60, max_size=1000)
    return _cache_instance
