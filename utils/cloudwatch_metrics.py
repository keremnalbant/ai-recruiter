import logging
from datetime import datetime
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Initialize CloudWatch client
cloudwatch = boto3.client('cloudwatch')

class CloudWatchMetrics:
    """Collect and manage application metrics using CloudWatch."""
    
    NAMESPACE = "GitHubLinkedInAnalyzer"

    @staticmethod
    def track_github_request(endpoint: str, status: str) -> None:
        """Track GitHub API request."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'GitHubAPIRequests',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint},
                        {'Name': 'Status', 'Value': status}
                    ]
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track GitHub request: {e}")

    @staticmethod
    def track_linkedin_request(status: str) -> None:
        """Track LinkedIn scraping request."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'LinkedInRequests',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Status', 'Value': status}
                    ]
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track LinkedIn request: {e}")

    @staticmethod
    def track_request_duration(endpoint: str, duration: float) -> None:
        """Track request duration."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'RequestDuration',
                    'Value': duration,
                    'Unit': 'Seconds',
                    'Dimensions': [
                        {'Name': 'Endpoint', 'Value': endpoint}
                    ]
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track duration: {e}")

    @staticmethod
    def track_active_requests(count: int) -> None:
        """Track number of active requests."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'ActiveRequests',
                    'Value': count,
                    'Unit': 'Count'
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track active requests: {e}")

    @staticmethod
    def track_error(error_type: str, agent: str) -> None:
        """Track error occurrence."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'Errors',
                    'Value': 1,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'ErrorType', 'Value': error_type},
                        {'Name': 'Agent', 'Value': agent}
                    ]
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track error: {e}")

    @staticmethod
    def track_rate_limit(service: str, remaining: int) -> None:
        """Track remaining rate limit."""
        try:
            cloudwatch.put_metric_data(
                Namespace=CloudWatchMetrics.NAMESPACE,
                MetricData=[{
                    'MetricName': 'RateLimitRemaining',
                    'Value': remaining,
                    'Unit': 'Count',
                    'Dimensions': [
                        {'Name': 'Service', 'Value': service}
                    ]
                }]
            )
        except ClientError as e:
            logger.error(f"Failed to track rate limit: {e}")


class RequestTracker:
    """Track individual request metrics."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time: Optional[datetime] = None

    def __enter__(self) -> 'RequestTracker':
        self.start_time = datetime.now()
        CloudWatchMetrics.track_active_requests(1)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            CloudWatchMetrics.track_request_duration(self.endpoint, duration)
        CloudWatchMetrics.track_active_requests(-1)
        
        if exc_type:
            CloudWatchMetrics.track_error(
                error_type=exc_type.__name__,
                agent=self.endpoint
            )
