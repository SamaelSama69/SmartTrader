"""
Thread-safe caching with disk and Redis support
"""
import time
import json
import hashlib
import threading
from pathlib import Path
from functools import wraps
import functools
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta


class TTLCache:
    """
    Simple in-memory cache with TTL support
    Thread-safe for single-process use
    """

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache with default TTL in seconds

        Args:
            default_ttl: Default time-to-live in seconds (5 minutes default)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key based on function and arguments"""
        # Create a hashable representation of the arguments
        key_parts = [func_name]

        # Add args (skip self/cls for methods)
        for arg in args:
            if isinstance(arg, (str, int, float, bool, type(None))):
                key_parts.append(str(arg))
            elif isinstance(arg, (list, tuple)):
                key_parts.append(str(tuple(arg)))
            elif isinstance(arg, dict):
                # Sort dict keys for consistent hashing
                sorted_dict = json.dumps(arg, sort_keys=True)
                key_parts.append(sorted_dict)
            else:
                # For other types, use their string representation
                key_parts.append(str(arg))

        # Add kwargs (sorted for consistency)
        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            if isinstance(v, (str, int, float, bool, type(None))):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{str(v)}")

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry['expires_at']:
            # Expired - remove and return None
            del self._cache[key]
            return None

        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with TTL"""
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }

    def delete(self, key: str):
        """Delete a specific key from cache"""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cached items"""
        self._cache.clear()

    def cleanup_expired(self):
        """Remove all expired entries"""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if now > v['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.cleanup_expired()
        return {
            'size': len(self._cache),
            'default_ttl': self.default_ttl
        }


# Global cache instances for different purposes
market_data_cache = TTLCache(default_ttl=300)  # 5 minutes for market data
sentiment_cache = TTLCache(default_ttl=3600)   # 1 hour for sentiment
company_info_cache = TTLCache(default_ttl=3600)  # 1 hour for company info
indicators_cache = TTLCache(default_ttl=600)     # 10 minutes for indicators


def cached(cache_instance: TTLCache, ttl: Optional[int] = None):
    """
    Decorator for caching function results with TTL

    Args:
        cache_instance: TTLCache instance to use
        ttl: Optional TTL override in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_instance._make_key(
                func.__name__, args, kwargs
            )

            # Try to get from cache
            cached_value = cache_instance.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


def rate_limited(min_interval: float = 0.5):
    """
    Decorator to rate limit function calls

    Args:
        min_interval: Minimum seconds between calls (default 0.5s)
    """
    last_called = {}

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            func_id = id(func)

            if func_id in last_called:
                elapsed = now - last_called[func_id]
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)

            last_called[func_id] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DiskCache:
    """Disk-backed cache for multi-process access"""

    def __init__(self, cache_dir: str = "cache", ttl: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self._lock = threading.Lock()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{hash(key)}.json"

    def get(self, key: str) -> Optional[Any]:
        cache_file = self._cache_path(key)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            if time.time() - data['timestamp'] > self.ttl:
                cache_file.unlink()  # Expired
                return None

            return data['value']
        except Exception:
            return None

    def set(self, key: str, value: Any):
        with self._lock:
            cache_file = self._cache_path(key)
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'value': value
                    }, f, default=str)
            except Exception as e:
                print(f"DiskCache write error: {e}")

    def clear(self):
        with self._lock:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()


# Optional: Redis cache (if redis is installed)
try:
    import redis

    class RedisCache:
        """Redis-backed cache for distributed systems"""

        def __init__(self, host='localhost', port=6379, db=0, ttl: int = 300):
            self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.ttl = ttl

        def get(self, key: str) -> Optional[Any]:
            try:
                data = self.redis.get(key)
                return json.loads(data) if data else None
            except Exception:
                return None

        def set(self, key: str, value: Any):
            try:
                self.redis.setex(key, self.ttl, json.dumps(value, default=str))
            except Exception as e:
                print(f"RedisCache write error: {e}")
except ImportError:
    pass  # Redis not installed
