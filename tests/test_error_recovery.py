"""Tests for Phase 6: Error Recovery."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from src.agent.error_recovery import (
    ErrorType,
    RecoveryStrategy,
    ErrorContext,
    RecoveryAction,
    ErrorMetrics,
    RetryStrategy,
    ErrorRecoveryHandler,
    ElementNotFoundError,
    NavigationError,
    BrowserError,
    APIError,
)


@pytest.fixture
def mock_browser():
    """Mock browser instance."""
    browser = AsyncMock()
    browser.scroll = AsyncMock()
    browser.go_back = AsyncMock()
    return browser


@pytest.fixture
def recovery_handler(mock_browser):
    """Error recovery handler."""
    return ErrorRecoveryHandler(
        browser=mock_browser,
        max_retries=3,
        timeout=10.0,
    )


class TestErrorType:
    """Test ErrorType enum."""
    
    def test_error_types_exist(self):
        """Test all error types exist."""
        assert ErrorType.ELEMENT_NOT_FOUND
        assert ErrorType.TIMEOUT
        assert ErrorType.NAVIGATION_FAILED
        assert ErrorType.INVALID_ACTION
        assert ErrorType.API_ERROR
        assert ErrorType.BROWSER_ERROR
        assert ErrorType.UNKNOWN
    
    def test_error_type_value(self):
        """Test error type values."""
        assert ErrorType.ELEMENT_NOT_FOUND.value == "element_not_found"
        assert ErrorType.TIMEOUT.value == "timeout"
    
    def test_recovery_strategy_types(self):
        """Test recovery strategy types."""
        assert RecoveryStrategy.RETRY_SAME
        assert RecoveryStrategy.SCROLL_AND_RETRY
        assert RecoveryStrategy.WAIT_AND_RETRY


class TestErrorContext:
    """Test ErrorContext."""
    
    def test_context_creation(self):
        """Test creating error context."""
        context = ErrorContext(
            error_type=ErrorType.ELEMENT_NOT_FOUND,
            message="Element #email not found",
            retry_count=1,
        )
        
        assert context.error_type == ErrorType.ELEMENT_NOT_FOUND
        assert context.message == "Element #email not found"
        assert context.retry_count == 1
    
    def test_context_to_dict(self):
        """Test converting context to dict."""
        context = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            message="Action timed out",
            retry_count=2,
        )
        
        result = context.to_dict()
        assert result["error_type"] == "timeout"
        assert result["message"] == "Action timed out"
        assert result["retry_count"] == 2


class TestRecoveryAction:
    """Test RecoveryAction."""
    
    def test_recovery_action_success(self):
        """Test successful recovery action."""
        action = RecoveryAction(
            strategy=RecoveryStrategy.RETRY_SAME,
            can_recover=True,
            retry_count=1,
        )
        
        assert action.can_recover == True
        assert action.retry_count == 1
    
    def test_recovery_action_failure(self):
        """Test failed recovery action."""
        action = RecoveryAction(
            strategy=RecoveryStrategy.ABORT_TASK,
            can_recover=False,
            reason="Unrecoverable error",
        )
        
        assert action.can_recover == False
        assert "Unrecoverable" in action.reason


class TestErrorMetrics:
    """Test ErrorMetrics."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = ErrorMetrics()
        assert metrics.total_errors == 0
        assert metrics.recovery_attempts == 0
        assert metrics.recovery_success_count == 0
    
    def test_record_error(self):
        """Test recording error."""
        metrics = ErrorMetrics()
        
        metrics.record_error(
            ErrorType.ELEMENT_NOT_FOUND,
            RecoveryStrategy.SCROLL_AND_RETRY,
        )
        
        assert metrics.total_errors == 1
        assert metrics.recovery_attempts == 1
    
    def test_recovery_success_rate(self):
        """Test recovery success rate calculation."""
        metrics = ErrorMetrics()
        
        metrics.record_error(
            ErrorType.TIMEOUT,
            RecoveryStrategy.WAIT_AND_RETRY,
        )
        metrics.record_recovery_success(100.0)
        
        assert metrics.recovery_success_rate == 1.0
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dict."""
        metrics = ErrorMetrics()
        metrics.total_errors = 5
        metrics.recovery_success_count = 4
        
        result = metrics.to_dict()
        assert result["total_errors"] == 5
        assert result["recovery_success_count"] == 4


class TestRetryStrategy:
    """Test RetryStrategy."""
    
    def test_initial_delay(self):
        """Test initial delay."""
        strategy = RetryStrategy(initial_delay=0.1)
        wait_time = strategy.get_wait_time(0)
        
        # Should be close to 0.1 (with jitter)
        assert 0.05 < wait_time < 0.15
    
    def test_exponential_backoff(self):
        """Test exponential backoff."""
        strategy = RetryStrategy(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        
        # Retry 0: 1.0
        # Retry 1: 2.0
        # Retry 2: 4.0
        assert strategy.get_wait_time(0) == 1.0
        assert strategy.get_wait_time(1) == 2.0
        assert strategy.get_wait_time(2) == 4.0
    
    def test_max_delay_cap(self):
        """Test max delay cap."""
        strategy = RetryStrategy(
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=False,
        )
        
        # Should cap at 10.0
        wait_time = strategy.get_wait_time(10)  # 1.0 * 2^10 = 1024.0
        assert wait_time <= 10.0


class TestErrorRecoveryHandler:
    """Test ErrorRecoveryHandler."""
    
    def test_handler_initialization(self, recovery_handler):
        """Test handler initialization."""
        assert recovery_handler.max_retries == 3
        assert recovery_handler.timeout == 10.0
        assert recovery_handler.metrics is not None
    
    def test_classify_element_not_found(self, recovery_handler):
        """Test classifying element not found error."""
        error = ElementNotFoundError("Element #email not found")
        
        error_type = recovery_handler._classify_error(error)
        assert error_type == ErrorType.ELEMENT_NOT_FOUND
    
    def test_classify_timeout_error(self, recovery_handler):
        """Test classifying timeout error."""
        error = asyncio.TimeoutError()
        
        error_type = recovery_handler._classify_error(error)
        assert error_type == ErrorType.TIMEOUT
    
    def test_classify_navigation_error(self, recovery_handler):
        """Test classifying navigation error."""
        error = NavigationError("Failed to navigate")
        
        error_type = recovery_handler._classify_error(error)
        assert error_type == ErrorType.NAVIGATION_FAILED
    
    def test_classify_api_error(self, recovery_handler):
        """Test classifying API error."""
        error = APIError("API request failed")
        
        error_type = recovery_handler._classify_error(error)
        assert error_type == ErrorType.API_ERROR
    
    def test_classify_browser_error(self, recovery_handler):
        """Test classifying browser error."""
        error = BrowserError("Browser operation failed")
        
        error_type = recovery_handler._classify_error(error)
        assert error_type == ErrorType.BROWSER_ERROR
    
    def test_strategy_element_not_found_first_retry(self, recovery_handler):
        """Test strategy for element not found (first retry)."""
        context = ErrorContext(
            error_type=ErrorType.ELEMENT_NOT_FOUND,
            retry_count=0,
        )
        
        strategy = recovery_handler._find_recovery_strategy(
            ErrorType.ELEMENT_NOT_FOUND,
            context,
        )
        
        assert strategy == RecoveryStrategy.SCROLL_AND_RETRY
    
    def test_strategy_timeout_retry(self, recovery_handler):
        """Test strategy for timeout."""
        context = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            retry_count=0,
        )
        
        strategy = recovery_handler._find_recovery_strategy(
            ErrorType.TIMEOUT,
            context,
        )
        
        assert strategy == RecoveryStrategy.WAIT_AND_RETRY
    
    def test_strategy_max_retries_exceeded(self, recovery_handler):
        """Test strategy when max retries exceeded."""
        context = ErrorContext(
            error_type=ErrorType.TIMEOUT,
            retry_count=5,  # > max_retries (3)
        )
        
        strategy = recovery_handler._find_recovery_strategy(
            ErrorType.TIMEOUT,
            context,
        )
        
        assert strategy == RecoveryStrategy.ABORT_TASK
    
    @pytest.mark.asyncio
    async def test_handle_error_element_not_found(self, recovery_handler):
        """Test handling element not found error."""
        error = ElementNotFoundError("Element not found")
        
        result = await recovery_handler.handle_error(error)
        
        assert isinstance(result, RecoveryAction)
        assert result.can_recover == True
        assert result.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_handle_error_max_retries(self, recovery_handler):
        """Test handling error when max retries reached."""
        recovery_handler.max_retries = 0  # No retries allowed
        
        error = ElementNotFoundError("Element not found")
        
        result = await recovery_handler.handle_error(error)
        
        assert result.can_recover == False
        assert result.reason in ["Unrecoverable error type", "Max retry attempts exceeded"]


class TestPhase6Integration:
    """Test Phase 6 error recovery integration."""
    
    @pytest.mark.asyncio
    async def test_full_error_recovery_flow(self, recovery_handler):
        """Test full error recovery flow."""
        
        # Simulate error
        error = ElementNotFoundError("#email not found")
        
        # Handle error
        result = await recovery_handler.handle_error(error)
        
        # Verify recovery
        assert isinstance(result, RecoveryAction)
        assert result.can_recover == True
        
        # Verify metrics
        assert recovery_handler.metrics.total_errors == 1
        assert recovery_handler.metrics.recovery_attempts >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])