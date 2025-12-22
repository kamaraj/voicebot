"""
Unit tests for ResponseCache
Testing thread safety, eviction, and TTL
"""
import pytest
import time
import threading
from datetime import datetime, timedelta

from src.memory.cache import ResponseCache


@pytest.mark.unit
class TestCacheBasics:
    """Basic cache functionality tests"""
    
    def test_cache_set_and_get(self, test_cache):
        """Test basic set and get operations"""
        test_cache.set("key1", {"data": "value1"})
        result = test_cache.get("key1")
        
        assert result is not None
        assert result["data"] == "value1"
    
    def test_cache_miss(self, test_cache):
        """Test cache miss returns None"""
        result = test_cache.get("nonexistent_key")
        assert result is None
    
    def test_cache_stats(self, test_cache):
        """Test cache statistics tracking"""
        # Initial stats
        stats = test_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        
        # Add and retrieve
        test_cache.set("key1", {"data": "value1"})
        test_cache.get("key1")  # Hit
        test_cache.get("key2")  # Miss
        
        stats = test_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 50.0


@pytest.mark.unit
class TestCacheEviction:
    """Test cache eviction policies"""
    
    def test_max_size_enforcement(self):
        """Test that cache respects max_size"""
        cache = ResponseCache(ttl_minutes=60, max_size=3)
        
        # Add 4 items (should evict oldest)
        cache.set("a", {"data": "1"})
        cache.set("b", {"data": "2"})
        cache.set("c", {"data": "3"})
        cache.set("d", {"data": "4"})  # Should evict "a"
        
        assert cache.get("a") is None  # Evicted
        assert cache.get("b") is not None
        assert cache.get("c") is not None
        assert cache.get("d") is not None
        
        stats = cache.get_stats()
        assert stats["size"] == 3  # Max size enforced
    
    def test_lru_eviction_order(self):
        """Test that oldest items are evicted first"""
        cache = ResponseCache(ttl_minutes=60, max_size=2)
        
        cache.set("first", {"data": "1"})
        time.sleep(0.01)  # Ensure time difference
        cache.set("second", {"data": "2"})
        time.sleep(0.01)
        cache.set("third", {"data": "3"})  # Should evict "first"
        
        assert cache.get("first") is None
        assert cache.get("second") is not None
        assert cache.get("third") is not None


@pytest.mark.unit
class TestCacheTTL:
    """Test cache TTL expiration"""
    
    def test_ttl_expiration(self):
        """Test that items expire after TTL"""
        cache = ResponseCache(ttl_minutes=0.001, max_size=100)  # 0.06 seconds
        
        cache.set("key1", {"data": "value1"})
        
        # Should be available immediately
        assert cache.get("key1") is not None
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Should be expired
        assert cache.get("key1") is None


@pytest.mark.unit
class TestCacheThreadSafety:
    """Test cache thread safety"""
    
    def test_concurrent_writes(self, test_cache):
        """Test concurrent write operations"""
        results = []
        errors = []
        
        def write_items(start, count):
            try:
                for i in range(start, start + count):
                    test_cache.set(f"key{i}", {"data": i})
                    results.append(True)
            except Exception as e:
                errors.append(str(e))
        
        # Start 10 threads, each writing 10 items
        threads = [
            threading.Thread(target=write_items, args=(i * 10, 10))
            for i in range(10)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0
        
        # All operations should succeed
        assert len(results) == 100
        
        # Cache size should be enforced
        stats = test_cache.get_stats()
        assert stats["size"] <= test_cache.max_size
    
    def test_concurrent_read_write(self, test_cache):
        """Test concurrent read and write operations"""
        errors = []
        
        def writer():
            try:
                for i in range(50):
                    test_cache.set(f"key{i}", {"data": i})
            except Exception as e:
                errors.append(f"Write error: {str(e)}")
        
        def reader():
            try:
                for i in range(50):
                    test_cache.get(f"key{i}")
            except Exception as e:
                errors.append(f"Read error: {str(e)}")
        
        # Start mixed read/write threads
        threads = (
            [threading.Thread(target=writer) for _ in range(5)] +
            [threading.Thread(target=reader) for _ in range(5)]
        )
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0


@pytest.mark.unit
class TestCacheOperations:
    """Test cache operations"""
    
    def test_clear_cache(self, test_cache):
        """Test cache clear operation"""
        test_cache.set("key1", {"data": "value1"})
        test_cache.set("key2", {"data": "value2"})
        
        assert test_cache.get_stats()["size"] == 2
        
        test_cache.clear()
        
        assert test_cache.get_stats()["size"] == 0
        assert test_cache.get("key1") is None
        assert test_cache.get("key2") is None
    
    def test_context_aware_keys(self, test_cache):
        """Test that context affects cache keys"""
        # Same query, different context should be different cache entries
        test_cache.set("query1", {"data": "v1"}, context={"user": "alice"})
        test_cache.set("query1", {"data": "v2"}, context={"user": "bob"})
        
        # Should get different results based on context
        result1 = test_cache.get("query1", context={"user": "alice"})
        result2 = test_cache.get("query1", context={"user": "bob"})
        
        assert result1["data"] == "v1"
        assert result2["data"] == "v2"
