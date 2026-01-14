"""
Configuration Package
Settings, constants, and configuration management
"""

from .settings import Settings, get_settings
from .constants import (
    # Timeouts
    BROWSER_LAUNCH_TIMEOUT,
    PAGE_LOAD_TIMEOUT,
    TOOL_EXECUTION_TIMEOUT,
    # LLM
    MAX_TOOL_USE_ITERATIONS,
)

__all__ = [
    "Settings",
    "get_settings",
    "BROWSER_LAUNCH_TIMEOUT",
    "PAGE_LOAD_TIMEOUT",
    "TOOL_EXECUTION_TIMEOUT",
    "MAX_TOOL_USE_ITERATIONS",
]
