from datetime import datetime
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.registry import CollectorRegistry

# Create a custom registry
REGISTRY = CollectorRegistry()

# Define metrics
github_requests = Counter(
    'github_api_requests_total',
    'Total GitHub API requests',
    ['endpoint', 'status'],
    registry=REGISTRY
)

linkedin_requests = Counter(
    'linkedin_scraper_requests_total',
    'Total LinkedIn scraping requests',
    ['status'],
    registry=REGISTRY
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['endpoint'],
    registry=REGISTRY
)

active_requests = Gauge(
    'active_requests',
    'Number of requests currently being processed',
    registry=REGISTRY
)

error_counter = Counter(
    'errors_total',
    'Total number of errors',
    ['type', 'agent'],
    registry=REGISTRY
)

profile_stats = Summary(
    'profile_processing_stats',
    'Statistics about profile processing',
    ['type'],
    registry=REGISTRY
)

rate_limit_remaining = Gauge(
    'rate_limit_remaining',
    'Remaining API rate limit',
    ['service'],
    registry=REGISTRY
)


class MetricsCollector:
    """Collect and manage application metrics."""

    @staticmethod
    def track_github_request(endpoint: str, status: str) -> None:
        """Track GitHub API request."""
        github_requests.labels(endpoint=endpoint, status=status).inc()

    @staticmethod
    def track_linkedin_request(status: str) -> None:
        """Track LinkedIn scraping request."""
        linkedin_requests.labels(status=status).inc()

    @staticmethod
    def track_request_duration(endpoint: str, duration: float) -> None:
        """Track request duration."""
        request_duration.labels(endpoint=endpoint).observe(duration)

    @staticmethod
    def update_active_requests(delta: int = 1) -> None:
        """Update number of active requests."""
        active_requests.inc(delta)

    @staticmethod
    def track_error(error_type: str, agent: str) -> None:
        """Track error occurrence."""
        error_counter.labels(type=error_type, agent=agent).inc()

    @staticmethod
    def track_profile_processing(profile_type: str, duration: float) -> None:
        """Track profile processing statistics."""
        profile_stats.labels(type=profile_type).observe(duration)

    @staticmethod
    def update_rate_limit(service: str, remaining: int) -> None:
        """Update rate limit metrics."""
        rate_limit_remaining.labels(service=service).set(remaining)


class RequestTracker:
    """Track individual request metrics."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> 'RequestTracker':
        self.start_time = datetime.now()
        MetricsCollector.update_active_requests(1)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            MetricsCollector.track_request_duration(self.endpoint, duration)
        MetricsCollector.update_active_requests(-1)
        
        if exc_type:
            MetricsCollector.track_error(
                error_type=exc_type.__name__,
                agent=self.endpoint
            )


def get_metrics() -> Dict[str, Any]:
    """Get current metrics as a dictionary."""
    return {
        'active_requests': active_requests._value.get(),
        'github_requests': {
            'total': sum(github_requests._metrics.values()),
            'success': github_requests.labels(endpoint='all', status='success')._value.get(),
            'error': github_requests.labels(endpoint='all', status='error')._value.get()
        },
        'linkedin_requests': {
            'total': sum(linkedin_requests._metrics.values()),
            'success': linkedin_requests.labels(status='success')._value.get(),
            'error': linkedin_requests.labels(status='error')._value.get()
        },
        'rate_limits': {
            'github': rate_limit_remaining.labels(service='github')._value.get(),
            'linkedin': rate_limit_remaining.labels(service='linkedin')._value.get()
        }
    }
