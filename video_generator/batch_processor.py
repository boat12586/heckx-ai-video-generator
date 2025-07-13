# video_generator/batch_processor.py - Batch processing system for video generation
import os
import uuid
import json
import threading
import queue
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .models import VideoProject, VideoType, ProjectStatus
from .main_service import VideoGeneratorService

class BatchJobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchJobType(Enum):
    MOTIVATION_BATCH = "motivation_batch"
    LOFI_BATCH = "lofi_batch"
    MIXED_BATCH = "mixed_batch"
    SCHEDULED_BATCH = "scheduled_batch"

@dataclass
class BatchJobItem:
    id: str
    type: VideoType
    parameters: Dict[str, Any]
    priority: int = 1
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.INITIALIZING
    result: Optional[Dict] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class BatchJob:
    id: str
    name: str
    type: BatchJobType
    items: List[BatchJobItem]
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    results: List[Dict] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.results is None:
            self.results = []
        if self.metadata is None:
            self.metadata = {}
        self.total_items = len(self.items)

class BatchProcessor:
    """Advanced batch processing system for video generation"""
    
    def __init__(self, video_service: VideoGeneratorService, max_concurrent_jobs: int = 2):
        self.video_service = video_service
        self.max_concurrent_jobs = max_concurrent_jobs
        self.current_jobs = {}
        self.job_queue = queue.PriorityQueue()
        self.job_history = {}
        self.worker_threads = []
        self.is_running = False
        self.job_callbacks = {}
        
        # Performance tracking
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_videos_generated': 0,
            'average_processing_time': 0,
            'start_time': datetime.now()
        }
        
        print("✅ Batch Processor initialized")
    
    def start_processing(self):
        """Start the batch processing workers"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(self.max_concurrent_jobs):
            worker = threading.Thread(target=self._worker_thread, args=(i,))
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
        
        print(f"🚀 Batch processor started with {self.max_concurrent_jobs} workers")
    
    def stop_processing(self):
        """Stop the batch processing workers"""
        self.is_running = False
        
        # Wait for workers to finish current jobs
        for worker in self.worker_threads:
            worker.join(timeout=30)
        
        self.worker_threads = []
        print("⏹️  Batch processor stopped")
    
    def create_motivation_batch(self,
                               themes: List[str],
                               durations: List[int],
                               custom_scripts: List[str] = None,
                               batch_name: str = None) -> str:
        """Create batch job for multiple motivation videos"""
        
        batch_id = str(uuid.uuid4())
        if not batch_name:
            batch_name = f"Motivation Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create batch items
        items = []
        for i, theme in enumerate(themes):
            duration = durations[i] if i < len(durations) else durations[0]
            custom_script = custom_scripts[i] if custom_scripts and i < len(custom_scripts) else None
            
            item = BatchJobItem(
                id=str(uuid.uuid4()),
                type=VideoType.MOTIVATION,
                parameters={
                    'theme': theme,
                    'duration': duration,
                    'custom_script': custom_script
                },
                priority=1
            )
            items.append(item)
        
        # Create batch job
        batch_job = BatchJob(
            id=batch_id,
            name=batch_name,
            type=BatchJobType.MOTIVATION_BATCH,
            items=items,
            metadata={
                'themes_count': len(set(themes)),
                'total_duration': sum(durations),
                'has_custom_scripts': custom_scripts is not None
            }
        )
        
        return self._submit_batch_job(batch_job)
    
    def create_lofi_batch(self,
                         categories: List[str],
                         durations: List[int],
                         batch_name: str = None) -> str:
        """Create batch job for multiple lofi videos"""
        
        batch_id = str(uuid.uuid4())
        if not batch_name:
            batch_name = f"Lofi Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create batch items
        items = []
        for i, category in enumerate(categories):
            duration = durations[i] if i < len(durations) else durations[0]
            
            item = BatchJobItem(
                id=str(uuid.uuid4()),
                type=VideoType.LOFI,
                parameters={
                    'category': category,
                    'duration': duration
                },
                priority=1
            )
            items.append(item)
        
        # Create batch job
        batch_job = BatchJob(
            id=batch_id,
            name=batch_name,
            type=BatchJobType.LOFI_BATCH,
            items=items,
            metadata={
                'categories_count': len(set(categories)),
                'total_duration': sum(durations)
            }
        )
        
        return self._submit_batch_job(batch_job)
    
    def create_mixed_batch(self,
                          job_specs: List[Dict],
                          batch_name: str = None) -> str:
        """Create batch job with mixed video types"""
        
        batch_id = str(uuid.uuid4())
        if not batch_name:
            batch_name = f"Mixed Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create batch items from specifications
        items = []
        for spec in job_specs:
            video_type = VideoType(spec['type'])
            
            item = BatchJobItem(
                id=str(uuid.uuid4()),
                type=video_type,
                parameters=spec.get('parameters', {}),
                priority=spec.get('priority', 1)
            )
            items.append(item)
        
        # Sort by priority (higher priority first)
        items.sort(key=lambda x: x.priority, reverse=True)
        
        # Create batch job
        batch_job = BatchJob(
            id=batch_id,
            name=batch_name,
            type=BatchJobType.MIXED_BATCH,
            items=items,
            metadata={
                'motivation_count': sum(1 for item in items if item.type == VideoType.MOTIVATION),
                'lofi_count': sum(1 for item in items if item.type == VideoType.LOFI),
                'priority_distribution': self._calculate_priority_distribution(items)
            }
        )
        
        return self._submit_batch_job(batch_job)
    
    def create_scheduled_batch(self,
                              job_specs: List[Dict],
                              schedule_time: datetime,
                              batch_name: str = None) -> str:
        """Create scheduled batch job for future execution"""
        
        batch_id = str(uuid.uuid4())
        if not batch_name:
            batch_name = f"Scheduled Batch {schedule_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Create batch items
        items = []
        for spec in job_specs:
            video_type = VideoType(spec['type'])
            
            item = BatchJobItem(
                id=str(uuid.uuid4()),
                type=video_type,
                parameters=spec.get('parameters', {}),
                priority=spec.get('priority', 1)
            )
            items.append(item)
        
        # Create batch job
        batch_job = BatchJob(
            id=batch_id,
            name=batch_name,
            type=BatchJobType.SCHEDULED_BATCH,
            items=items,
            metadata={
                'schedule_time': schedule_time.isoformat(),
                'total_videos': len(items)
            }
        )
        
        # Store for scheduled execution
        self.job_history[batch_id] = batch_job
        
        # Schedule execution
        self._schedule_batch_execution(batch_job, schedule_time)
        
        return batch_id
    
    def _submit_batch_job(self, batch_job: BatchJob) -> str:
        """Submit batch job to processing queue"""
        self.job_history[batch_job.id] = batch_job
        self.stats['total_jobs'] += 1
        
        # Add to priority queue (negative priority for max-heap behavior)
        priority = max(item.priority for item in batch_job.items)
        self.job_queue.put((-priority, time.time(), batch_job))
        
        print(f"📋 Batch job submitted: {batch_job.name} ({batch_job.total_items} items)")
        
        return batch_job.id
    
    def _worker_thread(self, worker_id: int):
        """Worker thread for processing batch jobs"""
        print(f"👷 Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get next job from queue (timeout to check is_running)
                try:
                    priority, timestamp, batch_job = self.job_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the batch job
                self._process_batch_job(batch_job, worker_id)
                
                # Mark task as done
                self.job_queue.task_done()
                
            except Exception as e:
                print(f"❌ Worker {worker_id} error: {e}")
                continue
        
        print(f"👷 Worker {worker_id} stopped")
    
    def _process_batch_job(self, batch_job: BatchJob, worker_id: int):
        """Process a single batch job"""
        print(f"🔄 Worker {worker_id} processing: {batch_job.name}")
        
        # Update job status
        batch_job.status = BatchJobStatus.RUNNING
        batch_job.started_at = datetime.now()
        self.current_jobs[batch_job.id] = batch_job
        
        try:
            # Process each item in the batch
            for i, item in enumerate(batch_job.items):
                if not self.is_running:
                    batch_job.status = BatchJobStatus.CANCELLED
                    break
                
                try:
                    # Update item status
                    item.status = ProjectStatus.INITIALIZING
                    item.started_at = datetime.now()
                    
                    # Generate video based on type
                    if item.type == VideoType.MOTIVATION:
                        result = self.video_service.generate_motivation_video(
                            theme=item.parameters.get('theme'),
                            duration=item.parameters.get('duration', 60),
                            custom_script=item.parameters.get('custom_script')
                        )
                    elif item.type == VideoType.LOFI:
                        result = self.video_service.generate_lofi_video(
                            category=item.parameters.get('category'),
                            duration=item.parameters.get('duration', 120)
                        )
                    else:
                        raise Exception(f"Unknown video type: {item.type}")
                    
                    # Update item with results
                    item.status = ProjectStatus.COMPLETED
                    item.completed_at = datetime.now()
                    item.result = result
                    
                    batch_job.results.append(result)
                    batch_job.completed_items += 1
                    
                    print(f"✅ Worker {worker_id} completed item {i+1}/{batch_job.total_items}")
                    
                except Exception as e:
                    # Handle item failure
                    item.status = ProjectStatus.FAILED
                    item.error_message = str(e)
                    batch_job.failed_items += 1
                    
                    print(f"❌ Worker {worker_id} failed item {i+1}/{batch_job.total_items}: {e}")
                
                # Update progress
                batch_job.progress = int((i + 1) / batch_job.total_items * 100)
                
                # Call progress callback if registered
                if batch_job.id in self.job_callbacks:
                    try:
                        self.job_callbacks[batch_job.id](batch_job)
                    except Exception as e:
                        print(f"Callback error: {e}")
            
            # Mark batch as completed
            if batch_job.status != BatchJobStatus.CANCELLED:
                batch_job.status = BatchJobStatus.COMPLETED
                batch_job.completed_at = datetime.now()
                self.stats['completed_jobs'] += 1
                self.stats['total_videos_generated'] += batch_job.completed_items
            
            print(f"✅ Worker {worker_id} finished batch: {batch_job.name}")
            
        except Exception as e:
            # Handle batch failure
            batch_job.status = BatchJobStatus.FAILED
            batch_job.completed_at = datetime.now()
            self.stats['failed_jobs'] += 1
            
            print(f"❌ Worker {worker_id} batch failed: {batch_job.name} - {e}")
        
        finally:
            # Remove from current jobs
            if batch_job.id in self.current_jobs:
                del self.current_jobs[batch_job.id]
    
    def _schedule_batch_execution(self, batch_job: BatchJob, schedule_time: datetime):
        """Schedule batch job for future execution"""
        def scheduled_execution():
            # Wait until scheduled time
            now = datetime.now()
            if schedule_time > now:
                wait_seconds = (schedule_time - now).total_seconds()
                time.sleep(wait_seconds)
            
            # Submit to queue
            self._submit_batch_job(batch_job)
        
        # Start scheduling thread
        schedule_thread = threading.Thread(target=scheduled_execution)
        schedule_thread.daemon = True
        schedule_thread.start()
        
        print(f"⏰ Batch job scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _calculate_priority_distribution(self, items: List[BatchJobItem]) -> Dict[int, int]:
        """Calculate priority distribution for metadata"""
        distribution = {}
        for item in items:
            priority = item.priority
            distribution[priority] = distribution.get(priority, 0) + 1
        return distribution
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get status of a specific batch job"""
        if batch_id in self.job_history:
            batch_job = self.job_history[batch_id]
            
            return {
                'batch_id': batch_job.id,
                'name': batch_job.name,
                'type': batch_job.type.value,
                'status': batch_job.status.value,
                'progress': batch_job.progress,
                'total_items': batch_job.total_items,
                'completed_items': batch_job.completed_items,
                'failed_items': batch_job.failed_items,
                'created_at': batch_job.created_at.isoformat(),
                'started_at': batch_job.started_at.isoformat() if batch_job.started_at else None,
                'completed_at': batch_job.completed_at.isoformat() if batch_job.completed_at else None,
                'results': batch_job.results,
                'metadata': batch_job.metadata
            }
        
        return None
    
    def get_all_batches(self, status_filter: str = None) -> List[Dict]:
        """Get all batch jobs, optionally filtered by status"""
        batches = []
        
        for batch_job in self.job_history.values():
            if status_filter and batch_job.status.value != status_filter:
                continue
            
            batch_info = {
                'batch_id': batch_job.id,
                'name': batch_job.name,
                'type': batch_job.type.value,
                'status': batch_job.status.value,
                'progress': batch_job.progress,
                'total_items': batch_job.total_items,
                'completed_items': batch_job.completed_items,
                'failed_items': batch_job.failed_items,
                'created_at': batch_job.created_at.isoformat(),
                'started_at': batch_job.started_at.isoformat() if batch_job.started_at else None,
                'completed_at': batch_job.completed_at.isoformat() if batch_job.completed_at else None
            }
            batches.append(batch_info)
        
        # Sort by creation time (newest first)
        batches.sort(key=lambda x: x['created_at'], reverse=True)
        
        return batches
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch job"""
        if batch_id in self.job_history:
            batch_job = self.job_history[batch_id]
            
            if batch_job.status in [BatchJobStatus.PENDING, BatchJobStatus.RUNNING]:
                batch_job.status = BatchJobStatus.CANCELLED
                print(f"🚫 Batch job cancelled: {batch_job.name}")
                return True
        
        return False
    
    def register_progress_callback(self, batch_id: str, callback: Callable):
        """Register callback for batch progress updates"""
        self.job_callbacks[batch_id] = callback
    
    def get_processing_stats(self) -> Dict:
        """Get batch processing statistics"""
        current_time = datetime.now()
        uptime = (current_time - self.stats['start_time']).total_seconds()
        
        # Calculate average processing time
        if self.stats['completed_jobs'] > 0:
            avg_time = uptime / self.stats['completed_jobs']
        else:
            avg_time = 0
        
        return {
            'total_jobs': self.stats['total_jobs'],
            'completed_jobs': self.stats['completed_jobs'],
            'failed_jobs': self.stats['failed_jobs'],
            'success_rate': (self.stats['completed_jobs'] / max(self.stats['total_jobs'], 1)) * 100,
            'total_videos_generated': self.stats['total_videos_generated'],
            'current_running_jobs': len(self.current_jobs),
            'queue_size': self.job_queue.qsize(),
            'average_processing_time_minutes': round(avg_time / 60, 2),
            'uptime_hours': round(uptime / 3600, 2),
            'videos_per_hour': round(self.stats['total_videos_generated'] / max(uptime / 3600, 0.01), 2),
            'is_running': self.is_running,
            'max_concurrent_jobs': self.max_concurrent_jobs
        }
    
    def cleanup_old_batches(self, days_old: int = 7) -> int:
        """Clean up old batch job records"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            old_batches = []
            for batch_id, batch_job in self.job_history.items():
                if (batch_job.completed_at and batch_job.completed_at < cutoff_date) or \
                   (not batch_job.completed_at and batch_job.created_at < cutoff_date):
                    old_batches.append(batch_id)
            
            # Remove old batches
            for batch_id in old_batches:
                del self.job_history[batch_id]
                if batch_id in self.job_callbacks:
                    del self.job_callbacks[batch_id]
            
            print(f"✅ Cleaned up {len(old_batches)} old batch records")
            return len(old_batches)
            
        except Exception as e:
            print(f"Batch cleanup failed: {e}")
            return 0

# Test function
def test_batch_processor():
    """Test batch processor capabilities"""
    print("📋 Testing Batch Processor...")
    
    try:
        from .main_service import VideoGeneratorService
        
        # Mock video service for testing
        video_service = VideoGeneratorService()
        processor = BatchProcessor(video_service, max_concurrent_jobs=1)
        
        print("✅ Batch processor initialized")
        
        # Test stats
        stats = processor.get_processing_stats()
        print(f"Processing stats: {stats}")
        
        print("✅ Batch processor tests completed")
        
    except Exception as e:
        print(f"❌ Batch processor test failed: {e}")

if __name__ == "__main__":
    test_batch_processor()