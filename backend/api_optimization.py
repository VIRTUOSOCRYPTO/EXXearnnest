"""
API Response Optimization Service
Compression, pagination, rate limiting, and response optimization
"""

import gzip
import json
import logging
from typing import Any, Dict, List, Optional, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import asyncio
import time
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# Configure logger
logger = logging.getLogger(__name__)

class APIOptimizer:
    def __init__(self):
        """Initialize API optimizer"""
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.default_page_size = 20
        self.max_page_size = 100
        self.response_cache = {}
        self.request_stats = defaultdict(list)
        self.rate_limit_windows = defaultdict(list)
        
        # Performance thresholds
        self.slow_response_threshold = 1.0  # seconds
        self.compression_ratio_threshold = 0.7  # Compress if ratio < 70%
        
    def compress_response(self, data: Union[str, bytes]) -> bytes:
        """Compress response data using gzip"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            if len(data) < self.compression_threshold:
                return data
            
            compressed = gzip.compress(data)
            compression_ratio = len(compressed) / len(data)
            
            # Only use compression if it's beneficial
            if compression_ratio < self.compression_ratio_threshold:
                logger.debug(f"Response compressed: {len(data)} -> {len(compressed)} bytes ({compression_ratio:.2%})")
                return compressed
            else:
                return data
                
        except Exception as e:
            logger.error(f"Compression error: {str(e)}")
            return data if isinstance(data, bytes) else data.encode('utf-8')

    def optimize_json_response(self, data: Any, compress: bool = True) -> JSONResponse:
        """Create optimized JSON response with optional compression"""
        try:
            # Serialize JSON
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            
            # Determine if we should compress
            should_compress = compress and len(json_str) > self.compression_threshold
            
            if should_compress:
                compressed_data = self.compress_response(json_str)
                
                # Return compressed response
                return Response(
                    content=compressed_data,
                    media_type="application/json",
                    headers={
                        "Content-Encoding": "gzip",
                        "Vary": "Accept-Encoding",
                        "Cache-Control": "public, max-age=300",  # 5 minutes cache
                        "X-Response-Optimized": "true"
                    }
                )
            else:
                return JSONResponse(
                    content=data,
                    headers={
                        "Cache-Control": "public, max-age=300",
                        "X-Response-Optimized": "true"
                    }
                )
                
        except Exception as e:
            logger.error(f"JSON optimization error: {str(e)}")
            return JSONResponse(content=data)

    def paginate_results(self, data: List[Any], page: int = 1, page_size: Optional[int] = None) -> Dict:
        """Paginate results with optimization"""
        if page_size is None:
            page_size = self.default_page_size
        
        # Ensure page_size is within bounds
        page_size = min(max(1, page_size), self.max_page_size)
        page = max(1, page)
        
        # Calculate pagination
        total_items = len(data)
        total_pages = (total_items + page_size - 1) // page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # Extract page data
        page_data = data[start_idx:end_idx]
        
        return {
            "items": page_data,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }

    async def lazy_load_data(self, data_loader_func, limit: int = 50) -> Dict:
        """Implement lazy loading for large datasets"""
        try:
            # Load data in chunks
            chunk_size = min(limit, 100)
            loaded_data = []
            
            async for chunk in data_loader_func(chunk_size):
                loaded_data.extend(chunk)
                if len(loaded_data) >= limit:
                    break
            
            return {
                "data": loaded_data[:limit],
                "loaded_count": len(loaded_data),
                "has_more": len(loaded_data) == limit,
                "next_offset": len(loaded_data) if len(loaded_data) == limit else None
            }
            
        except Exception as e:
            logger.error(f"Lazy loading error: {str(e)}")
            return {"data": [], "loaded_count": 0, "has_more": False}

    def optimize_response_fields(self, data: Union[Dict, List[Dict]], 
                               include_fields: Optional[List[str]] = None,
                               exclude_fields: Optional[List[str]] = None) -> Union[Dict, List[Dict]]:
        """Optimize response by including/excluding specific fields"""
        try:
            if isinstance(data, list):
                return [self._filter_dict_fields(item, include_fields, exclude_fields) for item in data]
            elif isinstance(data, dict):
                return self._filter_dict_fields(data, include_fields, exclude_fields)
            else:
                return data
                
        except Exception as e:
            logger.error(f"Field optimization error: {str(e)}")
            return data

    def _filter_dict_fields(self, data: Dict, include_fields: Optional[List[str]] = None,
                          exclude_fields: Optional[List[str]] = None) -> Dict:
        """Filter dictionary fields based on include/exclude lists"""
        if not isinstance(data, dict):
            return data
            
        filtered_data = {}
        
        for key, value in data.items():
            # Check inclusion/exclusion
            if include_fields and key not in include_fields:
                continue
            if exclude_fields and key in exclude_fields:
                continue
                
            # Recursively filter nested dictionaries
            if isinstance(value, dict):
                filtered_data[key] = self._filter_dict_fields(value, include_fields, exclude_fields)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                filtered_data[key] = [self._filter_dict_fields(item, include_fields, exclude_fields) for item in value]
            else:
                filtered_data[key] = value
        
        return filtered_data

    def track_request_performance(self, request: Request, response_time: float):
        """Track request performance metrics"""
        endpoint = f"{request.method} {request.url.path}"
        
        # Track response time
        self.request_stats[endpoint].append({
            'timestamp': datetime.now(),
            'response_time': response_time,
            'status': 'slow' if response_time > self.slow_response_threshold else 'fast'
        })
        
        # Keep only recent stats (last 1000 requests)
        if len(self.request_stats[endpoint]) > 1000:
            self.request_stats[endpoint] = self.request_stats[endpoint][-500:]
        
        # Log slow requests
        if response_time > self.slow_response_threshold:
            logger.warning(f"Slow request: {endpoint} - {response_time:.3f}s")

    def get_performance_stats(self) -> Dict:
        """Get comprehensive API performance statistics"""
        stats = {
            "endpoints": {},
            "summary": {
                "total_endpoints": len(self.request_stats),
                "total_requests": sum(len(requests) for requests in self.request_stats.values()),
                "slow_requests": 0,
                "avg_response_time": 0
            }
        }
        
        all_response_times = []
        
        for endpoint, requests in self.request_stats.items():
            if not requests:
                continue
                
            response_times = [req['response_time'] for req in requests]
            slow_count = len([req for req in requests if req['status'] == 'slow'])
            
            endpoint_stats = {
                "total_requests": len(requests),
                "avg_response_time": round(sum(response_times) / len(response_times), 3),
                "min_response_time": round(min(response_times), 3),
                "max_response_time": round(max(response_times), 3),
                "slow_requests": slow_count,
                "slow_ratio": round(slow_count / len(requests), 3)
            }
            
            stats["endpoints"][endpoint] = endpoint_stats
            all_response_times.extend(response_times)
            stats["summary"]["slow_requests"] += slow_count
        
        # Calculate overall stats
        if all_response_times:
            stats["summary"]["avg_response_time"] = round(sum(all_response_times) / len(all_response_times), 3)
        
        return stats

    async def implement_response_caching(self, cache_key: str, data_generator_func, ttl: int = 300) -> Any:
        """Implement response-level caching"""
        # Check if response is cached
        if cache_key in self.response_cache:
            cached_data, cache_time = self.response_cache[cache_key]
            if time.time() - cache_time < ttl:
                logger.debug(f"Response cache HIT: {cache_key}")
                return cached_data
        
        # Generate fresh data
        logger.debug(f"Response cache MISS: {cache_key}")
        fresh_data = await data_generator_func() if asyncio.iscoroutinefunction(data_generator_func) else data_generator_func()
        
        # Cache the response
        self.response_cache[cache_key] = (fresh_data, time.time())
        
        # Clean old cache entries
        if len(self.response_cache) > 500:
            await self._clean_response_cache()
        
        return fresh_data

    async def _clean_response_cache(self):
        """Clean old entries from response cache"""
        current_time = time.time()
        keys_to_delete = []
        
        for key, (_, cache_time) in self.response_cache.items():
            if current_time - cache_time > 3600:  # Remove entries older than 1 hour
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.response_cache[key]
        
        logger.debug(f"Cleaned {len(keys_to_delete)} expired response cache entries")

    def create_streaming_response(self, data_generator):
        """Create streaming response for large datasets"""
        async def stream_generator():
            try:
                async for chunk in data_generator:
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    def batch_process_requests(self, requests: List[Dict], batch_size: int = 10) -> List[Any]:
        """Process multiple requests in optimized batches"""
        results = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            # Process batch concurrently
            batch_results = asyncio.gather(*[
                self._process_single_request(request) for request in batch
            ])
            
            results.extend(batch_results)
        
        return results

    async def _process_single_request(self, request_data: Dict) -> Any:
        """Process a single request (placeholder for actual implementation)"""
        # This would contain the actual request processing logic
        await asyncio.sleep(0.01)  # Simulate processing time
        return {"processed": True, "data": request_data}

# Global API optimizer instance
api_optimizer = APIOptimizer()

# Middleware for automatic performance tracking
from starlette.middleware.base import BaseHTTPMiddleware

class PerformanceTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        api_optimizer.track_request_performance(request, response_time)
        return response

# Export for use in other modules
__all__ = ['APIOptimizer', 'api_optimizer', 'PerformanceTrackingMiddleware']
