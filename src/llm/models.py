"""Models for GLM API communication."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class MessageRole(Enum):
    """Message role in conversation."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """Single message in conversation."""
    
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class GLMRequest:
    """Request to GLM API."""
    
    messages: List[Message]
    model: str = "glm-4"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API."""
        return {
            "model": self.model,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens
        }


@dataclass
class GLMResponse:
    """Response from GLM API."""
    
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage
        }


@dataclass
class GLMConfig:
    """Configuration for GLM client."""
    
    api_key: str
    model: str = "glm-4"
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 1000
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 2.0