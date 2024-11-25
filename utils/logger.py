import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging and redirect to loguru.
    
    This allows us to capture logs from libraries that use standard logging
    and route them through loguru for consistent formatting.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    *,
    log_file: Optional[Path] = None,
    level: str = "INFO",
    rotation: str = "20 MB",
    retention: str = "1 month",
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
) -> None:
    """
    Configure logging with loguru.
    
    Args:
        log_file: Path to log file. If None, logs only to console.
        level: Minimum log level to display.
        rotation: When to rotate log files (size or time).
        retention: How long to keep log files.
        format: Log message format.
    """
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        level=level,
        format=format,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file logger if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level=level,
            format=format,
            rotation=rotation,
            retention=retention,
            compression="zip",
            backtrace=True,
            diagnose=True,
        )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # List of standard loggers to capture
    loggers = [
        "uvicorn",
        "uvicorn.error",
        "fastapi",
        "aiohttp",
        "selenium",
        "motor",
    ]
    
    # Redirect standard loggers to loguru
    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]


def get_request_id() -> str:
    """Generate a unique request ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


class RequestContextFilter:
    """Add context information to log records."""
    
    def __init__(self):
        self.request_id = None
    
    def filter(self, record):
        record["request_id"] = self.request_id or get_request_id()
        return True


def get_logger(name: str) -> logger:
    """Get a logger instance with the given name."""
    return logger.bind(name=name)
