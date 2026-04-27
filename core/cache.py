"""
Redis-backed cache for Scout urgency patterns and metrics.
Production-grade with TTL, eviction, and distributed support.
"""
import json
import time
from typing import Dict, Any, Optional, List

try:
    import redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    RedisError = Exception


class ScoutCache:
    """Redis-backed cache for Scout patterns with metrics"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._redis = None
        self._connected = False
        self._fallback_cache = {}  # Memory fallback when Redis unavailable
        
    def _ensure_connection(self):
        """Lazy connect to Redis with fallback to memory"""
        if not REDIS_AVAILABLE:
            self._connected = False
            return False
            
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                self._redis.ping()
                self._connected = True
            except (RedisError, ConnectionError) as e:
                print(f"Redis connection failed: {e}, falling back to memory cache")
                self._connected = False
                self._redis = None
        return self._connected
    
    def get_pattern(self, pattern: str) -> Optional[float]:
        """Get cached urgency for pattern"""
        if not self._ensure_connection():
            # Fallback to memory cache
            return self._fallback_cache.get(hash(pattern))
            
        try:
            key = f"scout:pattern:{hash(pattern)}"
            value = self._redis.get(key)
            if value:
                self._redis.expire(key, self.ttl_seconds)  # Reset TTL
                return float(value)
        except RedisError as e:
            print(f"Redis get error: {e}")
            self._connected = False
        return None
    
    def set_pattern(self, pattern: str, urgency: float):
        """Cache urgency pattern with TTL"""
        if not self._ensure_connection():
            # Fallback to memory cache
            self._fallback_cache[hash(pattern)] = urgency
            return
            
        try:
            key = f"scout:pattern:{hash(pattern)}"
            pipeline = self._redis.pipeline()
            pipeline.set(key, urgency, ex=self.ttl_seconds)
            pipeline.incr("scout:cache:writes")
            pipeline.execute()
        except RedisError as e:
            print(f"Redis set error: {e}")
            self._connected = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        if not self._ensure_connection():
            return {
                "redis_connected": False,
                "cache_size": len(self._fallback_cache),
                "cache_hits": 0,
                "cache_misses": 0,
                "fallback_active": True
            }
            
        try:
            stats = {
                "redis_connected": True,
                "cache_size": self._redis.dbsize(),
                "cache_hits": int(self._redis.get("scout:cache:hits") or 0),
                "cache_misses": int(self._redis.get("scout:cache:misses") or 0),
                "cache_writes": int(self._redis.get("scout:cache:writes") or 0),
                "ttl_seconds": self.ttl_seconds
            }
            stats["hit_rate"] = round(stats["cache_hits"] / max(1, stats["cache_hits"] + stats["cache_misses"]), 3)
            return stats
        except RedisError as e:
            print(f"Redis stats error: {e}")
            return {"redis_connected": False, "error": str(e), "fallback_cache_size": len(self._fallback_cache)}
    
    def record_hit(self):
        """Record cache hit metric"""
        if self._ensure_connection():
            try:
                self._redis.incr("scout:cache:hits")
            except RedisError:
                pass
    
    def record_miss(self):
        """Record cache miss metric"""
        if self._ensure_connection():
            try:
                self._redis.incr("scout:cache:misses")
            except RedisError:
                pass
    
    def clear_cache(self):
        """Clear all scout cache keys"""
        if self._ensure_connection():
            try:
                pattern = "scout:*"
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
            except RedisError:
                pass
    
    def get_eviction_policy(self) -> str:
        """Get Redis eviction policy"""
        if self._ensure_connection():
            try:
                config = self._redis.config_get("maxmemory-policy")
                return config.get("maxmemory-policy", "unknown")
            except RedisError:
                pass
        return "disabled"