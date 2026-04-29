"""
SprintCycle API 缓存模块
提供 HTTP 响应缓存功能，减少重复请求，提升性能
"""
import hashlib
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import gzip
import pickle


class CacheStrategy(Enum):
    """缓存策略"""
    LRU = "lru"           # 最近最少使用
    LFU = "lfu"           # 最不经常使用
    TTL = "ttl"           # 基于时间过期
    FIFO = "fifo"         # 先进先出


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def touch(self):
        """更新访问时间"""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    writes: int = 0
    total_size_bytes: int = 0
    start_time: float = field(default_factory=time.time)
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def uptime(self) -> float:
        """运行时间（秒）"""
        return time.time() - self.start_time


class ResponseCache:
    """
    HTTP 响应缓存
    
    特性：
    - 内存缓存 + 磁盘持久化
    - 支持 LRU/LFU/TTL/FIFO 多种策略
    - 线程安全
    - 自动压缩大对象
    - 过期自动清理
    """
    
    def __init__(
        self,
        cache_dir: str = ".sprintcycle/cache",
        max_size_mb: int = 100,
        default_ttl: int = 3600,
        strategy: CacheStrategy = CacheStrategy.LRU,
        enable_disk_persistence: bool = True,
        compress_threshold: int = 1024,
    ):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.enable_disk_persistence = enable_disk_persistence
        self.compress_threshold = compress_threshold
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载磁盘缓存
        if enable_disk_persistence:
            self._load_from_disk()
        
        # 启动后台清理线程
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _generate_key(self, request: Dict) -> str:
        """生成缓存键"""
        # 对请求进行规范化
        normalized = json.dumps(request, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def _get_request_hash(self, url: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, 
                          headers: Optional[Dict[str, Any]] = None) -> str:
        """获取请求哈希"""
        request_data = {
            "url": url,
            "method": method.upper(),
            "params": params or {},
            "headers": headers or {},
        }
        return self._generate_key(request_data)
    
    def get(self, url: str, method: str = "GET", params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        获取缓存的响应
        
        Args:
            url: 请求 URL
            method: HTTP 方法
            params: 请求参数
            headers: 请求头
            
        Returns:
            缓存的响应数据，或 None（未命中）
        """
        key = self._get_request_hash(url, method, params, headers)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            # 检查是否过期
            if self._is_expired(entry):
                del self._cache[key]
                self._stats.misses += 1
                self._remove_from_disk(key)
                return None
            
            # 更新访问信息
            entry.touch()
            self._stats.hits += 1
            
            return entry.value
    
    def set(self, url: str, value: Any, method: str = "GET",
            params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None,
            ttl: Optional[int] = None) -> None:
        """
        设置缓存
        
        Args:
            url: 请求 URL
            value: 响应数据
            method: HTTP 方法
            params: 请求参数
            headers: 请求头
            ttl: 过期时间（秒），None 使用默认值
        """
        key = self._get_request_hash(url, method, params, headers)
        ttl = ttl or self.default_ttl
        
        # 估算大小
        try:
            value_size = len(pickle.dumps(value))
        except Exception:
            value_size = len(str(value))
        
        with self._lock:
            # 如果超过最大大小，触发清理
            if self._stats.total_size_bytes + value_size > self.max_size_bytes:
                self._evict(value_size)
            
            entry = CacheEntry(
                key=key,
                value=value,
                size_bytes=value_size,
                metadata={
                    "url": url,
                    "method": method,
                    "params": params,
                    "headers": headers,
                    "expires_at": time.time() + ttl,
                }
            )
            
            self._cache[key] = entry
            self._stats.writes += 1
            self._stats.total_size_bytes += value_size
            
            # 持久化到磁盘
            if self.enable_disk_persistence:
                self._save_to_disk(key, entry)
    
    def invalidate(self, url: Optional[str] = None, pattern: Optional[str] = None) -> int:
        """
        使缓存失效
        
        Args:
            url: 精确的 URL（可选）
            pattern: URL 匹配模式（可选）
            
        Returns:
            删除的条目数量
        """
        count = 0
        with self._lock:
            keys_to_remove = []
            
            for key, entry in self._cache.items():
                should_remove = False
                
                if url and entry.metadata.get("url") == url:
                    should_remove = True
                elif pattern and pattern in entry.metadata.get("url", ""):
                    should_remove = True
                
                if should_remove:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                entry = self._cache.pop(key, None)
                if entry:
                    self._stats.total_size_bytes -= entry.size_bytes
                    self._remove_from_disk(key)
                    count += 1
        
        return count
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._stats.total_size_bytes = 0
            
            if self.enable_disk_persistence:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                writes=self._stats.writes,
                total_size_bytes=self._stats.total_size_bytes,
                start_time=self._stats.start_time,
            )
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        stats = self.get_stats()
        with self._lock:
            return {
                "strategy": self.strategy.value,
                "max_size_mb": self.max_size_bytes // (1024 * 1024),
                "current_size_mb": self._stats.total_size_bytes / (1024 * 1024),
                "entries": len(self._cache),
                "hit_rate": f"{stats.hit_rate * 100:.2f}%",
                "hits": stats.hits,
                "misses": stats.misses,
                "evictions": stats.evictions,
                "uptime_seconds": stats.uptime,
            }
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否过期"""
        if self.strategy == CacheStrategy.TTL:
            expires_at = entry.metadata.get("expires_at", 0)
            return time.time() > expires_at
        return False
    
    def _evict(self, needed_size: int) -> None:
        """驱逐条目以腾出空间"""
        if not self._cache:
            return
        
        candidates = list(self._cache.values())
        
        if self.strategy == CacheStrategy.LRU:
            # 按最后访问时间排序
            candidates.sort(key=lambda e: e.last_accessed)
        elif self.strategy == CacheStrategy.LFU:
            # 按访问次数排序
            candidates.sort(key=lambda e: e.access_count)
        elif self.strategy == CacheStrategy.FIFO:
            # 按创建时间排序
            candidates.sort(key=lambda e: e.created_at)
        
        # 驱逐直到有足够空间
        while candidates and self._stats.total_size_bytes + needed_size > self.max_size_bytes:
            entry = candidates.pop(0)
            key = entry.key
            del self._cache[key]
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.evictions += 1
            self._remove_from_disk(key)
    
    def _background_cleanup(self) -> None:
        """后台清理过期条目"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            self._cleanup_expired()
    
    def _cleanup_expired(self) -> None:
        """清理过期的条目"""
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in keys_to_remove:
                entry = self._cache.pop(key, None)
                if entry:
                    self._stats.total_size_bytes -= entry.size_bytes
                    self._remove_from_disk(key)
    
    def _save_to_disk(self, key: str, entry: CacheEntry) -> None:
        """保存到磁盘"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            data = {
                "entry": entry,
                "compressed": False,
            }
            
            # 压缩大对象
            value_data = pickle.dumps(entry.value)
            if len(value_data) > self.compress_threshold:
                value_data = gzip.compress(value_data)
                data["compressed"] = True
            
            data["value"] = value_data
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            pass  # 静默处理磁盘写入错误
    
    def _load_from_disk(self) -> None:
        """从磁盘加载缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    entry = data["entry"]
                    value_data = data["value"]
                    
                    # 解压
                    if data.get("compressed"):
                        value_data = gzip.decompress(value_data)
                    
                    entry.value = pickle.loads(value_data)
                    
                    # 检查是否过期
                    if not self._is_expired(entry):
                        self._cache[entry.key] = entry
                        self._stats.total_size_bytes += entry.size_bytes
                        self._stats.writes += 1
                except Exception:
                    pass  # 跳过损坏的缓存文件
        except Exception:
            pass
    
    def _remove_from_disk(self, key: str) -> None:
        """从磁盘删除缓存"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception:
            pass


# ============================================================
# 便捷函数
# ============================================================

_default_cache: Optional[ResponseCache] = None


def get_cache(
    cache_dir: str = ".sprintcycle/cache",
    max_size_mb: int = 100,
    default_ttl: int = 3600,
) -> ResponseCache:
    """获取全局默认缓存实例"""
    global _default_cache
    if _default_cache is None:
        _default_cache = ResponseCache(
            cache_dir=cache_dir,
            max_size_mb=max_size_mb,
            default_ttl=default_ttl,
        )
    return _default_cache


def cached(
    ttl: int = 3600,
    url_param: str = "url",
):
    """
    缓存装饰器
    
    用法:
        @cached(ttl=3600)
        def fetch_data(url):
            return requests.get(url).json()
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache()
        
        def wrapper(*args, **kwargs):
            # 从参数中提取 URL
            url = kwargs.get(url_param) or (args[0] if args else None)
            
            if url:
                # 尝试从缓存获取
                cached_value = cache.get(url)
                if cached_value is not None:
                    return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存到缓存
            if url:
                cache.set(url, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


if __name__ == "__main__":
    print("SprintCycle API 缓存模块 v4.9")
    print("-" * 40)
    
    # 测试缓存
    cache = ResponseCache(cache_dir="/tmp/test_cache", max_size_mb=10)
    
    # 测试写入
    cache.set("https://api.example.com/data", {"key": "value"})
    print(f"✅ 写入缓存")
    
    # 测试读取
    result = cache.get("https://api.example.com/data")
    print(f"✅ 读取缓存: {result}")
    
    # 测试统计
    info = cache.get_cache_info()
    print(f"📊 缓存信息: {info}")
    
    print("-" * 40)
    print("模块加载成功！")
