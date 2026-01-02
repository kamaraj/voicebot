"""
Semantic Response Cache for VoiceBot SaaS.
Caches responses based on semantic similarity, not exact matches.
Ensures consistent answers for semantically similar questions.
"""
from typing import Dict, Any, Optional, List
import time
import json
import hashlib
from pathlib import Path


class SemanticResponseCache:
    """
    Cache responses based on semantic similarity.
    
    How it works:
    1. When a new question comes in, check if a semantically similar question was asked before
    2. If similarity > threshold, return the cached response
    3. If not, generate new response and cache it with its embedding
    
    This ensures:
    - "What is your discipline policy?" 
    - "How do you handle bad behavior?"
    - "What happens if my kid misbehaves?"
    
    All return the SAME cached response once the first one is answered.
    """
    
    def __init__(
        self, 
        similarity_threshold: float = 0.85,
        max_cache_size: int = 1000,
        cache_file: str = None
    ):
        """
        Initialize semantic cache.
        
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider a cache hit
            max_cache_size: Maximum number of cached responses
            cache_file: Optional file to persist cache
        """
        self.similarity_threshold = similarity_threshold
        self.max_cache_size = max_cache_size
        self.cache_file = cache_file or "data/semantic_cache.json"
        
        # Cache structure: list of {embedding, question, response, metadata, timestamp}
        self.cache: List[Dict] = []
        
        # Embedding function (will be set externally)
        self._embed_fn = None
        
        # Load existing cache
        self._load_cache()
    
    def set_embedding_function(self, embed_fn):
        """
        Set the embedding function to use.
        
        Args:
            embed_fn: Function that takes text and returns embedding vector
        """
        self._embed_fn = embed_fn
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self._embed_fn:
            return self._embed_fn(text)
        else:
            # Fallback: simple hash-based pseudo-embedding
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """
        Simple hash-based pseudo-embedding for queries.
        Good enough for caching similar questions.
        """
        import math
        from collections import Counter
        import re
        
        # Normalize text
        text = text.lower().strip()
        words = re.findall(r'\b\w+\b', text)
        
        # Remove common words
        stop_words = {'what', 'is', 'your', 'how', 'do', 'you', 'the', 'a', 'an', 'to', 'for', 
                      'can', 'could', 'please', 'i', 'my', 'me', 'we', 'our', 'if', 'when',
                      'where', 'why', 'which', 'who', 'that', 'this', 'are', 'be', 'been',
                      'have', 'has', 'had', 'will', 'would', 'should', 'about', 'with'}
        
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Create embedding from word hashes
        embedding = [0.0] * dim
        
        for word in meaningful_words:
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for i in range(3):
                pos = (word_hash + i * 127) % dim
                embedding[pos] += 1.0 * (1 if word_hash % 2 == 0 else -1)
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    def get(self, question: str) -> Optional[Dict]:
        """
        Check if a semantically similar question has a cached response.
        
        Args:
            question: The user's question
            
        Returns:
            Cached response dict if found, None otherwise
        """
        if not self.cache:
            return None
        
        # Get embedding for the question
        query_embedding = self._get_embedding(question)
        
        # Find most similar cached question
        best_match = None
        best_similarity = 0.0
        
        for entry in self.cache:
            cached_embedding = entry.get("embedding", [])
            if not cached_embedding:
                continue
            
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry
        
        # Return if above threshold
        if best_match and best_similarity >= self.similarity_threshold:
            return {
                "response": best_match["response"],
                "original_question": best_match["question"],
                "similarity": best_similarity,
                "cache_hit": True,
                "metadata": best_match.get("metadata", {})
            }
        
        return None
    
    def set(self, question: str, response: str, metadata: Dict = None) -> None:
        """
        Cache a response for a question.
        
        Args:
            question: The question asked
            response: The response generated
            metadata: Optional metadata to store
        """
        # Get embedding
        embedding = self._get_embedding(question)
        
        # Check if similar question already cached (avoid duplicates)
        for entry in self.cache:
            cached_embedding = entry.get("embedding", [])
            if cached_embedding:
                similarity = self._cosine_similarity(embedding, cached_embedding)
                if similarity >= self.similarity_threshold:
                    # Update existing entry instead of adding new
                    entry["response"] = response
                    entry["timestamp"] = time.time()
                    entry["metadata"] = metadata or {}
                    self._save_cache()
                    return
        
        # Add new entry
        self.cache.append({
            "question": question,
            "embedding": embedding,
            "response": response,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
        
        # Evict oldest if over max size
        if len(self.cache) > self.max_cache_size:
            self.cache.sort(key=lambda x: x.get("timestamp", 0))
            self.cache = self.cache[-self.max_cache_size:]
        
        # Persist
        self._save_cache()
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache = []
        self._save_cache()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_cache_size,
            "similarity_threshold": self.similarity_threshold,
            "oldest_entry": min((e.get("timestamp", 0) for e in self.cache), default=0),
            "newest_entry": max((e.get("timestamp", 0) for e in self.cache), default=0)
        }
    
    def _load_cache(self) -> None:
        """Load cache from file."""
        cache_path = Path(self.cache_file)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get("entries", [])
            except Exception as e:
                print(f"Error loading semantic cache: {e}")
                self.cache = []
    
    def _save_cache(self) -> None:
        """Save cache to file."""
        cache_path = Path(self.cache_file)
        cache_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": "1.0",
                    "similarity_threshold": self.similarity_threshold,
                    "entries": self.cache
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving semantic cache: {e}")


# Singleton instance
_semantic_cache: Optional[SemanticResponseCache] = None


def get_semantic_cache(similarity_threshold: float = 0.85) -> SemanticResponseCache:
    """Get or create the semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticResponseCache(similarity_threshold=similarity_threshold)
    return _semantic_cache
