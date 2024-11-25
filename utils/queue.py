from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

import redis
from rq import Queue, Worker
from rq.decorators import job
from rq.job import Job
from rq.registry import FinishedJobRegistry, FailedJobRegistry

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Redis connection
redis_conn = redis.Redis(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=getattr(settings, 'REDIS_DB', 0),
    password=getattr(settings, 'REDIS_PASSWORD', None),
    decode_responses=True
)

# Create queues with different priorities
high_queue = Queue('high', connection=redis_conn)
default_queue = Queue('default', connection=redis_conn)
low_queue = Queue('low', connection=redis_conn)

# Job status tracking
JOB_TIMEOUT = 3600  # 1 hour
JOB_RESULT_TTL = 86400  # 24 hours


class JobManager:
    """Manage background jobs."""

    @staticmethod
    def enqueue_job(
        func: Any,
        *args: Any,
        priority: str = 'default',
        job_id: Optional[str] = None,
        **kwargs: Any
    ) -> Job:
        """Enqueue a job with specified priority."""
        queue = {
            'high': high_queue,
            'default': default_queue,
            'low': low_queue
        }.get(priority, default_queue)

        job_id = job_id or f"job_{uuid4()}"
        job_timeout = kwargs.pop('timeout', JOB_TIMEOUT)
        result_ttl = kwargs.pop('result_ttl', JOB_RESULT_TTL)

        job = queue.enqueue(
            func,
            *args,
            job_id=job_id,
            timeout=job_timeout,
            result_ttl=result_ttl,
            **kwargs
        )
        
        logger.info(f"Enqueued job {job_id} with priority {priority}")
        return job

    @staticmethod
    def get_job_status(job_id: str) -> Dict[str, Any]:
        """Get detailed job status."""
        job = Job.fetch(job_id, connection=redis_conn)
        
        status = {
            "id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "exc_info": job.exc_info,
            "meta": job.meta
        }

        if job.is_finished:
            status["result"] = job.result
        
        return status

    @staticmethod
    def cancel_job(job_id: str) -> bool:
        """Cancel a job if it hasn't started."""
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            if job.get_status() == 'queued':
                job.cancel()
                return True
        except Exception as e:
            logger.error(f"Error canceling job {job_id}: {e}")
        return False

    @staticmethod
    def get_queue_info() -> Dict[str, Any]:
        """Get information about all queues."""
        queues = {
            'high': high_queue,
            'default': default_queue,
            'low': low_queue
        }
        
        info = {}
        for name, queue in queues.items():
            finished_registry = FinishedJobRegistry(queue=queue)
            failed_registry = FailedJobRegistry(queue=queue)
            
            info[name] = {
                'queued': len(queue),
                'finished': len(finished_registry),
                'failed': len(failed_registry),
                'workers': len(Worker.all(queue=queue))
            }
        
        return info

    @staticmethod
    def clean_old_jobs(days: int = 7) -> int:
        """Clean up old job data."""
        threshold = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for queue in [high_queue, default_queue, low_queue]:
            registry = FinishedJobRegistry(queue=queue)
            for job_id in registry.get_job_ids():
                try:
                    job = Job.fetch(job_id, connection=redis_conn)
                    if job.ended_at and job.ended_at < threshold:
                        job.delete()
                        cleaned += 1
                except Exception as e:
                    logger.error(f"Error cleaning job {job_id}: {e}")
        
        return cleaned


# Decorator for creating background jobs
def background_task(
    queue: str = 'default',
    timeout: int = JOB_TIMEOUT,
    result_ttl: int = JOB_RESULT_TTL
) -> Any:
    """Decorator to mark a function as a background task."""
    def decorator(func: Any) -> Any:
        @job(queue, connection=redis_conn, timeout=timeout, result_ttl=result_ttl)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapped
    return decorator
