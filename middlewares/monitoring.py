from datetime import datetime
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from limits import RateLimitItem, storage
from limits.storage import StorageRegistry
from limits.strategies import MovingWindowRateLimiter
from prometheus_client import generate_latest

from config import settings
from utils.logger import get_logger
from utils.monitoring import MetricsCollector, RequestTracker

logger = get_logger(__name__)

# Initialize rate limiter
storage = StorageRegistry.get_storage_class("redis")(
    uri=settings.REDIS_URL
) if hasattr(settings, 'REDIS_URL') else StorageRegistry.get_storage_class("memory")()

limiter = MovingWindowRateLimiter(storage)

# Define rate limits
RATE_LIMITS = {
    "/recruit": RateLimitItem(60, 60),  # 60 requests per minute
    "/studio/": RateLimitItem(300, 60),  # 300 requests per minute
}


def setup_monitoring(app: FastAPI) -> None:
    """Set up monitoring middlewares."""
    
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next: Callable) -> Response:
        """Monitor request metrics and handle rate limiting."""
        path = request.url.path
        
        # Check rate limit
        for route_prefix, limit in RATE_LIMITS.items():
            if path.startswith(route_prefix):
                identifier = f"{request.client.host}:{path}"
                if not limiter.hit(limit, identifier):
                    logger.warning(f"Rate limit exceeded for {identifier}")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests. Please try again later.",
                            "retry_after": limiter.get_window_stats(limit, identifier)[1]
                        }
                    )
        
        # Track request metrics
        start_time = datetime.now()
        
        try:
            with RequestTracker(path):
                response = await call_next(request)
                
                # Track response status
                status_code = response.status_code
                if 200 <= status_code < 300:
                    MetricsCollector.track_github_request(path, "success")
                else:
                    MetricsCollector.track_github_request(path, "error")
                
                return response
                
        except Exception as e:
            logger.exception(f"Request failed: {e}")
            MetricsCollector.track_error(type(e).__name__, path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        finally:
            # Track request duration
            duration = (datetime.now() - start_time).total_seconds()
            MetricsCollector.track_request_duration(path, duration)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable) -> Response:
        """Add security headers to responses."""
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics."""
        return Response(
            generate_latest(),
            media_type="text/plain"
        )

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": getattr(settings, 'VERSION', 'unknown'),
            "rate_limits": {
                route: limiter.get_window_stats(limit, "global")
                for route, limit in RATE_LIMITS.items()
            }
        }
