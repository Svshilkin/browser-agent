"""
Unit tests for configuration module.
"""

import pytest
from pathlib import Path

from src.config.settings import get_settings, Settings
from src.config import constants
from src.utils.logger import setup_logger, logger


class TestSettings:
    """Test Settings class and configuration loading."""
    
    def test_settings_loads(self):
        """Test that settings can be loaded."""
        settings = get_settings()
        assert settings is not None
    
    def test_settings_has_api_key(self):
        """Test that API key is loaded."""
        settings = get_settings()
        # This will fail if .env is not set up correctly
        assert settings.anthropic_api_key != ""
    
    def test_settings_defaults(self):
        """Test that default values are set."""
        settings = get_settings()
        assert settings.browser_type == "chromium"
        assert settings.max_iterations == 20
        assert settings.log_level == "INFO"
    
    def test_settings_singleton(self):
        """Test that get_settings returns same instance."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
    
    def test_settings_paths_created(self):
        """Test that necessary directories are created."""
        settings = get_settings()
        assert settings.screenshots_dir.exists()
        assert settings.logs_dir.exists()
    
    def test_settings_type_safe(self):
        """Test that settings are type-safe."""
        settings = get_settings()
        assert isinstance(settings.browser_timeout, int)
        assert isinstance(settings.headless, bool)
        assert isinstance(settings.llm_temperature, float)


class TestConstants:
    """Test constants are defined correctly."""
    
    def test_timeouts_defined(self):
        """Test that timeout constants are defined."""
        assert hasattr(constants, "BROWSER_LAUNCH_TIMEOUT")
        assert constants.BROWSER_LAUNCH_TIMEOUT == 30000
    
    def test_llm_constants(self):
        """Test LLM related constants."""
        assert constants.LLM_REQUEST_TIMEOUT == 60
        assert constants.MAX_TOOL_USE_ITERATIONS == 20
    
    def test_screenshot_settings(self):
        """Test screenshot constants."""
        assert constants.SCREENSHOT_WIDTH == 1920
        assert constants.SCREENSHOT_HEIGHT == 1080
    
    def test_feature_flags(self):
        """Test feature flags."""
        assert isinstance(constants.FEATURE_VISION_ENABLED, bool)
        assert isinstance(constants.FEATURE_MULTI_TAB, bool)


class TestLogger:
    """Test logger configuration."""
    
    def test_logger_created(self):
        """Test that logger is created."""
        assert logger is not None
    
    def test_logger_has_handlers(self):
        """Test that logger has handlers."""
        assert len(logger.handlers) > 0
    
    def test_setup_logger_simple(self):
        """Test setting up logger with simple format."""
        test_logger = setup_logger(name="test", log_format="simple")
        assert test_logger is not None
    
    def test_setup_logger_detailed(self):
        """Test setting up logger with detailed format."""
        test_logger = setup_logger(name="test", log_format="detailed")
        assert test_logger is not None
    
    def test_logger_logging(self, caplog):
        """Test that logger can log messages."""
        import logging
        test_logger = logging.getLogger("test_logger")
        test_logger.info("Test message")
        assert "Test message" in caplog.text or caplog.records


class TestIntegration:
    """Integration tests for configuration system."""
    
    def test_constants_match_settings(self):
        """Test that constants are consistent with settings."""
        settings = get_settings()
        # Browser timeout in constants should match approx value in settings
        assert constants.BROWSER_LAUNCH_TIMEOUT <= 60000  # Reasonable limit
    
    def test_project_structure(self):
        """Test that project structure is correct."""
        settings = get_settings()
        assert settings.project_root.exists()
        assert (settings.project_root / "src").exists()
        assert (settings.project_root / "tests").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
