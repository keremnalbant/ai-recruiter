from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.metrics import MetricUnit, Metrics
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# Type variables for generic functions
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# Initialize utilities
logger = Logger()
tracer = Tracer()
metrics = Metrics()

def create_response(
    status_code: int,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Create standardized Lambda response."""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': body
    }

def handle_exceptions(func: F) -> F:
    """Decorator to handle exceptions in Lambda functions."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}: {str(e)}")
            metrics.add_metric(
                name="LambdaErrors",
                unit=MetricUnit.Count,
                value=1
            )
            return create_response(
                status_code=500,
                body={'error': str(e), 'type': type(e).__name__}
            )
    return cast(F, wrapper)

def validate_input(required_fields: Dict[str, type]) -> Callable[[F], F]:
    """Decorator to validate Lambda function input."""
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(event: Dict[str, Any], context: LambdaContext) -> Any:
            try:
                if 'body' in event:
                    body = event['body']
                    for field, field_type in required_fields.items():
                        if field not in body:
                            raise ValueError(f"Missing required field: {field}")
                        if not isinstance(body[field], field_type):
                            raise TypeError(
                                f"Field {field} must be of type {field_type.__name__}"
                            )
                return await func(event, context)
            except (ValueError, TypeError) as e:
                logger.warning(f"Input validation failed: {str(e)}")
                return create_response(
                    status_code=400,
                    body={'error': str(e)}
                )
        return cast(F, wrapper)
    return decorator

def add_timestamp() -> str:
    """Add ISO 8601 timestamp with timezone."""
    return datetime.now(timezone.utc).isoformat()

def add_tracing_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Add X-Ray tracing headers to response."""
    trace_id = tracer.get_trace_id()
    if trace_id:
        headers['X-Amzn-Trace-Id'] = trace_id
    return headers

def metric_wrapper(name: str) -> Callable[[F], F]:
    """Decorator to add metrics to Lambda functions."""
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                metrics.add_metric(
                    name=f"{name}Success",
                    unit=MetricUnit.Count,
                    value=1
                )
                return result
            except Exception:
                metrics.add_metric(
                    name=f"{name}Error",
                    unit=MetricUnit.Count,
                    value=1
                )
                raise
            finally:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                metrics.add_metric(
                    name=f"{name}Duration",
                    unit=MetricUnit.Milliseconds,
                    value=duration
                )
        return cast(F, wrapper)
    return decorator

def log_event(func: F) -> F:
    """Decorator to log Lambda event details."""
    @wraps(func)
    async def wrapper(event: Dict[str, Any], context: LambdaContext) -> Any:
        logger.info(
            "Lambda invocation",
            extra={
                'function_name': context.function_name,
                'aws_request_id': context.aws_request_id,
                'event_type': event.get('type', 'unknown'),
                'timestamp': add_timestamp()
            }
        )
        return await func(event, context)
    return cast(F, wrapper)
