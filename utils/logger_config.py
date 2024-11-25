from functools import wraps
from typing import Any, Callable, Dict, Optional

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize powertools
logger = Logger(service="github-linkedin-analyzer")
metrics = Metrics(namespace="GitHubLinkedInAnalyzer")
tracer = Tracer()

def inject_lambda_context(
    lambda_handler: Callable[[Dict[str, Any], LambdaContext], Any]
) -> Callable[[Dict[str, Any], LambdaContext], Any]:
    """Decorator to inject lambda context into logger."""
    @wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: LambdaContext) -> Any:
        # Extract correlation ID from event
        correlation_id = event.get("requestContext", {}).get("requestId")
        if correlation_id:
            logger.set_correlation_id(correlation_id)

        # Add lambda context
        logger.append_keys(
            lambda_function_name=context.function_name,
            lambda_function_memory=context.memory_limit_in_mb,
            lambda_function_arn=context.invoked_function_arn,
            lambda_request_id=context.aws_request_id,
        )

        return lambda_handler(event, context)
    return wrapper

def log_metrics(
    lambda_handler: Callable[[Dict[str, Any], LambdaContext], Any]
) -> Callable[[Dict[str, Any], LambdaContext], Any]:
    """Decorator to add metrics to lambda execution."""
    @wraps(lambda_handler)
    def wrapper(event: Dict[str, Any], context: LambdaContext) -> Any:
        try:
            metrics.add_metric(
                name="LambdaInvocations",
                unit=MetricUnit.Count,
                value=1
            )
            return lambda_handler(event, context)
        except Exception as e:
            metrics.add_metric(
                name="LambdaErrors",
                unit=MetricUnit.Count,
                value=1
            )
            raise
        finally:
            metrics.flush_metrics()
    return wrapper

def add_logging(
    level: str = "INFO",
    sample_rate: float = 0.1,
    lambda_handler: Optional[bool] = True
) -> Callable:
    """Decorator to add logging to functions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Add correlation ID if available
            if 'correlation_id' in kwargs:
                logger.set_correlation_id(kwargs['correlation_id'])

            # Add custom context
            logger.append_keys(
                function_name=func.__name__,
                args=str(args),
                kwargs=str(kwargs)
            )

            try:
                logger.debug(f"Executing {func.__name__}")
                result = await func(*args, **kwargs)
                logger.debug(f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logger.exception(
                    f"Error executing {func.__name__}",
                    exc_info=e
                )
                raise
            finally:
                logger.remove_keys(["function_name", "args", "kwargs"])

        if lambda_handler:
            wrapper = inject_lambda_context(wrapper)
            wrapper = log_metrics(wrapper)
            wrapper = tracer.capture_lambda_handler(capture_response=True)(wrapper)

        return wrapper
    return decorator

def setup_logging(correlation_id: Optional[str] = None) -> None:
    """Configure logging for the application."""
    if correlation_id:
        logger.set_correlation_id(correlation_id)

    # Add default keys
    logger.append_keys(
        service="github-linkedin-analyzer",
        environment=getattr(tracer, "service_env", "unknown"),
        logger_version="1.0.0"
    )

class RequestLogger:
    """Context manager for request logging."""
    
    def __init__(self, request_type: str, **kwargs: Any):
        self.request_type = request_type
        self.context = kwargs
        self.start_time: Optional[float] = None

    async def __aenter__(self) -> 'RequestLogger':
        self.start_time = tracer.get_current_event()
        logger.info(
            f"Starting {self.request_type} request",
            extra=self.context
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            logger.error(
                f"Error in {self.request_type} request",
                exc_info=exc_val,
                extra=self.context
            )
        else:
            logger.info(
                f"Completed {self.request_type} request",
                extra=self.context
            )

        # Add duration metric
        if self.start_time:
            duration = tracer.get_current_event() - self.start_time
            metrics.add_metric(
                name=f"{self.request_type}Duration",
                unit=MetricUnit.Milliseconds,
                value=duration * 1000
            )
