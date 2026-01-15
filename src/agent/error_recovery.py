"""Error recovery and resilience system."""

import asyncio
import logging
import random
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict
from datetime import datetime

from src.agent.action_types import ActionDecision, ActionType


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur during automation."""
    
    ELEMENT_NOT_FOUND = "element_not_found"
    TIMEOUT = "timeout"
    NAVIGATION_FAILED = "navigation_failed"
    INVALID_ACTION = "invalid_action"
    API_ERROR = "api_error"
    BROWSER_ERROR = "browser_error"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Strategies for recovering from errors."""
    
    RETRY_SAME = "retry_same"
    SCROLL_AND_RETRY = "scroll_and_retry"
    WAIT_AND_RETRY = "wait_and_retry"
    NAVIGATE_BACK = "navigate_back"
    SKIP_ACTION = "skip_action"
    ABORT_TASK = "abort_task"
    HUMAN_INTERVENTION = "human"


class ElementNotFoundError(Exception):
    """Element not found on page."""
    pass


class NavigationError(Exception):
    """Navigation failed."""
    pass


class BrowserError(Exception):
    """Browser operation failed."""
    pass


class APIError(Exception):
    """API call failed."""
    pass


@dataclass
class ErrorContext:
    """Information about an error."""
    
    error_type: ErrorType = ErrorType.UNKNOWN
    message: str = ""
    traceback: Optional[str] = None
    action: Optional[ActionDecision] = None
    state_snapshot: Optional[Dict] = None
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    recovery_strategy: Optional[RecoveryStrategy] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "retry_count": self.retry_count,
            "strategy": (
                self.recovery_strategy.value
                if self.recovery_strategy
                else None
            ),
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
        }


@dataclass
class RecoveryAction:
    """Action to take to recover from error."""
    
    strategy: RecoveryStrategy
    can_recover: bool
    retry_count: int = 0
    reason: str = ""
    fallback_action: Optional[ActionDecision] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "strategy": self.strategy.value,
            "can_recover": self.can_recover,
            "retry_count": self.retry_count,
            "reason": self.reason,
        }


@dataclass
class ErrorMetrics:
    """Metrics about errors and recovery."""
    
    total_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    recovery_attempts: int = 0
    recovery_success_count: int = 0
    total_recovery_time_ms: float = 0.0
    fallback_count: int = 0
    failed_recoveries: int = 0
    
    def record_error(self, error_type: ErrorType, strategy: RecoveryStrategy):
        """Record an error."""
        self.total_errors += 1
        
        type_name = error_type.name
        current_count = self.errors_by_type.get(type_name, 0)
        self.errors_by_type[type_name] = current_count + 1
        
        if strategy != RecoveryStrategy.ABORT_TASK:
            self.recovery_attempts += 1
    
    def record_recovery_success(self, recovery_time_ms: float):
        """Record successful recovery."""
        self.recovery_success_count += 1
        self.total_recovery_time_ms += recovery_time_ms
    
    def record_recovery_failure(self):
        """Record failed recovery."""
        self.failed_recoveries += 1
    
    @property
    def recovery_success_rate(self) -> float:
        """Get success rate of recovery attempts."""
        if self.recovery_attempts == 0:
            return 1.0
        return self.recovery_success_count / self.recovery_attempts
    
    @property
    def avg_recovery_time_ms(self) -> float:
        """Get average recovery time."""
        if self.recovery_success_count == 0:
            return 0.0
        return self.total_recovery_time_ms / self.recovery_success_count
    
    def to_dict(self):
        """Convert metrics to dictionary."""
        return {
            "total_errors": self.total_errors,
            "errors_by_type": self.errors_by_type,
            "recovery_attempts": self.recovery_attempts,
            "recovery_success_count": self.recovery_success_count,
            "failed_recoveries": self.failed_recoveries,
            "success_rate": round(self.recovery_success_rate, 2),
            "avg_recovery_time_ms": round(self.avg_recovery_time_ms, 2),
            "fallback_count": self.fallback_count,
        }


