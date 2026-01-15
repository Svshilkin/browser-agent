"""Browser agent state management."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from src.agent.action_types import ActionDecision
from src.browser.analyzer import PageStructure


@dataclass
class PageSnapshot:
    """Snapshot of page state at specific point in time."""
    
    url: str
    structure: PageStructure
    timestamp: float
    screenshot_path: Optional[str] = None
    
    @property
    def time_str(self):
        """Get human-readable timestamp."""
        return datetime.fromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )


@dataclass
class BrowserAgentState:
    """Mutable state of browser agent during execution."""
    
    current_url: str
    goal: str = ""
    iteration_count: int = 0
    action_history: List[ActionDecision] = field(default_factory=list)
    page_snapshots: List[PageSnapshot] = field(default_factory=list)
    error_log: List[str] = field(default_factory=list)
    success: bool = False
    start_time: Optional[float] = None
    
    def add_action(self, action: ActionDecision):
        """Add action to history."""
        self.action_history.append(action)
    
    def add_error(self, error: str):
        """Log an error."""
        timestamp = f"[{self.iteration_count}]"
        self.error_log.append(f"{timestamp} {error}")
    
    def add_snapshot(self, snapshot: PageSnapshot):
        """Record page state."""
        self.page_snapshots.append(snapshot)
    
    def get_last_actions(self, n: int = 5) -> List[ActionDecision]:
        """Get last N actions."""
        return self.action_history[-n:] if self.action_history else []
    
    def get_current_snapshot(self) -> Optional[PageSnapshot]:
        """Get most recent page snapshot."""
        return self.page_snapshots[-1] if self.page_snapshots else None
    
    def has_errors(self) -> bool:
        """Check if any errors occurred."""
        return len(self.error_log) > 0
    
    def to_dict(self):
        """Convert state to dict for logging."""
        return {
            "current_url": self.current_url,
            "goal": self.goal,
            "iteration_count": self.iteration_count,
            "total_actions": len(self.action_history),
            "total_errors": len(self.error_log),
            "success": self.success,
            "last_action": (
                self.action_history[-1].action.name
                if self.action_history
                else None
            ),
        }