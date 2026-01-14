import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import colorlog

from src.config.settings import get_settings
from src.config.constants import (
    LOG_FORMAT_SIMPLE,
    LOG_FORMAT_DETAILED,
    LOG_DATE_FORMAT,
    LOG_FILE_MAX_SIZE,
    LOG_FILE_BACKUP_COUNT,
)


class ColoredFormatter(colorlog.ColoredFormatter):
    """Custom colored formatter with better styling."""
    
    COLORS = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    }
    
    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            log_colors=self.COLORS,
            secondary_log_colors={},
            reset=True,
        )


def setup_logger(
    name: str = "ai_browser_agent",
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance with both console and file handlers.
    
    Args:
        name: Logger name (default: "ai_browser_agent")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, uses settings.log_level
        log_format: Format type ("simple" or "detailed")
                   If None, uses settings.log_format
    
    Returns:
        Configured logger instance
    
    Example:
        logger = setup_logger("my_module")
        logger.info("Starting application")
    """
    settings = get_settings()
    
    # Use settings if not provided
    if log_level is None:
        log_level = settings.log_level
    if log_format is None:
        log_format = settings.log_format
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Choose format
    if log_format == "detailed":
        fmt = LOG_FORMAT_DETAILED
    else:
        fmt = LOG_FORMAT_SIMPLE
    
    # ========== Console Handler (with colors) ==========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = ColoredFormatter(
        fmt=fmt,
        datefmt=LOG_DATE_FORMAT,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ========== File Handler (rotating) ==========
    log_dir = settings.logs_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=LOG_FILE_MAX_SIZE,
        backupCount=LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = logging.Formatter(
        fmt=fmt,
        datefmt=LOG_DATE_FORMAT,
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger


# Create global logger instance
logger = setup_logger()


# ========== Convenience functions ==========

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def debug(msg: str, *args, **kwargs):
    """Log a DEBUG message."""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log an INFO message."""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log a WARNING message."""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, exc_info: bool = False, **kwargs):
    """Log an ERROR message."""
    logger.error(msg, *args, exc_info=exc_info, **kwargs)


def critical(msg: str, *args, exc_info: bool = False, **kwargs):
    """Log a CRITICAL message."""
    logger.critical(msg, *args, exc_info=exc_info, **kwargs)


if __name__ == "__main__":
    # Test logging
    debug("This is a DEBUG message")
    info("This is an INFO message")
    warning("This is a WARNING message")
    error("This is an ERROR message")
    critical("This is a CRITICAL message")
