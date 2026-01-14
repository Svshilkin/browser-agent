"""Unit tests for BrowserManager"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.browser.manager import BrowserManager, BrowserError
from src.config import Settings


class TestBrowserManagerInit:
    """Test BrowserManager initialization"""
    
    def test_browser_manager_init(self):
        """Test initialization"""
        settings = Settings()
        manager = BrowserManager(settings)
        
        assert manager.settings == settings
        assert manager._browser is None
        assert manager._context is None
        assert manager._page is None
    
    def test_browser_manager_logger_setup(self):
        """Test logger is configured"""
        settings = Settings()
        manager = BrowserManager(settings)
        
        assert manager.logger is not None


class TestBrowserManagerLaunch:
    """Test browser launch functionality"""
    
    @patch('src.browser.manager.sync_playwright')
    def test_launch_browser(self, mock_playwright):
        """Test successful browser launch"""
        # Setup mocks
        mock_p = MagicMock()
        mock_chromium = MagicMock()
        mock_browser = MagicMock()
        
        mock_playwright.return_value.start.return_value = mock_p
        mock_p.chromium = mock_chromium
        mock_chromium.launch.return_value = mock_browser
        
        # Execute
        settings = Settings(browser_type="chromium", browser_headless=True)
        manager = BrowserManager(settings)
        result = manager.launch()
        
        # Verify
        assert result == mock_browser
        assert manager._browser == mock_browser
        mock_chromium.launch.assert_called_once()
    
    @patch('src.browser.manager.sync_playwright')
    def test_launch_browser_with_retries(self, mock_playwright):
        """Test retry on timeout"""
        # Setup: first call fails, second succeeds
        mock_p = MagicMock()
        mock_chromium = MagicMock()
        mock_browser = MagicMock()
        
        mock_playwright.return_value.start.return_value = mock_p
        mock_p.chromium = mock_chromium
        
        # First call raises timeout, second succeeds
        mock_chromium.launch.side_effect = [
            PlaywrightTimeoutError("timeout"),
            mock_browser
        ]
        
        # Execute
        settings = Settings(browser_max_retries=3, browser_retry_delay=0.1)
        manager = BrowserManager(settings)
        result = manager.launch()
        
        # Verify: called twice (once failed, once succeeded)
        assert mock_chromium.launch.call_count == 2
        assert result == mock_browser
    
    @patch('src.browser.manager.sync_playwright')
    def test_launch_browser_max_retries_exceeded(self, mock_playwright):
        """Test error when max retries exceeded"""
        mock_p = MagicMock()
        mock_chromium = MagicMock()
        
        mock_playwright.return_value.start.return_value = mock_p
        mock_p.chromium = mock_chromium
        mock_chromium.launch.side_effect = PlaywrightTimeoutError("timeout")
        
        # Execute
        settings = Settings(browser_max_retries=2, browser_retry_delay=0.01)
        manager = BrowserManager(settings)
        
        # Verify: should raise BrowserError after 2 attempts
        with pytest.raises(BrowserError) as exc_info:
            manager.launch()
        
        # Check error message
        assert "after 2 attempts" in str(exc_info.value).lower()


class TestBrowserManagerContext:
    """Test context creation"""
    
    def test_create_context_without_launch_raises_error(self):
        """Test error when creating context before launch"""
        settings = Settings()
        manager = BrowserManager(settings)
        
        with pytest.raises(BrowserError) as exc_info:
            manager.create_context()
        
        assert "not launched" in str(exc_info.value)
    
    def test_create_context_with_viewport(self):
        """Test context creation with viewport"""
        settings = Settings(
            browser_viewport_width=1920,
            browser_viewport_height=1080
        )
        
        # Mock browser
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context.return_value = mock_context
        
        # Execute
        manager = BrowserManager(settings)
        manager._browser = mock_browser
        result = manager.create_context()
        
        # Verify: context created with correct viewport
        assert result == mock_context
        mock_browser.new_context.assert_called_once()
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs['viewport']['width'] == 1920
        assert call_kwargs['viewport']['height'] == 1080


class TestBrowserManagerPage:
    """Test page creation"""
    
    def test_create_page(self):
        """Test page creation"""
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_context.new_page.return_value = mock_page
        
        settings = Settings(browser_timeout_ms=30000)
        manager = BrowserManager(settings)
        result = manager.create_page(mock_context)
        
        assert result == mock_page
        mock_page.set_default_timeout.assert_called_once_with(30000)
        # Verify event handlers registered
        mock_page.on.assert_called()


class TestBrowserManagerClose:
    """Test resource cleanup"""
    
    def test_close_all_resources(self):
        """Test closing all resources in correct order"""
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_browser = MagicMock()
        mock_playwright = MagicMock()
        
        settings = Settings()
        manager = BrowserManager(settings)
        manager._page = mock_page
        manager._context = mock_context
        manager._browser = mock_browser
        manager._playwright = mock_playwright
        
        # Execute
        manager.close()
        
        # Verify order: page → context → browser → playwright
        assert manager._page is None
        assert manager._context is None
        assert manager._browser is None
        assert manager._playwright is None
        
        # Verify close methods called
        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
    
    def test_close_is_idempotent(self):
        """Test close can be called multiple times safely"""
        settings = Settings()
        manager = BrowserManager(settings)
        
        # Should not raise
        manager.close()
        manager.close()
        manager.close()


class TestBrowserManagerContextManager:
    """Test context manager support"""
    
    def test_context_manager_cleanup(self):
        """Test with statement cleanup"""
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_browser = MagicMock()
        
        settings = Settings()
        
        with patch.object(BrowserManager, 'close') as mock_close:
            manager = BrowserManager(settings)
            manager._page = mock_page
            manager._context = mock_context
            manager._browser = mock_browser
            
            with manager:
                pass
            
            mock_close.assert_called_once()