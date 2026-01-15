"""Execute browser actions."""

import asyncio
import logging
from typing import Optional

from src.agent.action_types import ActionType, ActionDecision


logger = logging.getLogger(__name__)


class ActionExecutionError(Exception):
    """Action execution failed."""
    pass


class ElementNotFoundError(ActionExecutionError):
    """Target element not found."""
    pass


class ActionExecutor:
    """Execute actions on browser."""
    
    def __init__(self, browser):
        """Initialize executor with browser instance.
        
        Args:
            browser: AsyncBrowser instance from Phase 2
        """
        self.browser = browser
    
    async def execute(
        self,
        decision: ActionDecision,
        timeout: float = 10.0,
        auto_scroll: bool = True,
    ) -> bool:
        """Execute action from decision.
        
        Args:
            decision: ActionDecision with action and target
            timeout: Timeout in seconds
            auto_scroll: Auto-scroll element into view
            
        Returns:
            True if successful
            
        Raises:
            ActionExecutionError: If execution failed
        """
        
        logger.info(
            f"Executing: {decision.action.name} | "
            f"Target: {decision.target} | "
            f"Confidence: {decision.confidence:.2f}"
        )
        
        try:
            if decision.action == ActionType.CLICK:
                return await self.execute_click(
                    decision.target,
                    timeout=timeout,
                    auto_scroll=auto_scroll,
                )
            
            elif decision.action == ActionType.FILL:
                return await self.execute_fill(
                    decision.target,
                    decision.value or "",
                    timeout=timeout,
                    auto_scroll=auto_scroll,
                )
            
            elif decision.action == ActionType.SCROLL:
                return await self.execute_scroll(
                    decision.value or "down",
                    timeout=timeout,
                )
            
            elif decision.action == ActionType.WAIT:
                return await self.execute_wait(
                    float(decision.value or "2"),
                    timeout=timeout,
                )
            
            elif decision.action == ActionType.DONE:
                logger.info("Agent completed task (DONE action)")
                return True
            
            else:
                raise ActionExecutionError(
                    f"Unknown action: {decision.action}"
                )
        
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            raise
    
    async def execute_click(
        self,
        selector: str,
        timeout: float = 10.0,
        auto_scroll: bool = True,
    ) -> bool:
        """Click on element.
        
        Args:
            selector: CSS selector of element
            timeout: Timeout in seconds
            auto_scroll: Scroll element into view first
            
        Returns:
            True if successful
        """
        
        try:
            logger.debug(f"Click: {selector}")
            
            # Find element
            element = await asyncio.wait_for(
                self.browser.find(selector),
                timeout=timeout,
            )
            
            if not element:
                raise ElementNotFoundError(f"Element not found: {selector}")
            
            # Scroll into view if needed
            if auto_scroll:
                await element.scroll_into_view()
                await asyncio.sleep(0.2)
            
            # Click
            await asyncio.wait_for(
                element.click(),
                timeout=timeout,
            )
            
            logger.info(f"✓ Click successful: {selector}")
            return True
        
        except asyncio.TimeoutError:
            raise ActionExecutionError(f"Click timeout: {selector}")
        except Exception as e:
            raise ActionExecutionError(f"Click failed: {selector} - {e}")
    
    async def execute_fill(
        self,
        selector: str,
        value: str,
        timeout: float = 10.0,
        auto_scroll: bool = True,
    ) -> bool:
        """Fill form field.
        
        Args:
            selector: CSS selector of input field
            value: Value to fill
            timeout: Timeout in seconds
            auto_scroll: Scroll element into view first
            
        Returns:
            True if successful
        """
        
        try:
            logger.debug(f"Fill: {selector} = {value[:20]}...")
            
            # Find element
            element = await asyncio.wait_for(
                self.browser.find(selector),
                timeout=timeout,
            )
            
            if not element:
                raise ElementNotFoundError(f"Element not found: {selector}")
            
            # Scroll into view if needed
            if auto_scroll:
                await element.scroll_into_view()
                await asyncio.sleep(0.2)
            
            # Clear existing value
            await asyncio.wait_for(
                element.clear(),
                timeout=timeout,
            )
            
            # Fill with new value
            await asyncio.wait_for(
                element.fill(value),
                timeout=timeout,
            )
            
            logger.info(f"✓ Fill successful: {selector}")
            return True
        
        except asyncio.TimeoutError:
            raise ActionExecutionError(f"Fill timeout: {selector}")
        except Exception as e:
            raise ActionExecutionError(f"Fill failed: {selector} - {e}")
    
    async def execute_scroll(
        self,
        direction: str = "down",
        timeout: float = 10.0,
    ) -> bool:
        """Scroll page.
        
        Args:
            direction: "up", "down", or "left", "right"
            timeout: Timeout in seconds
            
        Returns:
            True if successful
        """
        
        try:
            logger.debug(f"Scroll: {direction}")
            
            # Determine scroll amount
            if direction.lower() in ["down", "right"]:
                x_delta, y_delta = 0, 500
            else:  # up, left
                x_delta, y_delta = 0, -500
            
            # Execute scroll
            await asyncio.wait_for(
                self.browser.scroll(x_delta, y_delta),
                timeout=timeout,
            )
            
            logger.info(f"✓ Scroll successful: {direction}")
            return True
        
        except asyncio.TimeoutError:
            raise ActionExecutionError(f"Scroll timeout")
        except Exception as e:
            raise ActionExecutionError(f"Scroll failed: {e}")
    
    async def execute_wait(
        self,
        duration: float = 2.0,
        timeout: float = 10.0,
    ) -> bool:
        """Wait for specified duration.
        
        Args:
            duration: Duration in seconds
            timeout: Timeout in seconds
            
        Returns:
            True (always succeeds)
        """
        
        try:
            logger.debug(f"Wait: {duration}s")
            
            # Clamp duration to reasonable range
            duration = max(0.1, min(duration, 60.0))
            
            await asyncio.wait_for(
                asyncio.sleep(duration),
                timeout=timeout,
            )
            
            logger.info(f"✓ Wait complete: {duration}s")
            return True
        
        except asyncio.TimeoutError:
            raise ActionExecutionError("Wait timeout")
        except Exception as e:
            raise ActionExecutionError(f"Wait failed: {e}")