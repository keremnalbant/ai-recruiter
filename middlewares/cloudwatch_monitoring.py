from datetime import datetime
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from utils.cloudwatch_metrics import CloudWatchMetrics, RequestTracker
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_monitoring(app: FastAPI) -> None:
    """Set up monitoring middlewares."""
    
    @app.middleware("http")
    async def monitor_requests(request: Request, call_next: Callable) -> Response:
        """Monitor request metrics using CloudWatch."""
        path = request.url.path
        
        try:
            with RequestTracker(path):
                response = await call_next(request)
                
                # Track response status
                status_code = response.status_code
                if 200 <= status_code < 300:
                    CloudWatchMetrics.track_github_request(path, "success")
                else:
                    CloudWatchMetrics.track_github_request(path, "error")
                
                return response
                
        except Exception as e:
            logger.exception(f"Request failed: {e}")
            CloudWatchMetrics.track_error(type(e).__name__, path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

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

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": getattr(settings, 'VERSION', 'unknown')
        }
