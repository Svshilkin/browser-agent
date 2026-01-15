"""Agent configuration."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Configuration for browser agent."""
    
    # Execution limits
    max_iterations: int = 20
    action_timeout: float = 10.0
    session_timeout: float = 300.0
    
    # Behavior
    verbose: bool = True
    retry_on_error: bool = True
    fail_fast: bool = False
    screenshot_on_error: bool = True
    
    # Features
    use_smart_prompt: bool = True
    element_highlight: bool = False
    auto_scroll: bool = True
    keep_history: bool = True
    save_state: bool = False
    
    # Sleep durations (seconds)
    sleep_after_click: float = 0.5
    sleep_after_fill: float = 0.3
    sleep_after_scroll: float = 0.5
    sleep_on_error: float = 1.0
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables."""
        import os
        return cls(
            max_iterations=int(os.getenv("MAX_ITERATIONS", "20")),
            verbose=os.getenv("VERBOSE", "true").lower() == "true",
            fail_fast=os.getenv("FAIL_FAST", "false").lower() == "true",
        )


@dataclass
class AgentMetrics:
    """Metrics from agent execution."""
    
    total_iterations: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    total_time_ms: float = 0.0
    avg_confidence: float = 0.0
    actions_by_type: dict = field(default_factory=dict)
    start_time: Optional[float] = None
    
    def record_iteration(self, success: bool, action_type: str, confidence: float):
        """Record metrics from iteration."""
        self.total_iterations += 1
        
        if success:
            self.successful_actions += 1
        else:
            self.failed_actions += 1
        
        # Update action type counter
        current_count = self.actions_by_type.get(action_type, 0)
        self.actions_by_type[action_type] = current_count + 1
        
        # Update average confidence
        if self.total_iterations == 1:
            self.avg_confidence = confidence
        else:
            # Running average
            self.avg_confidence = (
                (self.avg_confidence * (self.total_iterations - 1) + confidence)
                / self.total_iterations
            )
    
    def to_dict(self):
        """Convert metrics to dict."""
        return {
            "total_iterations": self.total_iterations,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "total_time_ms": self.total_time_ms,
            "avg_confidence": round(self.avg_confidence, 2),
            "actions_by_type": self.actions_by_type,
            "success_rate": round(
                (self.successful_actions / self.total_iterations * 100)
                if self.total_iterations > 0
                else 0,
                1
            ),
        }