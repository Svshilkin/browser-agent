from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.agent.multi_step.enums import (
    TaskType, TaskPriority, TaskStatus, DependencyType
)


@dataclass
class TaskDependency:
    """Task dependency definition"""
    task_id: str
    dep_type: DependencyType
    condition: Optional[str] = None  # For CONDITIONAL


@dataclass
class TaskDefinition:
    """Definition of a task to execute"""
    id: str
    type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[TaskDependency] = field(default_factory=list)
    retry_count: int = 3
    timeout: float = 30.0
    
    def __str__(self) -> str:
        return f"Task({self.id}, {self.type.value}, {self.priority.name})"


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: TaskStatus
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    retry_attempts: int = 0


@dataclass
class TaskMetrics:
    """Metrics for task execution"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    
    tasks_by_type: Dict[str, int] = field(default_factory=dict)
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)
    tasks_by_status: Dict[str, int] = field(default_factory=dict)
    
    success_rate: float = 0.0
    avg_task_time_ms: float = 0.0
    critical_failures: int = 0
    retries_used: int = 0
    total_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary"""
        return {
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "pending_tasks": self.pending_tasks,
            "tasks_by_type": self.tasks_by_type,
            "tasks_by_priority": self.tasks_by_priority,
            "tasks_by_status": self.tasks_by_status,
            "success_rate": round(self.success_rate, 3),
            "avg_task_time_ms": round(self.avg_task_time_ms, 2),
            "critical_failures": self.critical_failures,
            "retries_used": self.retries_used,
            "total_time_ms": round(self.total_time_ms, 2),
        }