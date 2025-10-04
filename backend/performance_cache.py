"""
Advanced Performance Caching Service
Comprehensive caching strategy for API responses, user data, and computational results
"""

import redis
import json
import hashlib
import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from functools import wraps
import pickle
import os
from concurrent.futures import ThreadPoolExecutor

# Configure logger
logger = logging.getLogger(__name__)

class AdvancedCacheService:
    def __init__(self):
        """Initialize advanced caching with multiple cache layers"""
        self.redis_client = None
        self.memory_cache = {}
        self.memory_cache_size = 1000  # Max items in memory cache
        self.connected = False
        self.cache_enabled = True
        
        # Cache TTL configurations (in seconds)
        self.TTL_CONFIG = {
            'user_profile': 300,        # 5 minutes
            'financial_goals': 600,     # 10 minutes
            'budgets': 300,             # 5 minutes
            'transactions': 180,        # 3 minutes
            'analytics': 900,           # 15 minutes
            'leaderboards': 1800,       # 30 minutes
            'hustle_recommendations': 3600,  # 1 hour
            'trending_skills': 7200,    # 2 hours
            'static_data': 86400,       # 24 hours
            'computation_heavy': 1800,  # 30 minutes
        }
        
        # Initialize connection and thread pool
        self._initialize_connection()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
    
    def _initialize_connection(self):
        """Initialize Redis connection with fallback"""
        try:
            redis_configs = [
                {"host": "localhost", "port": 6379, "db": 1},
                {"host": "127.0.0.1", "port": 6379, "db": 1},
                {"host": "redis", "port": 6379, "db": 1},
            ]
            
            for config in redis_configs:
                try:
                    self.redis_client = redis.Redis(
                        host=config["host"],
                        port=config["port"],
                        db=config["db"],
                        socket_timeout=3,
                        socket_connect_timeout=3,
                        retry_on_timeout=True,
                        decode_responses=False  # For pickle support
                    )
                    
                    self.redis_client.ping()
                    self.connected = True
                    logger.info(f"✅ Advanced Cache connected to Redis on {config['host']}:{config['port']}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis at {config['host']}:{config['port']}: {str(e)}")
                    continue
            
            logger.info("⚠️ Redis not available - using memory-only cache mode")
            self.cache_enabled = True  # Still enable caching with memory only
            self.connected = False
            
        except Exception as e:
            logger.error(f"Cache initialization error: {str(e)}")
            self.cache_enabled = False
            self.connected = False

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key from prefix and parameters"""
        # Create a consistent key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key_string = f"{prefix}:{':'.join(key_parts)}"
        
        # Hash long keys to keep them manageable
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string

    def _get_from_memory_cache(self, key: str) -> Optional[Any]:
        """Get item from memory cache"""
        if key in self.memory_cache:
            item, expiry = self.memory_cache[key]
            if datetime.now() < expiry:
                return item
            else:
                del self.memory_cache[key]
        return None

    def _set_in_memory_cache(self, key: str, value: Any, ttl: int):
        """Set item in memory cache with TTL"""
        # Manage memory cache size
        if len(self.memory_cache) >= self.memory_cache_size:
            # Remove oldest items
            oldest_keys = list(self.memory_cache.keys())[:100]
            for old_key in oldest_keys:
                del self.memory_cache[old_key]
        
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.memory_cache[key] = (value, expiry)

    async def get(self, cache_type: str, *args, **kwargs) -> Optional[Any]:
        """Get cached data with multi-layer lookup"""
        key = self._generate_cache_key(cache_type, *args, **kwargs)
        
        # Try memory cache first (fastest)
        value = self._get_from_memory_cache(key)
        if value is not None:
            logger.debug(f"✅ Memory cache HIT: {cache_type}")
            return value
        
        # Try Redis cache
        if self.connected:
            try:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    value = pickle.loads(cached_data)
                    # Store in memory cache for faster access
                    ttl = self.TTL_CONFIG.get(cache_type, 300)
                    self._set_in_memory_cache(key, value, ttl // 2)  # Shorter TTL for memory
                    logger.debug(f"✅ Redis cache HIT: {cache_type}")
                    return value
            except Exception as e:
                logger.error(f"Redis get error: {str(e)}")
        
        logger.debug(f"❌ Cache MISS: {cache_type}")
        return None

    async def set(self, cache_type: str, value: Any, *args, **kwargs) -> bool:
        """Set cached data in both memory and Redis"""
        key = self._generate_cache_key(cache_type, *args, **kwargs)
        ttl = self.TTL_CONFIG.get(cache_type, 300)
        
        try:
            # Set in memory cache
            self._set_in_memory_cache(key, value, ttl)
            
            # Set in Redis cache
            if self.connected:
                serialized_value = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized_value)
                logger.debug(f"✅ Cached: {cache_type} (TTL: {ttl}s)")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {cache_type}: {str(e)}")
            return False

    async def delete(self, cache_type: str, *args, **kwargs) -> bool:
        """Delete cached data from all layers"""
        key = self._generate_cache_key(cache_type, *args, **kwargs)
        
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
            
            # Remove from Redis
            if self.connected:
                self.redis_client.delete(key)
            
            logger.debug(f"🗑️  Deleted cache: {cache_type}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for {cache_type}: {str(e)}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache keys matching a pattern"""
        deleted_count = 0
        
        try:
            # Clear matching keys from memory cache
            keys_to_delete = [key for key in self.memory_cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.memory_cache[key]
                deleted_count += 1
            
            # Clear matching keys from Redis
            if self.connected:
                keys = self.redis_client.keys(f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    deleted_count += len(keys)
            
            logger.info(f"🧹 Invalidated {deleted_count} cache entries matching '{pattern}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {str(e)}")
            return 0

    async def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        stats = {
            "memory_cache": {
                "enabled": True,
                "size": len(self.memory_cache),
                "max_size": self.memory_cache_size
            },
            "redis_cache": {
                "enabled": self.connected,
                "connected": self.connected
            }
        }
        
        if self.connected:
            try:
                info = self.redis_client.info()
                stats["redis_cache"].update({
                    "memory_usage": info.get('used_memory_human', 'N/A'),
                    "connected_clients": info.get('connected_clients', 0),
                    "total_commands": info.get('total_commands_processed', 0),
                    "keyspace_hits": info.get('keyspace_hits', 0),
                    "keyspace_misses": info.get('keyspace_misses', 0)
                })
                
                # Calculate hit ratio
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                if hits + misses > 0:
                    stats["redis_cache"]["hit_ratio"] = round(hits / (hits + misses), 3)
                
            except Exception as e:
                logger.error(f"Stats collection error: {str(e)}")
        
        return stats

    async def warm_cache(self, cache_types: List[str]) -> Dict:
        """Pre-warm cache with frequently accessed data"""
        warming_results = {}
        
        for cache_type in cache_types:
            try:
                if cache_type == "trending_skills":
                    # Warm trending skills cache
                    from server import get_trending_skills_data
                    skills_data = await get_trending_skills_data()
                    await self.set("trending_skills", skills_data)
                    warming_results[cache_type] = "success"
                
                elif cache_type == "static_data":
                    # Warm static data cache
                    static_data = {
                        "categories": ["Food", "Transportation", "Books", "Entertainment", 
                                     "Rent", "Utilities", "Movies", "Shopping", "Groceries"],
                        "emergency_types": ["Medical", "Family", "Job Loss", "Education", "Travel"],
                        "avatar_options": ["Boy", "Man", "Girl", "Woman", "Grandfather", "Grandmother"]
                    }
                    await self.set("static_data", static_data)
                    warming_results[cache_type] = "success"
                
                else:
                    warming_results[cache_type] = "skipped"
                    
            except Exception as e:
                logger.error(f"Cache warming error for {cache_type}: {str(e)}")
                warming_results[cache_type] = f"error: {str(e)}"
        
        logger.info(f"🔥 Cache warming completed: {warming_results}")
        return warming_results

# Decorator for automatic caching
def cache_result(cache_type: str, ttl: Optional[int] = None):
    """Decorator to automatically cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = await advanced_cache.get(cache_type, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                await advanced_cache.set(cache_type, result, cache_key)
            
            return result
        return wrapper
    return decorator

# Global cache service instance
advanced_cache = AdvancedCacheService()

# Export for use in other modules
__all__ = ['AdvancedCacheService', 'advanced_cache', 'cache_result']
