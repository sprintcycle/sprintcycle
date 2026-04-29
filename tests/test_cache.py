"""SprintCycle Cache 模块测试"""
import pytest
import time
import tempfile
from pathlib import Path
import sprintcycle.cache as cache_module
from sprintcycle.cache import (
    CacheStrategy, CacheEntry, CacheStats, ResponseCache,
    get_cache, cached
)


class TestCacheStrategy:
    def test_cache_strategy_values(self):
        assert CacheStrategy.LRU.value == "lru"
        assert CacheStrategy.LFU.value == "lfu"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.FIFO.value == "fifo"


class TestCacheEntry:
    def test_cache_entry_creation(self):
        entry = CacheEntry(key="test_key", value={"data": "test"})
        assert entry.key == "test_key"
        assert entry.value == {"data": "test"}
        assert entry.access_count == 0
    
    def test_cache_entry_touch(self):
        entry = CacheEntry(key="test", value="value")
        old_accessed = entry.last_accessed
        time.sleep(0.01)
        entry.touch()
        assert entry.last_accessed >= old_accessed
        assert entry.access_count == 1


class TestCacheStats:
    def test_cache_stats_default(self):
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0
    
    def test_cache_stats_hit_rate(self):
        stats = CacheStats(hits=80, misses=20)
        assert stats.hit_rate == 0.8


class TestResponseCache:
    @pytest.fixture
    def cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def cache(self, cache_dir):
        return ResponseCache(
            cache_dir=cache_dir,
            max_size_mb=10,
            default_ttl=3600,
            strategy=CacheStrategy.LRU,
            enable_disk_persistence=False
        )
    
    def test_cache_initialization(self, cache):
        assert cache.max_size_bytes == 10 * 1024 * 1024
        assert cache.default_ttl == 3600
    
    def test_cache_set_and_get(self, cache):
        url = "https://api.example.com/test"
        data = {"result": "success"}
        cache.set(url, data)
        result = cache.get(url)
        assert result == data
    
    def test_cache_miss(self, cache):
        result = cache.get("https://nonexistent.com")
        assert result is None
    
    def test_cache_invalidate_by_url(self, cache):
        url = "https://api.example.com/data"
        cache.set(url, {"data": "value"})
        assert cache.get(url) == {"data": "value"}
        count = cache.invalidate(url=url)
        assert count == 1
    
    def test_cache_clear(self, cache):
        cache.set("https://api.example.com/1", {"data": "1"})
        cache.clear()
        assert cache.get("https://api.example.com/1") is None
    
    def test_cache_stats(self, cache):
        cache.set("https://api.example.com/test", {"data": "test"})
        cache.get("https://api.example.com/test")
        cache.get("https://nonexistent.com")
        stats = cache.get_stats()
        assert stats.writes == 1
        assert stats.hits == 1
        assert stats.misses == 1
    
    def test_cache_ttl_strategy(self, cache_dir):
        cache = ResponseCache(
            cache_dir=cache_dir,
            strategy=CacheStrategy.TTL,
            enable_disk_persistence=False
        )
        url = "https://api.example.com/ttl"
        cache.set(url, {"data": "ttl"}, ttl=1)
        assert cache.get(url) == {"data": "ttl"}
        time.sleep(1.5)
        assert cache.get(url) is None


class TestCacheEviction:
    @pytest.fixture
    def cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_lru_eviction(self, cache_dir):
        cache = ResponseCache(
            cache_dir=cache_dir,
            max_size_mb=1,
            strategy=CacheStrategy.LRU,
            enable_disk_persistence=False
        )
        for i in range(100):
            cache.set(f"https://api.example.com/{i}", {"data": "x" * 1000})
        assert cache.get_stats().writes >= 1


class TestCachedDecorator:
    def test_cached_decorator(self):
        # Reset global cache
        cache_module._default_cache = None
        
        call_count = [0]
        
        @cached(ttl=3600)
        def fetch_data(url):
            call_count[0] += 1
            return {"fetched": url}
        
        url = "https://api.example.com/decorated_new_" + str(time.time())
        result1 = fetch_data(url=url)
        assert result1 == {"fetched": url}
        assert call_count[0] == 1
        
        result2 = fetch_data(url=url)
        assert result2 == {"fetched": url}
        assert call_count[0] == 1  # Cached
        
        # Cleanup
        cache_module._default_cache = None


class TestDiskPersistence:
    @pytest.fixture
    def cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_persistence_write(self, cache_dir):
        cache = ResponseCache(
            cache_dir=cache_dir,
            enable_disk_persistence=True,
            compress_threshold=0
        )
        cache.set("https://api.example.com/persist", {"data": "value"})
        cache_files = list(Path(cache_dir).glob("*.cache"))
        assert len(cache_files) > 0
    
    def test_persistence_load(self, cache_dir):
        cache1 = ResponseCache(
            cache_dir=cache_dir,
            enable_disk_persistence=True
        )
        cache1.set("https://api.example.com/load", {"data": "loaded"})
        
        cache2 = ResponseCache(
            cache_dir=cache_dir,
            enable_disk_persistence=True
        )
        result = cache2.get("https://api.example.com/load")
        assert result == {"data": "loaded"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
