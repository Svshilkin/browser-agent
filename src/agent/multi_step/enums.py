from enum import Enum


class TaskType(Enum):
    """Types of tasks"""
    NAVIGATE = "navigate"
    FILL_FORM = "fill_form"
    CLICK_ELEMENT = "click_element"
    EXTRACT_DATA = "extract_data"
    WAIT_FOR_CONDITION = "wait_for_condition"
    CONDITIONAL_BRANCH = "conditional_branch"
    LOOP_TASK = "loop_task"
    COMPOSITE_TASK = "composite_task"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 3
    HIGH = 2
    NORMAL = 1


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class DependencyType(Enum):
    """Types of task dependencies"""
    SEQUENTIAL = "sequential"      # B starts after A
    PARALLEL = "parallel"          # B starts with A
    CONDITIONAL = "conditional"    # B depends on A result
    WAIT_FOR = "wait_for"         # B waits for A ready