class RetryStrategy:
    """Exponential backoff retry logic."""
    
    def __init__(
        self,
        initial_delay: float = 0.1,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry strategy.
        
        Args:
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add randomization to delay
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_wait_time(self, retry_count: int) -> float:
        """Get wait time for retry.
        
        Args:
            retry_count: Number of retries so far
            
        Returns:
            Wait time in seconds
        """
        # Exponential backoff: initial * (base ^ retry_count)
        wait_time = self.initial_delay * (self.exponential_base ** retry_count)
        
        # Cap at max_delay
        wait_time = min(wait_time, self.max_delay)
        
        # Add jitter (±20%)
        if self.jitter:
            jitter_amount = wait_time * 0.2
            wait_time += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, wait_time)  # Ensure non-negative


class ErrorRecoveryHandler:
    """Handle errors and recover from them."""
    
    def __init__(
        self,
        browser=None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ):
        """Initialize recovery handler.
        
        Args:
            browser: AsyncBrowser instance
            max_retries: Maximum retries per error
            timeout: Timeout for recovery operations
        """
        self.browser = browser
        self.max_retries = max_retries
        self.timeout = timeout
        self.metrics = ErrorMetrics()
        self.retry_strategy = RetryStrategy()
    
    async def handle_error(
        self,
        error: Exception,
        action: Optional[ActionDecision] = None,
        context: Optional[ErrorContext] = None,
    ) -> RecoveryAction:
        """Handle an error and return recovery action.
        
        Args:
            error: The exception that occurred
            action: The action that failed
            context: Error context (optional)
            
        Returns:
            RecoveryAction with strategy and recovery details
        """
        
        start_time = time.time()
        
        # Create or update context
        if context is None:
            context = ErrorContext()
        
        context.message = str(error)
        context.traceback = traceback.format_exc()
        context.action = action
        context.timestamp = time.time()
        
        try:
            # 1. Classify error
            error_type = self._classify_error(error)
            context.error_type = error_type
            logger.debug(f"Classified error: {error_type.value}")
            
            # 2. Find recovery strategy
            strategy = self._find_recovery_strategy(
                error_type=error_type,
                context=context,
            )
            context.recovery_strategy = strategy
            logger.debug(f"Recovery strategy: {strategy.value}")
            
            # 3. Check if recoverable
            if strategy == RecoveryStrategy.ABORT_TASK:
                logger.error(f"Error is unrecoverable: {error}")
                
                self.metrics.record_error(error_type, strategy)
                self.metrics.record_recovery_failure()
                
                return RecoveryAction(
                    strategy=strategy,
                    can_recover=False,
                    retry_count=context.retry_count,
                    reason="Unrecoverable error type",
                )
            
            # 4. Check max retries
            if context.retry_count >= self.max_retries:
                logger.warning(
                    f"Max retries exceeded ({self.max_retries})"
                )
                
                self.metrics.record_error(error_type, RecoveryStrategy.ABORT_TASK)
                self.metrics.record_recovery_failure()
                
                return RecoveryAction(
                    strategy=RecoveryStrategy.ABORT_TASK,
                    can_recover=False,
                    retry_count=context.retry_count,
                    reason=f"Max retries exceeded ({self.max_retries})",
                )
            
            # 5. Execute recovery
            try:
                await self._execute_recovery(strategy, context)
            except Exception as recovery_error:
                logger.error(f"Recovery execution failed: {recovery_error}")
                self.metrics.record_recovery_failure()
                
                return RecoveryAction(
                    strategy=RecoveryStrategy.ABORT_TASK,
                    can_recover=False,
                    retry_count=context.retry_count,
                    reason=f"Recovery execution failed: {str(recovery_error)}",
                )
            
            # 6. Record metrics
            recovery_time_ms = (time.time() - start_time) * 1000
            self.metrics.record_error(error_type, strategy)
            self.metrics.record_recovery_success(recovery_time_ms)
            
            logger.info(
                f"✓ Recovery successful ({recovery_time_ms:.0f}ms): {strategy.value}"
            )
            
            return RecoveryAction(
                strategy=strategy,
                can_recover=True,
                retry_count=context.retry_count + 1,
                reason="Recovery executed successfully",
            )
        
        except Exception as e:
            logger.error(f"Fatal error in recovery handler: {e}")
            self.metrics.record_recovery_failure()
            
            return RecoveryAction(
                strategy=RecoveryStrategy.ABORT_TASK,
                can_recover=False,
                retry_count=context.retry_count,
                reason=f"Recovery handler error: {str(e)}",
            )
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type.
        
        Args:
            error: The exception
            
        Returns:
            ErrorType
        """
        
        error_str = str(error).lower()
        
        if isinstance(error, ElementNotFoundError):
            return ErrorType.ELEMENT_NOT_FOUND
        elif isinstance(error, asyncio.TimeoutError):
            return ErrorType.TIMEOUT
        elif "timeout" in error_str:
            return ErrorType.TIMEOUT
        elif isinstance(error, NavigationError):
            return ErrorType.NAVIGATION_FAILED
        elif "navigation" in error_str or "navigate" in error_str:
            return ErrorType.NAVIGATION_FAILED
        elif isinstance(error, APIError):
            return ErrorType.API_ERROR
        elif "api" in error_str or "network" in error_str:
            return ErrorType.API_ERROR
        elif isinstance(error, BrowserError):
            return ErrorType.BROWSER_ERROR
        elif "browser" in error_str or "chromium" in error_str:
            return ErrorType.BROWSER_ERROR
        else:
            return ErrorType.UNKNOWN
    
    def _find_recovery_strategy(
        self,
        error_type: ErrorType,
        context: ErrorContext,
    ) -> RecoveryStrategy:
        """Find best recovery strategy for error.
        
        Args:
            error_type: Type of error
            context: Error context
            
        Returns:
            RecoveryStrategy
        """
        
        # Max retries check
        if context.retry_count >= self.max_retries:
            return RecoveryStrategy.ABORT_TASK
        
        # Error-specific strategies
        if error_type == ErrorType.ELEMENT_NOT_FOUND:
            if context.retry_count == 0:
                return RecoveryStrategy.SCROLL_AND_RETRY
            elif context.retry_count == 1:
                return RecoveryStrategy.WAIT_AND_RETRY
            else:
                return RecoveryStrategy.SKIP_ACTION
        
        elif error_type == ErrorType.TIMEOUT:
            if context.retry_count < 2:
                return RecoveryStrategy.WAIT_AND_RETRY
            else:
                return RecoveryStrategy.SKIP_ACTION
        
        elif error_type == ErrorType.API_ERROR:
            # API errors often recover with wait
            return RecoveryStrategy.WAIT_AND_RETRY
        
        elif error_type == ErrorType.NAVIGATION_FAILED:
            return RecoveryStrategy.NAVIGATE_BACK
        
        elif error_type == ErrorType.BROWSER_ERROR:
            return RecoveryStrategy.RETRY_SAME
        
        elif error_type == ErrorType.INVALID_ACTION:
            return RecoveryStrategy.SKIP_ACTION
        
        else:
            return RecoveryStrategy.RETRY_SAME
    
    async def _execute_recovery(
        self,
        strategy: RecoveryStrategy,
        context: ErrorContext,
    ):
        """Execute recovery strategy.
        
        Args:
            strategy: Recovery strategy
            context: Error context
        """
        
        try:
            if strategy == RecoveryStrategy.RETRY_SAME:
                # Just retry immediately
                await asyncio.sleep(0.1)
                logger.debug("Recovery: retry immediately")
            
            elif strategy == RecoveryStrategy.SCROLL_AND_RETRY:
                # Scroll to try to find element
                if self.browser:
                    await asyncio.wait_for(
                        self.browser.scroll(0, 300),
                        timeout=self.timeout,
                    )
                await asyncio.sleep(0.5)
                logger.debug("Recovery: scrolled and waiting")
            
            elif strategy == RecoveryStrategy.WAIT_AND_RETRY:
                # Wait for page to stabilize (exponential backoff)
                wait_time = self.retry_strategy.get_wait_time(context.retry_count)
                logger.debug(f"Recovery: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            
            elif strategy == RecoveryStrategy.NAVIGATE_BACK:
                # Go back in browser history
                if self.browser:
                    await asyncio.wait_for(
                        self.browser.go_back(),
                        timeout=self.timeout,
                    )
                await asyncio.sleep(1.0)
                logger.debug("Recovery: navigated back")
            
            elif strategy == RecoveryStrategy.SKIP_ACTION:
                # Just skip this action
                logger.debug("Recovery: skipping action")
        
        except asyncio.TimeoutError:
            logger.warning("Recovery action timed out")
            raise Exception("Recovery timeout")
        except Exception as e:
            logger.error(f"Recovery execution error: {e}")
            raise