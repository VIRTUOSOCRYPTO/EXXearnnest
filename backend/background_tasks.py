"""
Background Task Processing Service
Handles computational heavy tasks, cache warming, and periodic maintenance
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
from dataclasses import dataclass
from enum import Enum

# Configure logger
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class BackgroundTask:
    id: str
    name: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    max_retries: int = 3
    retry_count: int = 0
    result: Any = None
    error: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed

class BackgroundTaskProcessor:
    def __init__(self, max_workers: int = 4):
        """Initialize background task processor"""
        self.max_workers = max_workers
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}
        self.is_running = False
        
        # Thread pools for different types of tasks
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=2)
        
        # Task statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_processing_time': 0,
            'tasks_by_priority': {priority.name: 0 for priority in TaskPriority}
        }

    async def start_processing(self):
        """Start the background task processing loop"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("🚀 Background task processor started")
        
        # Start worker coroutines
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.max_workers)
        ]
        
        # Start maintenance task
        maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        try:
            await asyncio.gather(*workers, maintenance_task)
        except Exception as e:
            logger.error(f"Background processor error: {str(e)}")
        finally:
            self.is_running = False

    async def stop_processing(self):
        """Stop the background task processing"""
        self.is_running = False
        logger.info("⏹️  Background task processor stopped")

    async def add_task(self, task: BackgroundTask) -> str:
        """Add a task to the processing queue"""
        # Calculate priority for queue
        priority = -task.priority.value  # Negative for proper priority ordering
        
        # Add timestamp for FIFO within same priority
        priority_with_time = (priority, time.time())
        
        await self.task_queue.put((priority_with_time, task))
        
        # Update statistics
        self.stats['total_tasks'] += 1
        self.stats['tasks_by_priority'][task.priority.name] += 1
        
        logger.info(f"📋 Task added: {task.name} (Priority: {task.priority.name})")
        return task.id

    async def create_and_add_task(self, name: str, function: Callable, 
                                args: tuple = (), kwargs: dict = None,
                                priority: TaskPriority = TaskPriority.MEDIUM,
                                scheduled_for: Optional[datetime] = None,
                                max_retries: int = 3) -> str:
        """Create and add a task to the queue"""
        if kwargs is None:
            kwargs = {}
            
        task = BackgroundTask(
            id=f"{name}_{int(time.time() * 1000)}",
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            max_retries=max_retries
        )
        
        return await self.add_task(task)

    async def _worker(self, worker_name: str):
        """Worker coroutine to process tasks"""
        logger.info(f"👷 Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                try:
                    priority_info, task = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Check if task should be delayed
                if task.scheduled_for and datetime.now() < task.scheduled_for:
                    # Put task back in queue for later processing
                    await self.task_queue.put((priority_info, task))
                    await asyncio.sleep(1)
                    continue
                
                # Process the task
                await self._process_task(worker_name, task)
                
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}")
                await asyncio.sleep(1)
        
        logger.info(f"👷 Worker {worker_name} stopped")

    async def _process_task(self, worker_name: str, task: BackgroundTask):
        """Process a single task"""
        start_time = time.time()
        task.status = "running"
        self.running_tasks[task.id] = task
        
        logger.info(f"🔄 Worker {worker_name} processing: {task.name}")
        
        try:
            # Determine execution method
            if asyncio.iscoroutinefunction(task.function):
                # Async function
                result = await task.function(*task.args, **task.kwargs)
            elif hasattr(task.function, '__name__') and 'cpu_intensive' in task.function.__name__:
                # CPU intensive task - use process pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.process_executor, task.function, *task.args
                )
            else:
                # Regular function - use thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_executor, task.function, *task.args
                )
            
            # Task completed successfully
            task.result = result
            task.status = "completed"
            self.completed_tasks[task.id] = task
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['completed_tasks'] += 1
            self._update_avg_processing_time(processing_time)
            
            logger.info(f"✅ Task completed: {task.name} ({processing_time:.2f}s)")
            
        except Exception as e:
            # Task failed
            task.error = str(e)
            task.status = "failed"
            task.retry_count += 1
            
            logger.error(f"❌ Task failed: {task.name} - {str(e)}")
            
            # Retry if possible
            if task.retry_count < task.max_retries:
                task.status = "pending"
                # Add delay for retry
                task.scheduled_for = datetime.now() + timedelta(seconds=2 ** task.retry_count)
                await self.task_queue.put(((-task.priority.value, time.time()), task))
                logger.info(f"🔄 Task retry scheduled: {task.name} (attempt {task.retry_count + 1})")
            else:
                self.failed_tasks[task.id] = task
                self.stats['failed_tasks'] += 1
                logger.error(f"💀 Task permanently failed: {task.name}")
        
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

    def _update_avg_processing_time(self, processing_time: float):
        """Update average processing time"""
        total_completed = self.stats['completed_tasks']
        if total_completed == 1:
            self.stats['avg_processing_time'] = processing_time
        else:
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = (
                (current_avg * (total_completed - 1) + processing_time) / total_completed
            )

    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        logger.info("🧹 Maintenance loop started")
        
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_tasks()
                await self._log_statistics()
                
            except Exception as e:
                logger.error(f"Maintenance loop error: {str(e)}")

    async def _cleanup_old_tasks(self):
        """Clean up old completed and failed tasks"""
        current_time = datetime.now()
        cleanup_threshold = timedelta(hours=24)
        
        # Clean completed tasks
        completed_to_remove = [
            task_id for task_id, task in self.completed_tasks.items()
            if current_time - task.created_at > cleanup_threshold
        ]
        
        for task_id in completed_to_remove:
            del self.completed_tasks[task_id]
        
        # Clean failed tasks
        failed_to_remove = [
            task_id for task_id, task in self.failed_tasks.items()
            if current_time - task.created_at > cleanup_threshold
        ]
        
        for task_id in failed_to_remove:
            del self.failed_tasks[task_id]
        
        if completed_to_remove or failed_to_remove:
            logger.info(f"🧹 Cleaned up {len(completed_to_remove)} completed and {len(failed_to_remove)} failed tasks")

    async def _log_statistics(self):
        """Log task processing statistics"""
        stats = self.get_statistics()
        logger.info(f"📊 Task Stats - Total: {stats['total']}, Completed: {stats['completed']}, "
                   f"Failed: {stats['failed']}, Running: {stats['running']}, "
                   f"Avg Time: {stats['avg_processing_time']:.2f}s")

    def get_statistics(self) -> Dict:
        """Get comprehensive task processing statistics"""
        return {
            'total': self.stats['total_tasks'],
            'completed': self.stats['completed_tasks'],
            'failed': self.stats['failed_tasks'],
            'running': len(self.running_tasks),
            'queued': self.task_queue.qsize(),
            'avg_processing_time': round(self.stats['avg_processing_time'], 3),
            'tasks_by_priority': self.stats['tasks_by_priority'].copy(),
            'success_rate': round(
                self.stats['completed_tasks'] / max(1, self.stats['total_tasks']), 3
            )
        }

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a specific task"""
        # Check running tasks
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'retry_count': task.retry_count
            }
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'result': task.result
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            task = self.failed_tasks[task_id]
            return {
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'error': task.error,
                'retry_count': task.retry_count
            }
        
        return None

# Common background tasks
async def cache_warming_task():
    """Warm up application caches"""
    try:
        from performance_cache import advanced_cache
        
        # Warm up trending skills cache
        trending_skills = [
            {"name": "Freelancing", "icon": "💼", "category": "Business"},
            {"name": "Graphic Design", "icon": "🎨", "category": "Creative"},
            {"name": "Coding", "icon": "💻", "category": "Technical"},
            {"name": "Digital Marketing", "icon": "📱", "category": "Marketing"}
        ]
        
        await advanced_cache.set("trending_skills", trending_skills)
        logger.info("✅ Cache warming completed")
        
    except Exception as e:
        logger.error(f"Cache warming task error: {str(e)}")
        raise

def cpu_intensive_analytics_calculation(user_data: Dict) -> Dict:
    """CPU intensive analytics calculation"""
    try:
        # Simulate heavy computation
        import math
        
        result = {
            'calculated_score': 0,
            'trends': [],
            'predictions': []
        }
        
        # Complex calculations (placeholder)
        for i in range(1000):
            result['calculated_score'] += math.sqrt(i) * 0.1
        
        return result
        
    except Exception as e:
        logger.error(f"Analytics calculation error: {str(e)}")
        raise

async def database_maintenance_task():
    """Database maintenance and optimization"""
    try:
        from database_optimization import db_optimizer
        
        await db_optimizer.optimize_database_maintenance()
        logger.info("✅ Database maintenance completed")
        
    except Exception as e:
        logger.error(f"Database maintenance error: {str(e)}")
        raise

# Global background task processor instance
background_processor = BackgroundTaskProcessor(max_workers=4)

# Export for use in other modules
__all__ = ['BackgroundTaskProcessor', 'BackgroundTask', 'TaskPriority', 
           'background_processor', 'cache_warming_task', 'cpu_intensive_analytics_calculation',
           'database_maintenance_task']
