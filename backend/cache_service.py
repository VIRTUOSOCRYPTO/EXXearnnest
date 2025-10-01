"""
Hospital Cache Service - Redis-based caching for hospital recommendations
Implements intelligent caching strategies to reduce OpenStreetMap API calls
and ensure 24/7 availability for emergency hospital recommendations.
"""

import redis
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import os
import asyncio

# Configure logger
logger = logging.getLogger(__name__)

class HospitalCacheService:
    def __init__(self):
        """Initialize Redis connection with fallback configurations"""
        self.redis_client = None
        self.connected = False
        self.cache_enabled = True
        
        # Cache configuration
        self.DEFAULT_TTL = 24 * 60 * 60  # 24 hours for hospital data
        self.LOCATION_TTL = 12 * 60 * 60  # 12 hours for location-specific cache
        self.API_RATE_LIMIT_TTL = 10 * 60  # 10 minutes for API rate limit tracking
        
        # Initialize connection
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Redis connection with multiple fallback options"""
        try:
            # Try different Redis connection options
            redis_configs = [
                {"host": "localhost", "port": 6379, "db": 0},
                {"host": "127.0.0.1", "port": 6379, "db": 0},
                {"host": "redis", "port": 6379, "db": 0},  # Docker container name
            ]
            
            for config in redis_configs:
                try:
                    # Use redis-py for both sync and async operations
                    self.redis_client = redis.Redis(
                        host=config["host"],
                        port=config["port"],
                        db=config["db"],
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True,
                        decode_responses=True
                    )
                    
                    # Test connection
                    self.redis_client.ping()
                    self.connected = True
                    logger.info(f"✅ Redis connected successfully on {config['host']}:{config['port']}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis at {config['host']}:{config['port']}: {str(e)}")
                    continue
            
            # If no connection successful, disable caching
            logger.warning("❌ Redis connection failed - running without cache (degraded mode)")
            self.cache_enabled = False
            self.connected = False
            
        except Exception as e:
            logger.error(f"Redis initialization error: {str(e)}")
            self.cache_enabled = False
            self.connected = False

    def _generate_cache_key(self, latitude: float, longitude: float, 
                          emergency_type: str, radius: int = 25) -> str:
        """Generate a unique cache key for hospital searches"""
        # Round coordinates to reduce cache key variations
        lat_rounded = round(latitude, 3)  # ~100m precision
        lon_rounded = round(longitude, 3)
        
        key_data = f"hospitals:{lat_rounded}:{lon_rounded}:{emergency_type}:{radius}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _generate_location_key(self, latitude: float, longitude: float, 
                             radius: int = 25) -> str:
        """Generate location-based cache key for general hospital data"""
        lat_rounded = round(latitude, 2)  # ~1km precision for broader caching
        lon_rounded = round(longitude, 2)
        
        key_data = f"location_hospitals:{lat_rounded}:{lon_rounded}:{radius}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_cached_hospitals(self, latitude: float, longitude: float, 
                                 emergency_type: str, radius: int = 25) -> Optional[List[Dict]]:
        """Retrieve cached hospital data"""
        if not self.cache_enabled or not self.connected:
            return None
            
        try:
            # Try emergency-type specific cache first
            specific_key = self._generate_cache_key(latitude, longitude, emergency_type, radius)
            cached_data = self.redis_client.get(specific_key)
            
            if cached_data:
                hospitals = json.loads(cached_data)
                logger.info(f"✅ Cache HIT: Found {len(hospitals)} hospitals for {emergency_type}")
                return hospitals
            
            # Try general location cache as fallback
            location_key = self._generate_location_key(latitude, longitude, radius)
            cached_data = self.redis_client.get(location_key)
            
            if cached_data:
                hospitals = json.loads(cached_data)
                logger.info(f"✅ Cache HIT (fallback): Found {len(hospitals)} hospitals for location")
                return hospitals
                
            logger.info(f"❌ Cache MISS: No cached data for {emergency_type} at {latitude}, {longitude}")
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None

    async def cache_hospitals(self, latitude: float, longitude: float, 
                            emergency_type: str, hospitals: List[Dict], 
                            radius: int = 25) -> bool:
        """Store hospital data in cache with intelligent TTL"""
        if not self.cache_enabled or not self.connected:
            return False
            
        try:
            # Cache emergency-type specific data
            specific_key = self._generate_cache_key(latitude, longitude, emergency_type, radius)
            self.redis_client.setex(
                specific_key, 
                self.DEFAULT_TTL, 
                json.dumps(hospitals, default=str)
            )
            
            # Also cache general location data (broader cache)
            location_key = self._generate_location_key(latitude, longitude, radius)
            self.redis_client.setex(
                location_key, 
                self.LOCATION_TTL, 
                json.dumps(hospitals, default=str)
            )
            
            logger.info(f"✅ Cached {len(hospitals)} hospitals for {emergency_type} (TTL: {self.DEFAULT_TTL}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
            return False

    async def check_api_rate_limit(self, api_endpoint: str = "overpass") -> Tuple[bool, int]:
        """Check if API calls are within rate limits"""
        if not self.cache_enabled or not self.connected:
            return True, 0  # Allow calls if cache not available
            
        try:
            rate_key = f"api_rate_limit:{api_endpoint}"
            current_calls = self.redis_client.get(rate_key)
            
            if current_calls is None:
                current_calls = 0
            else:
                current_calls = int(current_calls)
            
            # Overpass API limit: 600 calls per 10 minutes (be conservative: 500 per 10 min)
            if api_endpoint == "overpass" and current_calls >= 500:
                logger.warning(f"⚠️  API Rate limit reached for {api_endpoint}: {current_calls}/500")
                return False, current_calls
            
            return True, current_calls
            
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            return True, 0  # Allow on error

    async def increment_api_calls(self, api_endpoint: str = "overpass") -> int:
        """Increment API call counter"""
        if not self.cache_enabled or not self.connected:
            return 0
            
        try:
            rate_key = f"api_rate_limit:{api_endpoint}"
            
            # Increment counter with expiry
            current = self.redis_client.incr(rate_key)
            if current == 1:  # First call, set expiry
                self.redis_client.expire(rate_key, self.API_RATE_LIMIT_TTL)
            
            logger.info(f"📊 API calls for {api_endpoint}: {current}")
            return current
            
        except Exception as e:
            logger.error(f"API counter increment error: {str(e)}")
            return 0

    async def get_popular_locations_cache(self) -> List[Dict]:
        """Get cached data for popular/frequently searched locations"""
        if not self.cache_enabled or not self.connected:
            return []
            
        try:
            popular_key = "popular_locations:hospitals"
            cached_data = self.redis_client.get(popular_key)
            
            if cached_data:
                return json.loads(cached_data)
            return []
            
        except Exception as e:
            logger.error(f"Popular locations cache error: {str(e)}")
            return []

    async def cache_popular_location(self, city: str, hospitals: List[Dict]) -> bool:
        """Cache hospital data for popular cities"""
        if not self.cache_enabled or not self.connected:
            return False
            
        try:
            popular_key = f"popular_city:{city.lower().replace(' ', '_')}"
            self.redis_client.setex(
                popular_key, 
                self.DEFAULT_TTL * 2,  # Longer TTL for popular locations
                json.dumps(hospitals, default=str)
            )
            
            logger.info(f"✅ Cached popular location data for {city}")
            return True
            
        except Exception as e:
            logger.error(f"Popular location cache error: {str(e)}")
            return False

    async def get_cache_stats(self) -> Dict:
        """Get cache statistics for monitoring"""
        if not self.cache_enabled or not self.connected:
            return {
                "status": "disabled",
                "connected": False,
                "total_keys": 0,
                "memory_usage": "N/A"
            }
            
        try:
            # Get Redis info
            info = self.redis_client.info()
            
            # Count hospital-related keys
            keys = self.redis_client.keys("hospitals:*")
            location_keys = self.redis_client.keys("location_hospitals:*")
            
            return {
                "status": "enabled",
                "connected": self.connected,
                "total_hospital_keys": len(keys),
                "total_location_keys": len(location_keys),
                "memory_usage": info.get('used_memory_human', 'N/A'),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "connected_clients": info.get('connected_clients', 0)
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def clear_expired_cache(self) -> int:
        """Clear expired cache entries (maintenance function)"""
        if not self.cache_enabled or not self.connected:
            return 0
            
        try:
            # Redis handles TTL expiry automatically, but we can manually clean if needed
            deleted_count = 0
            
            # Get all hospital cache keys
            keys = self.redis_client.keys("hospitals:*")
            keys.extend(self.redis_client.keys("location_hospitals:*"))
            
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key expired
                    self.redis_client.delete(key)
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned {deleted_count} expired cache entries")
                
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
            return 0

    async def warm_popular_locations(self):
        """Pre-warm cache with popular Indian cities (background task)"""
        if not self.cache_enabled or not self.connected:
            return
            
        # Popular Indian cities with coordinates
        popular_cities = [
            {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
            {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
            {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
            {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
            {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
            {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
            {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
            {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
            {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
            {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462}
        ]
        
        logger.info("🔄 Starting cache warming for popular cities...")
        
        for city in popular_cities:
            try:
                # Check if already cached
                cache_key = self._generate_location_key(city["lat"], city["lon"])
                cached = self.redis_client.get(cache_key)
                
                if not cached:
                    logger.info(f"⏳ Cache warming needed for {city['name']}")
                    # Note: Actual warming would require calling the hospital fetch function
                    # This is a placeholder for the warming logic
                else:
                    logger.info(f"✅ {city['name']} already cached")
                    
            except Exception as e:
                logger.error(f"Cache warming error for {city['name']}: {str(e)}")
                continue

# Global cache service instance
cache_service = HospitalCacheService()

# Export for use in other modules
__all__ = ['HospitalCacheService', 'cache_service']
