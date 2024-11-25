import time
from datetime import datetime
from typing import Dict, List

from prometheus_client import start_http_server, Gauge, Counter, Summary
from rq import Queue, Worker
from rq.job import Job, JobStatus

from config import settings
from utils.logger import get_logger
from utils.queue import redis_conn

logger = get_logger(__name__)

# Prometheus metrics
QUEUE_SIZE = Gauge('rq_queue_size', 'Number of jobs in queue', ['queue_name'])
QUEUE_LATENCY = Gauge('rq_queue_latency_seconds', 'Queue processing latency in seconds', ['queue_name'])
WORKER_COUNT = Gauge('rq_worker_count', 'Number of workers', ['queue_name'])
PROCESSED_JOBS = Counter('rq_processed_jobs_total', 'Total number of processed jobs', ['queue_name', 'status'])
JOB_DURATION = Summary('rq_job_duration_seconds', 'Job processing duration in seconds', ['queue_name'])

class QueueMonitor:
    """Monitor RQ queues and expose metrics."""

    def __init__(self, queues: List[str] = ['high', 'default', 'low']):
        self.queues = {
            name: Queue(name, connection=redis_conn)
            for name in queues
        }
        self.last_check = datetime.now()

    def update_queue_metrics(self) -> None:
        """Update queue-related metrics."""
        for queue_name, queue in self.queues.items():
            # Queue size
            QUEUE_SIZE.labels(queue_name=queue_name).set(len(queue))

            # Worker count
            workers = Worker.all(queue=queue)
            WORKER_COUNT.labels(queue_name=queue_name).set(len(workers))

            # Process completed jobs
            completed_jobs = queue.finished_job_registry.get_job_ids()
            failed_jobs = queue.failed_job_registry.get_job_ids()

            PROCESSED_JOBS.labels(queue_name=queue_name, status='completed').inc(len(completed_jobs))
            PROCESSED_JOBS.labels(queue_name=queue_name, status='failed').inc(len(failed_jobs))

            # Calculate queue latency
            if queue.jobs:
                oldest_job = queue.jobs[0]
                latency = (datetime.now() - oldest_job.enqueued_at).total_seconds()
                QUEUE_LATENCY.labels(queue_name=queue_name).set(latency)

    def update_job_metrics(self) -> None:
        """Update job-related metrics."""
        for queue_name, queue in self.queues.items():
            # Get jobs that completed since last check
            registry = queue.finished_job_registry
            jobs = [Job.fetch(job_id, connection=redis_conn) for job_id in registry.get_job_ids()]
            
            for job in jobs:
                if job.ended_at and job.started_at:
                    duration = (job.ended_at - job.started_at).total_seconds()
                    JOB_DURATION.labels(queue_name=queue_name).observe(duration)

    def check_worker_health(self) -> Dict[str, List[str]]:
        """Check health of workers and return any issues."""
        issues = {queue_name: [] for queue_name in self.queues}
        
        for queue_name, queue in self.queues.items():
            workers = Worker.all(queue=queue)
            
            for worker in workers:
                # Check if worker is busy too long
                if worker.state == 'busy':
                    if worker.current_job:
                        job_duration = (datetime.now() - worker.current_job.started_at).total_seconds()
                        if job_duration > settings.JOB_TIMEOUT:
                            issues[queue_name].append(
                                f"Worker {worker.name} stuck on job {worker.current_job.id} "
                                f"for {job_duration} seconds"
                            )
                
                # Check last heartbeat
                last_heartbeat = worker.last_heartbeat
                if last_heartbeat:
                    heartbeat_age = (datetime.now() - last_heartbeat).total_seconds()
                    if heartbeat_age > 300:  # 5 minutes
                        issues[queue_name].append(
                            f"Worker {worker.name} hasn't sent heartbeat for {heartbeat_age} seconds"
                        )
        
        return issues

    def monitor(self) -> None:
        """Main monitoring loop."""
        try:
            # Start Prometheus server
            start_http_server(9090)
            logger.info("Queue monitor started on port 9090")

            while True:
                try:
                    self.update_queue_metrics()
                    self.update_job_metrics()
                    
                    # Check worker health every minute
                    if (datetime.now() - self.last_check).total_seconds() > 60:
                        issues = self.check_worker_health()
                        for queue_name, queue_issues in issues.items():
                            for issue in queue_issues:
                                logger.warning(f"Queue {queue_name}: {issue}")
                        self.last_check = datetime.now()
                    
                    time.sleep(15)  # Update every 15 seconds
                
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(5)  # Back off on error
        
        except Exception as e:
            logger.error(f"Fatal error in queue monitor: {e}")
            raise

if __name__ == "__main__":
    monitor = QueueMonitor()
    monitor.monitor()
