"""Action types and decision models for the agent."""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List
from datetime import datetime


class ActionType(Enum):
    """Available actions for the browser agent."""
    
    CLICK = "click"
    FILL = "fill"
    SUBMIT = "submit"
    SCROLL = "scroll"
    WAIT = "wait"
    DONE = "done"
    INVALID = "invalid"


class ScrollDirection(Enum):
    """Scroll directions."""
    
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class ActionDecision:
    """Decision made by LLM about what action to take."""
    
    action: ActionType
    target: str  # CSS selector or element identifier
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "target": self.target,
            "params": self.params,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionDecision":
        """Create from dictionary."""
        return cls(
            action=ActionType(data.get("action", "invalid")),
            target=data.get("target", ""),
            params=data.get("params", {}),
            reasoning=data.get("reasoning", ""),
            confidence=float(data.get("confidence", 0.5))
        )


@dataclass
class ActionResult:
    """Result of executing an action."""
    
    action: ActionType
    target: str
    success: bool
    error: Optional[str] = None
    html_after: Optional[str] = None
    url_after: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "target": self.target,
            "success": self.success,
            "error": self.error,
            "url": self.url_after,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentState:
    """State of the agent during execution."""
    
    current_url: str
    current_title: str
    iterations: int = 0
    decisions: List[ActionDecision] = field(default_factory=list)
    results: List[ActionResult] = field(default_factory=list)
    goal: str = ""
    status: str = "running"  # running, completed, failed, timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.current_url,
            "title": self.current_title,
            "iterations": self.iterations,
            "decisions": [d.to_dict() for d in self.decisions],
            "results": [r.to_dict() for r in self.results],
            "goal": self.goal,
            "status": self.status
        }