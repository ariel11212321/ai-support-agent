"""
AI Support Agent - Worker Pool System
Manages concurrent question processing using ThreadPoolExecutor
"""

import time
import uuid
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from queue import Queue, Empty
from typing import Dict, List, Optional, Callable, Any
from dataclasses import asdict

from models import UserQuestion, WorkerTask, SupportResponse, SystemMetrics
from workflow import SupportWorkflow
from config import Config


class WorkerPool:
    """
    Manages a pool of worker threads for concurrent question processing
    Provides load balancing, queue management, and performance monitoring
    """
    
    def __init__(self, max_workers: int = None, enable_monitoring: bool = True):
        """
        Initialize worker pool
        
        Args:
            max_workers: Maximum number of worker threads
            enable_monitoring: Whether to enable performance monitoring
        """
        self.max_workers = max_workers or Config.MAX_WORKERS
        self.enable_monitoring = enable_monitoring
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="SupportWorker"
        )
        
        # Initialize workflow for each worker
        self.workflow = SupportWorkflow()
        
        # Task management
        self.task_queue = Queue(maxsize=Config.MAX_QUEUE_SIZE)
        self.active_tasks: Dict[str, WorkerTask] = {}
        self.completed_tasks: List[WorkerTask] = []
        self.failed_tasks: List[WorkerTask] = []
        
        # Worker tracking
        self.worker_stats: Dict[int, Dict] = {}
        self.next_worker_id = 1
        self.worker_lock = threading.Lock()
        
        # Performance metrics
        self.start_time = datetime.now()
        self.total_tasks_processed = 0
        self.total_processing_time = 0.0
        
        # Monitoring
        if self.enable_monitoring:
            self.metrics_history: List[SystemMetrics] = []
            self._start_monitoring_thread()
        
        # Shutdown flag
        self.shutdown = False
    
    def submit_question(self, question: UserQuestion, callback: Optional[Callable] = None) -> str:
        """
        Submit a question for processing
        
        Args:
            question: UserQuestion to process
            callback: Optional callback function to call when complete
            
        Returns:
            Task ID for tracking
        """
        if self.shutdown:
            raise RuntimeError("Worker pool is shutting down")
        
        # Create task
        task_id = str(uuid.uuid4())
        task = WorkerTask(
            task_id=task_id,
            question=question
        )
        
        # Add to active tasks
        self.active_tasks[task_id] = task
        
        # Submit to executor
        future = self.executor.submit(self._process_question_worker, task)
        
        # Add callback if provided
        if callback:
            future.add_done_callback(lambda fut: callback(task_id, fut.result()))
        
        return task_id
    
    def submit_batch(self, questions: List[UserQuestion], 
                    progress_callback: Optional[Callable] = None) -> List[str]:
        """
        Submit multiple questions for batch processing
        
        Args:
            questions: List of UserQuestion objects
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for i, question in enumerate(questions):
            task_id = self.submit_question(question)
            task_ids.append(task_id)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, len(questions), task_id)
        
        return task_ids
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.active_tasks.get(task_id)
        if not task:
            # Check completed tasks
            for completed_task in self.completed_tasks:
                if completed_task.task_id == task_id:
                    return {
                        "status": "completed",
                        "task": asdict(completed_task),
                        "result": asdict(completed_task.result) if completed_task.result else None
                    }
            
            # Check failed tasks
            for failed_task in self.failed_tasks:
                if failed_task.task_id == task_id:
                    return {
                        "status": "failed",
                        "task": asdict(failed_task),
                        "error": failed_task.error
                    }
            
            return None
        
        # Active task
        status = "queued"
        if task.started_at:
            status = "processing"
        if task.completed_at:
            status = "completed"
        
        return {
            "status": status,
            "task": asdict(task),
            "worker_id": task.worker_id,
            "processing_time_ms": task.processing_time_ms
        }
    
    def wait_for_completion(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for multiple tasks to complete
        
        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dictionary with completion results
        """
        start_time = time.time()
        completed = []
        failed = []
        timed_out = []
        
        while task_ids:
            if timeout and (time.time() - start_time) > timeout:
                timed_out = task_ids.copy()
                break
            
            # Check task statuses
            still_pending = []
            for task_id in task_ids:
                status = self.get_task_status(task_id)
                if not status:
                    continue
                
                if status["status"] == "completed":
                    completed.append(task_id)
                elif status["status"] == "failed":
                    failed.append(task_id)
                else:
                    still_pending.append(task_id)
            
            task_ids = still_pending
            
            if task_ids:
                time.sleep(0.1)  # Small delay to prevent busy waiting
        
        return {
            "completed": completed,
            "failed": failed,
            "timed_out": timed_out,
            "total_time_seconds": time.time() - start_time
        }
    
    def _process_question_worker(self, task: WorkerTask) -> Optional[SupportResponse]:
        """
        Worker function to process a question
        This runs in a worker thread
        """
        worker_id = self._get_worker_id()
        
        try:
            # Mark task as started
            task.start_processing(worker_id)
            
            # Update worker stats
            self._update_worker_stats(worker_id, "task_started")
            
            # Process question through workflow
            workflow_result = self.workflow.process_question(task.question, worker_id)
            
            # Extract response from workflow result
            if workflow_result.get("error"):
                task.fail_processing(workflow_result["error"])
                self._move_to_failed(task)
                self._update_worker_stats(worker_id, "task_failed")
                return None
            
            response_data = workflow_result.get("final_response")
            if not response_data:
                task.fail_processing("No response generated")
                self._move_to_failed(task)
                self._update_worker_stats(worker_id, "task_failed")
                return None
            
            # Create SupportResponse object
            response = SupportResponse(**response_data)
            
            # Mark task as completed
            task.complete_processing(response)
            self._move_to_completed(task)
            
            # Update performance tracking
            self._update_performance_tracking(task.processing_time_ms)
            self._update_worker_stats(worker_id, "task_completed")
            
            return response
            
        except Exception as e:
            # Handle worker errors
            error_msg = f"Worker {worker_id} error: {str(e)}"
            task.fail_processing(error_msg)
            self._move_to_failed(task)
            self._update_worker_stats(worker_id, "task_failed")
            return None
        
        finally:
            # Clean up active task
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    def _get_worker_id(self) -> int:
        """Get unique worker ID for current thread"""
        with self.worker_lock:
            worker_id = self.next_worker_id
            self.next_worker_id += 1
            
            # Initialize worker stats if needed
            if worker_id not in self.worker_stats:
                self.worker_stats[worker_id] = {
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                    "total_processing_time": 0.0,
                    "thread_name": threading.current_thread().name
                }
            
            return worker_id
    
    def _update_worker_stats(self, worker_id: int, event: str) -> None:
        """Update statistics for a worker"""
        if worker_id not in self.worker_stats:
            return
        
        stats = self.worker_stats[worker_id]
        
        if event == "task_completed":
            stats["tasks_completed"] += 1
        elif event == "task_failed":
            stats["tasks_failed"] += 1
    
    def _move_to_completed(self, task: WorkerTask) -> None:
        """Move task to completed list"""
        self.completed_tasks.append(task)
        
        # Keep only recent completed tasks to prevent memory buildup
        if len(self.completed_tasks) > 1000:
            self.completed_tasks = self.completed_tasks[-500:]
    
    def _move_to_failed(self, task: WorkerTask) -> None:
        """Move task to failed list"""
        self.failed_tasks.append(task)
        
        # Keep only recent failed tasks
        if len(self.failed_tasks) > 100:
            self.failed_tasks = self.failed_tasks[-50:]
    
    def _update_performance_tracking(self, processing_time: float) -> None:
        """Update overall performance tracking"""
        self.total_tasks_processed += 1
        self.total_processing_time += processing_time
    
    def _start_monitoring_thread(self) -> None:
        """Start background monitoring thread"""
        def monitor():
            while not self.shutdown:
                try:
                    metrics = self._collect_system_metrics()
                    self.metrics_history.append(metrics)
                    
                    # Keep only recent metrics
                    if len(self.metrics_history) > 1440:  # 24 hours at 1-minute intervals
                        self.metrics_history = self.metrics_history[-720:]  # Keep 12 hours
                    
                    time.sleep(60)  # Collect metrics every minute
                    
                except Exception:
                    pass  # Ignore monitoring errors
        
        monitor_thread = threading.Thread(target=monitor, daemon=True, name="MetricsMonitor")
        monitor_thread.start()
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        import psutil
        
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            memory_mb = 0.0
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return SystemMetrics(
            active_workers=len([w for w in self.worker_stats.values() if w["tasks_completed"] > 0]),
            queue_size=len(self.active_tasks),
            cache_size=0,  # Will be updated by cache system
            memory_usage_mb=memory_mb,
            uptime_seconds=uptime
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate worker efficiency
        worker_efficiency = {}
        for worker_id, stats in self.worker_stats.items():
            total_tasks = stats["tasks_completed"] + stats["tasks_failed"]
            if total_tasks > 0:
                efficiency = stats["tasks_completed"] / total_tasks * 100
                worker_efficiency[worker_id] = {
                    "efficiency_percent": efficiency,
                    "total_tasks": total_tasks,
                    "completed": stats["tasks_completed"],
                    "failed": stats["tasks_failed"]
                }
        
        return {
            "uptime_seconds": uptime_seconds,
            "total_tasks_processed": self.total_tasks_processed,
            "average_processing_time_ms": (
                self.total_processing_time / self.total_tasks_processed
                if self.total_tasks_processed > 0 else 0.0
            ),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "worker_count": self.max_workers,
            "worker_efficiency": worker_efficiency,
            "workflow_stats": self.workflow.get_performance_stats()
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "active_tasks": len(self.active_tasks),
            "max_queue_size": Config.MAX_QUEUE_SIZE,
            "queue_utilization_percent": (len(self.active_tasks) / Config.MAX_QUEUE_SIZE) * 100,
            "oldest_active_task": (
                min(task.created_at for task in self.active_tasks.values())
                if self.active_tasks else None
            )
        }
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        Shutdown the worker pool
        
        Args:
            wait: Whether to wait for active tasks to complete
            timeout: Maximum time to wait for shutdown
        """
        self.shutdown = True
        
        if wait:
            self.executor.shutdown(wait=True, timeout=timeout)
        else:
            # Cancel pending tasks
            for task_id in list(self.active_tasks.keys()):
                task = self.active_tasks[task_id]
                task.fail_processing("Shutdown requested")
                self._move_to_failed(task)
            
            self.executor.shutdown(wait=False)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown(wait=True, timeout=30)