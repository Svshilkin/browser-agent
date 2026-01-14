"""Browser lifecycle management with Playwright sync API"""

from typing import Optional
import time
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright.sync_api import TimeoutError, Error as PlaywrightError

from src.config import Settings
from src.utils import get_logger

logger = get_logger(__name__)


class BrowserError(Exception):
    """Custom exception for browser-related errors"""
    pass


class BrowserManager:
    """
    Manages Playwright browser lifecycle.
    
    Features:
    - Launch browser with retry logic (exponential backoff)
    - Create isolated contexts for session management
    - Create pages with default error handlers
    - Graceful resource cleanup
    - Full error handling and logging
    
    Example:
        settings = Settings()
        manager = BrowserManager(settings)
        browser = manager.launch()
        context = manager.create_context()
        page = manager.create_page(context)
        
        try:
            page.goto("https://example.com")
        finally:
            manager.close()
    """
    
    def __init__(self, settings: Settings):
        """Initialize BrowserManager with configuration"""
        self.settings = settings
        self.logger = logger
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
        self.logger.info("BrowserManager initialized")
    
    def launch(self) -> Browser:
        """
        Launch browser with retry logic.
        
        Retries on TimeoutError with exponential backoff:
        - Attempt 1: immediate
        - Attempt 2: wait 2s
        - Attempt 3: wait 4s
        
        Returns:
            Browser: Playwright browser instance
            
        Raises:
            BrowserError: If all retries exhausted
        """
        max_retries = getattr(self.settings, 'browser_max_retries', 3)
        base_delay = getattr(self.settings, 'browser_retry_delay', 2)
        
        self.logger.info(
            f"Launching browser ({self.settings.browser_type}) "
            f"headless={self.settings.browser_headless}"
        )
        
        for attempt in range(max_retries):
            try:
                # Start playwright context
                self._playwright = sync_playwright().start()
                self.logger.debug("Playwright started")
                
                # Get browser type (chromium, firefox, webkit)
                browser_type = getattr(
                    self._playwright, 
                    self.settings.browser_type
                )
                
                # Launch browser
                self._browser = browser_type.launch(
                    headless=self.settings.browser_headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                    ]
                )
                
                self.logger.info(
                    f"Browser launched successfully "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                return self._browser
                
            except TimeoutError as e:
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"Failed to launch browser after {max_retries} retries"
                    )
                    raise BrowserError(
                        f"Browser launch timeout after {max_retries} attempts"
                    ) from e
                
                delay = base_delay * (2 ** attempt)  # exponential backoff
                self.logger.warning(
                    f"Browser launch timeout (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay}s..."
                )
                time.sleep(delay)
                
            except PlaywrightError as e:
                self.logger.error(f"Playwright error during launch: {e}")
                raise BrowserError(f"Failed to launch browser: {e}") from e
            
            except Exception as e:
                self.logger.error(f"Unexpected error during browser launch: {e}")
                raise BrowserError(f"Unexpected error: {e}") from e
        
        # Should not reach here
        raise BrowserError("Browser launch failed")
    
    def create_context(self, **kwargs) -> BrowserContext:
        """
        Create isolated browser context.
        
        Context provides:
        - Session isolation (separate cookies/storage)
        - Viewport configuration
        - User agent
        - Locale/timezone
        
        Args:
            **kwargs: Additional context options (viewport, locale, etc.)
            
        Returns:
            BrowserContext: Isolated browser context
            
        Raises:
            BrowserError: If browser not launched
        """
        if self._browser is None:
            raise BrowserError("Browser not launched. Call launch() first.")
        
        try:
            # Default context options
            context_options = {
                "viewport": {
                    "width": self.settings.browser_viewport_width,
                    "height": self.settings.browser_viewport_height,
                },
                "user_agent": self.settings.browser_user_agent,
            }
            
            # Override with kwargs
            context_options.update(kwargs)
            
            self._context = self._browser.new_context(**context_options)
            
            self.logger.info(
                f"Browser context created: "
                f"{self.settings.browser_viewport_width}x"
                f"{self.settings.browser_viewport_height}"
            )
            return self._context
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to create browser context: {e}")
            raise BrowserError(f"Failed to create context: {e}") from e
    
    def create_page(self, context: BrowserContext) -> Page:
        """
        Create page in context with default handlers.
        
        Sets up:
        - Page timeout from settings
        - Console message logging
        - Error/rejection logging
        
        Args:
            context: BrowserContext to create page in
            
        Returns:
            Page: Playwright page instance
            
        Raises:
            BrowserError: If context invalid
        """
        try:
            self._page = context.new_page()
            
            # Set default timeout
            self._page.set_default_timeout(self.settings.browser_timeout)
            
            # Log console messages
            self._page.on("console", self._on_console)
            
            # Log page errors
            self._page.on("pageerror", self._on_page_error)
            
            # Log request failures
            self._page.on("requestfailed", self._on_request_failed)
            
            self.logger.info("Page created and configured")
            return self._page
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to create page: {e}")
            raise BrowserError(f"Failed to create page: {e}") from e
    
    def close(self) -> None:
        """
        Close all resources in correct order: page → context → browser.
        
        Safe to call multiple times (idempotent).
        """
        errors = []
        
        # Close page
        if self._page is not None:
            try:
                self._page.close()
                self.logger.debug("Page closed")
                self._page = None
            except Exception as e:
                self.logger.warning(f"Error closing page: {e}")
                errors.append(e)
        
        # Close context
        if self._context is not None:
            try:
                self._context.close()
                self.logger.debug("Browser context closed")
                self._context = None
            except Exception as e:
                self.logger.warning(f"Error closing context: {e}")
                errors.append(e)
        
        # Close browser
        if self._browser is not None:
            try:
                self._browser.close()
                self.logger.debug("Browser closed")
                self._browser = None
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
                errors.append(e)
        
        # Stop playwright
        if self._playwright is not None:
            try:
                self._playwright.stop()
                self.logger.debug("Playwright stopped")
                self._playwright = None
            except Exception as e:
                self.logger.warning(f"Error stopping playwright: {e}")
                errors.append(e)
        
        if not errors:
            self.logger.info("All resources closed successfully")
        else:
            self.logger.warning(f"Closed with {len(errors)} error(s)")
    
    # Event handlers
    
    def _on_console(self, msg) -> None:
        """Handle page console messages"""
        self.logger.debug(f"[CONSOLE {msg.type}] {msg.text}")
    
    def _on_page_error(self, exc) -> None:
        """Handle page errors"""
        self.logger.error(f"[PAGE ERROR] {exc}")
    
    def _on_request_failed(self, request) -> None:
        """Handle failed requests"""
        self.logger.warning(f"[REQUEST FAILED] {request.url}")
    
    # Context manager support
    
    def __enter__(self):
        """Support with statement"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup on context exit"""
        self.close()
        return False