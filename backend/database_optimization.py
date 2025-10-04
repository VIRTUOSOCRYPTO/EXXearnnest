"""
Database Performance Optimization
Connection pooling, query optimization, and performance monitoring
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logger
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    def __init__(self):
        """Initialize database optimizer with connection pooling"""
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/earnnest')
        self.client = None
        self.database = None
        self.connection_pool_size = 50
        self.query_stats = {}
        self.slow_query_threshold = 1000  # ms
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance monitoring
        self.performance_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_query_time': 0,
            'connection_pool_usage': 0
        }
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize optimized MongoDB connection"""
        try:
            # Configure connection with optimizations
            self.client = AsyncIOMotorClient(
                self.mongo_url,
                maxPoolSize=self.connection_pool_size,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
                retryWrites=True,
                # Write concern for performance
                w='majority',
                wtimeoutMS=10000
            )
            
            # Extract database name from URL
            db_name = self.mongo_url.split('/')[-1].split('?')[0]
            self.database = self.client[db_name]
            
            logger.info(f"✅ Database optimizer initialized with pool size: {self.connection_pool_size}")
            
        except Exception as e:
            logger.error(f"Database optimizer initialization error: {str(e)}")
            raise

    async def create_performance_indexes(self):
        """Create optimized indexes for better query performance"""
        try:
            # User collection indexes
            await self.database.users.create_index([("email", 1)], unique=True)
            await self.database.users.create_index([("user_id", 1)], unique=True)
            await self.database.users.create_index([("university", 1)])
            await self.database.users.create_index([("role", 1)])
            await self.database.users.create_index([("created_at", -1)])
            
            # Transaction collection indexes
            await self.database.transactions.create_index([("user_id", 1), ("created_at", -1)])
            await self.database.transactions.create_index([("category", 1)])
            await self.database.transactions.create_index([("type", 1)])
            await self.database.transactions.create_index([("amount", -1)])
            
            # Budget collection indexes
            await self.database.budgets.create_index([("user_id", 1), ("category", 1)], unique=True)
            await self.database.budgets.create_index([("user_id", 1)])
            
            # Financial goals collection indexes
            await self.database.financial_goals.create_index([("user_id", 1)])
            await self.database.financial_goals.create_index([("category", 1)])
            await self.database.financial_goals.create_index([("target_date", 1)])
            
            # Gamification indexes
            await self.database.gamification_profiles.create_index([("user_id", 1)], unique=True)
            await self.database.gamification_profiles.create_index([("level", -1)])
            await self.database.gamification_profiles.create_index([("experience_points", -1)])
            await self.database.gamification_profiles.create_index([("current_streak", -1)])
            
            # Social sharing indexes
            await self.database.social_shares.create_index([("user_id", 1), ("created_at", -1)])
            await self.database.social_shares.create_index([("platform", 1)])
            
            # Notification indexes
            await self.database.notifications.create_index([("user_id", 1), ("created_at", -1)])
            await self.database.notifications.create_index([("read", 1)])
            
            # Compound indexes for complex queries
            await self.database.transactions.create_index([
                ("user_id", 1), ("type", 1), ("created_at", -1)
            ])
            
            await self.database.gamification_profiles.create_index([
                ("university", 1), ("experience_points", -1)
            ])
            
            logger.info("✅ Performance indexes created successfully")
            
        except Exception as e:
            logger.error(f"Index creation error: {str(e)}")

    async def optimize_query(self, collection_name: str, query: Dict, 
                           options: Optional[Dict] = None) -> List[Dict]:
        """Execute optimized query with caching and monitoring"""
        start_time = time.time()
        
        # Generate cache key
        cache_key = f"{collection_name}:{hash(str(query) + str(options))}"
        
        # Check cache first
        if cache_key in self.query_cache:
            cached_result, cache_time = self.query_cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                self.performance_stats['cache_hits'] += 1
                return cached_result
        
        try:
            # Execute query
            collection = getattr(self.database, collection_name)
            
            if options:
                # Handle different query types
                if 'sort' in options and 'limit' in options:
                    cursor = collection.find(query).sort(options['sort']).limit(options['limit'])
                elif 'sort' in options:
                    cursor = collection.find(query).sort(options['sort'])
                elif 'limit' in options:
                    cursor = collection.find(query).limit(options['limit'])
                else:
                    cursor = collection.find(query)
            else:
                cursor = collection.find(query)
            
            # Execute and collect results
            results = await cursor.to_list(length=None)
            
            # Calculate query time
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Update performance stats
            self.performance_stats['total_queries'] += 1
            if query_time > self.slow_query_threshold:
                self.performance_stats['slow_queries'] += 1
                logger.warning(f"Slow query detected: {collection_name} - {query_time:.2f}ms")
            
            # Update average query time
            total_time = self.performance_stats['avg_query_time'] * (self.performance_stats['total_queries'] - 1)
            self.performance_stats['avg_query_time'] = (total_time + query_time) / self.performance_stats['total_queries']
            
            # Cache result
            self.query_cache[cache_key] = (results, time.time())
            self.performance_stats['cache_misses'] += 1
            
            # Clean old cache entries
            if len(self.query_cache) > 1000:
                await self._clean_query_cache()
            
            logger.debug(f"Query executed: {collection_name} - {query_time:.2f}ms - {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Query optimization error in {collection_name}: {str(e)}")
            raise

    async def _clean_query_cache(self):
        """Clean old entries from query cache"""
        current_time = time.time()
        keys_to_delete = []
        
        for key, (_, cache_time) in self.query_cache.items():
            if current_time - cache_time > self.cache_ttl:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.query_cache[key]
        
        logger.debug(f"Cleaned {len(keys_to_delete)} expired cache entries")

    async def bulk_insert_optimized(self, collection_name: str, documents: List[Dict]) -> bool:
        """Optimized bulk insert with batching"""
        try:
            collection = getattr(self.database, collection_name)
            batch_size = 1000
            
            # Process in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await collection.insert_many(batch, ordered=False)
            
            logger.info(f"✅ Bulk inserted {len(documents)} documents into {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Bulk insert error in {collection_name}: {str(e)}")
            return False

    async def aggregate_optimized(self, collection_name: str, pipeline: List[Dict]) -> List[Dict]:
        """Execute optimized aggregation pipeline"""
        start_time = time.time()
        
        try:
            collection = getattr(self.database, collection_name)
            
            # Add performance hints to pipeline
            optimized_pipeline = pipeline.copy()
            
            # Execute aggregation
            cursor = collection.aggregate(optimized_pipeline, allowDiskUse=True)
            results = await cursor.to_list(length=None)
            
            query_time = (time.time() - start_time) * 1000
            logger.debug(f"Aggregation executed: {collection_name} - {query_time:.2f}ms - {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Aggregation optimization error in {collection_name}: {str(e)}")
            raise

    async def get_performance_stats(self) -> Dict:
        """Get comprehensive database performance statistics"""
        try:
            # Get MongoDB server stats
            server_stats = await self.database.command("serverStatus")
            db_stats = await self.database.command("dbStats")
            
            # Connection pool stats
            pool_stats = {
                'max_pool_size': self.connection_pool_size,
                'current_connections': server_stats.get('connections', {}).get('current', 0),
                'available_connections': server_stats.get('connections', {}).get('available', 0)
            }
            
            # Query performance stats
            query_stats = {
                'total_queries': self.performance_stats['total_queries'],
                'slow_queries': self.performance_stats['slow_queries'],
                'avg_query_time_ms': round(self.performance_stats['avg_query_time'], 2),
                'cache_hit_ratio': round(
                    self.performance_stats['cache_hits'] / 
                    max(1, self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']), 
                    3
                ),
                'cached_queries': len(self.query_cache)
            }
            
            # Database stats
            database_stats = {
                'data_size': db_stats.get('dataSize', 0),
                'storage_size': db_stats.get('storageSize', 0),
                'index_size': db_stats.get('indexSize', 0),
                'collections': db_stats.get('collections', 0),
                'indexes': db_stats.get('indexes', 0)
            }
            
            return {
                'connection_pool': pool_stats,
                'query_performance': query_stats,
                'database': database_stats,
                'uptime_seconds': server_stats.get('uptime', 0),
                'server_version': server_stats.get('version', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Performance stats error: {str(e)}")
            return {}

    async def optimize_database_maintenance(self):
        """Perform database maintenance tasks"""
        try:
            # Compact collections to reclaim space
            collections = await self.database.list_collection_names()
            
            for collection_name in collections:
                try:
                    # Run compact command (be careful in production)
                    await self.database.command("compact", collection_name)
                    logger.debug(f"Compacted collection: {collection_name}")
                except Exception as e:
                    logger.warning(f"Failed to compact {collection_name}: {str(e)}")
            
            # Update collection statistics
            for collection_name in collections:
                try:
                    await self.database.command("collStats", collection_name)
                except Exception as e:
                    logger.warning(f"Failed to update stats for {collection_name}: {str(e)}")
            
            logger.info("✅ Database maintenance completed")
            
        except Exception as e:
            logger.error(f"Database maintenance error: {str(e)}")

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()

# Export for use in other modules
__all__ = ['DatabaseOptimizer', 'db_optimizer']
