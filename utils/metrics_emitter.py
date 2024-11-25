from datetime import datetime
from typing import Any, Dict, List, Optional

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics(namespace="GitHubLinkedInAnalyzer")

class MetricsEmitter:
    """Emit custom CloudWatch metrics with standardized dimensions."""
    
    def __init__(self, service: str):
        self.service = service
        self.default_dimensions = {
            "Service": service,
            "Environment": self._get_environment()
        }
    
    def _get_environment(self) -> str:
        """Get current environment from Lambda function name."""
        import os
        function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
        if "-prod-" in function_name:
            return "production"
        elif "-dev-" in function_name:
            return "development"
        return "unknown"

    def add_metric(
        self,
        name: str,
        value: float,
        unit: MetricUnit,
        dimensions: Optional[Dict[str, str]] = None
    ) -> None:
        """Add metric with default dimensions."""
        try:
            all_dimensions = self.default_dimensions.copy()
            if dimensions:
                all_dimensions.update(dimensions)
                
            metrics.add_metric(
                name=name,
                value=value,
                unit=unit,
                dimensions=all_dimensions
            )
            logger.debug(f"Added metric: {name}={value} {unit}")
        except Exception as e:
            logger.error(f"Failed to add metric {name}: {e}")

    def track_duration(
        self,
        operation: str,
        duration: float,
        resource: Optional[str] = None
    ) -> None:
        """Track operation duration."""
        dimensions = {"Operation": operation}
        if resource:
            dimensions["Resource"] = resource
            
        self.add_metric(
            name="OperationDuration",
            value=duration,
            unit=MetricUnit.Milliseconds,
            dimensions=dimensions
        )

    def track_success(
        self,
        operation: str,
        resource: Optional[str] = None
    ) -> None:
        """Track successful operation."""
        dimensions = {"Operation": operation}
        if resource:
            dimensions["Resource"] = resource
            
        self.add_metric(
            name="SuccessfulOperations",
            value=1,
            unit=MetricUnit.Count,
            dimensions=dimensions
        )

    def track_error(
        self,
        operation: str,
        error_type: str,
        resource: Optional[str] = None
    ) -> None:
        """Track operation error."""
        dimensions = {
            "Operation": operation,
            "ErrorType": error_type
        }
        if resource:
            dimensions["Resource"] = resource
            
        self.add_metric(
            name="OperationErrors",
            value=1,
            unit=MetricUnit.Count,
            dimensions=dimensions
        )

    def track_cache(
        self,
        hit: bool,
        cache_type: str
    ) -> None:
        """Track cache hit/miss."""
        self.add_metric(
            name="CacheHits" if hit else "CacheMisses",
            value=1,
            unit=MetricUnit.Count,
            dimensions={"CacheType": cache_type}
        )

    def track_rate_limit(
        self,
        service: str,
        remaining: int
    ) -> None:
        """Track remaining rate limit."""
        self.add_metric(
            name="RateLimitRemaining",
            value=remaining,
            unit=MetricUnit.Count,
            dimensions={"LimitedService": service}
        )

    def track_batch_operation(
        self,
        operation: str,
        total: int,
        successful: int,
        resource: Optional[str] = None
    ) -> None:
        """Track batch operation results."""
        dimensions = {"Operation": operation}
        if resource:
            dimensions["Resource"] = resource
            
        self.add_metric(
            name="BatchOperationTotal",
            value=total,
            unit=MetricUnit.Count,
            dimensions=dimensions
        )
        
        self.add_metric(
            name="BatchOperationSuccessful",
            value=successful,
            unit=MetricUnit.Count,
            dimensions=dimensions
        )
        
        if total > 0:
            success_rate = (successful / total) * 100
            self.add_metric(
                name="BatchOperationSuccessRate",
                value=success_rate,
                unit=MetricUnit.Percent,
                dimensions=dimensions
            )

    def track_memory_usage(
        self,
        used_mb: float
    ) -> None:
        """Track Lambda memory usage."""
        import os
        import psutil
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        self.add_metric(
            name="MemoryUsed",
            value=used_mb,
            unit=MetricUnit.Megabytes
        )
        
        # Calculate usage percentage
        memory_limit = int(os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", 0))
        if memory_limit > 0:
            usage_percent = (used_mb / memory_limit) * 100
            self.add_metric(
                name="MemoryUtilization",
                value=usage_percent,
                unit=MetricUnit.Percent
            )

    def track_cold_start(self) -> None:
        """Track Lambda cold start."""
        self.add_metric(
            name="ColdStarts",
            value=1,
            unit=MetricUnit.Count
        )
