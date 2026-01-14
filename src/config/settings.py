import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """
    Application settings loaded from .env file with validation and defaults.
    
    All settings are type-safe and validated by Pydantic.
    """
    
    # ========== ANTHROPIC API ==========
    anthropic_api_key: str = ""  # Required, must be set in .env
    
    # ========== MODEL CONFIGURATION ==========
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7
    
    # ========== BROWSER SETTINGS ==========
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False  # Set to True for CI/CD
    browser_timeout: int = 30000  # milliseconds
    browser_launch_args: list[str] = []
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 720
    browser_headless: bool = True
    browser_max_retries: int = 3
    browser_retry_delay: float = 2.0
    browser_user_agent: str = (  # ADD THIS
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    # ========== AGENT SETTINGS ==========
    max_iterations: int = 20  # Max tool-use loop iterations
    context_window_size: int = 4000  # Tokens for context management
    request_timeout: int = 60  # seconds
    
    # ========== LOGGING ==========
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "detailed"  # simple, detailed
    debug: bool = False
    
    # ========== FEATURE FLAGS ==========
    enable_screenshot_capture: bool = True
    enable_page_analysis: bool = True
    enable_error_recovery: bool = True
    cache_page_analysis: bool = True
    
    # ========== PATHS ==========
    project_root: Path = Path(__file__).parent.parent.parent
    screenshots_dir: Path = Path(__file__).parent.parent.parent / "screenshots"
    logs_dir: Path = Path(__file__).parent.parent.parent / "logs"
    
    # ========== PERFORMANCE ==========
    network_idle_timeout: int = 5000  # Wait for network idle (ms)
    page_load_timeout: int = 30000  # Page load timeout (ms)
    element_interaction_delay: int = 100  # Delay before interaction (ms)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )
    
    
    def __init__(self, **data):
        super().__init__(**data)
        # Validate required fields
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in .env file. "
                "Copy .env.example to .env and add your API key."
            )
        # Create necessary directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# Singleton instance
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global Settings instance.
    
    Usage:
        from src.config.settings import get_settings
        settings = get_settings()
        print(settings.llm_name)
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# Create default instance for direct imports
settings = get_settings()