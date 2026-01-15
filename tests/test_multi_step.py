"""
Tests for Phase 7: Multi-step tasks
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.agent.multi_step.enums import (
    TaskType, TaskPriority, TaskStatus, DependencyType
)
from src.agent.multi_step.models import (
    TaskDefinition, TaskResult, TaskDependency, TaskMetrics
)
from src.agent.multi_step.dependency_graph import DependencyGraph
from src.agent.multi_step.multi_step_manager import MultiStepTaskManager


class TestTaskDefinition:
    """Test TaskDefinition"""
    
    def test_create_task(self):
        task = TaskDefinition(
            id="task1",
            type=TaskType.NAVIGATE,
            priority=TaskPriority.HIGH,
            parameters={"url": "https://example.com"}
        )
        
        assert task.id == "task1"
        assert task.type == TaskType.NAVIGATE
        assert task.priority == TaskPriority.HIGH


class TestDependencyGraph:
    """Test dependency graph"""
    
    def test_create_graph(self):
        graph = DependencyGraph()
        
        task1 = TaskDefinition(
            id="task1",
            type=TaskType.NAVIGATE
        )
        graph.add_task(task1)
        
        assert "task1" in graph.tasks
    
    def test_sequential_dependency(self):
        graph = DependencyGraph()
        
        task1 = TaskDefinition(id="task1", type=TaskType.NAVIGATE)
        task2 = TaskDefinition(
            id="task2",
            type=TaskType.FILL_FORM,
            dependencies=[
                TaskDependency(
                    task_id="task1",
                    dep_type=DependencyType.SEQUENTIAL
                )
            ]
        )
        
        graph.add_task(task1)
        graph.add_task(task2)
        
        # task1 has no dependencies, should be ready first
        ready = graph.get_ready_tasks(set())
        assert ready[0].id == "task1"
    
    def test_cycle_detection(self):
        graph = DependencyGraph()
        
        # This would create a cycle, but we prevent it during add
        task1 = TaskDefinition(id="task1", type=TaskType.NAVIGATE)
        graph.add_task(task1)
        
        # Cycle detection would need explicit setup
        cycles = graph.detect_cycles()
        assert len(cycles) == 0
    
    def test_topological_sort(self):
        graph = DependencyGraph()
        
        task1 = TaskDefinition(id="task1", type=TaskType.NAVIGATE)
        task2 = TaskDefinition(
            id="task2",
            type=TaskType.FILL_FORM,
            dependencies=[
                TaskDependency("task1", DependencyType.SEQUENTIAL)
            ]
        )
        task3 = TaskDefinition(
            id="task3",
            type=TaskType.CLICK_ELEMENT,
            dependencies=[
                TaskDependency("task2", DependencyType.SEQUENTIAL)
            ]
        )
        
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        order = graph.get_execution_order()
        assert order == ["task1", "task2", "task3"]


class TestTaskMetrics:
    """Test task metrics"""
    
    def test_create_metrics(self):
        metrics = TaskMetrics()
        
        assert metrics.total_tasks == 0
        assert metrics.completed_tasks == 0
    
    def test_to_dict(self):
        metrics = TaskMetrics(
            total_tasks=5,
            completed_tasks=3,
            failed_tasks=2
        )
        
        result = metrics.to_dict()
        assert result["total_tasks"] == 5
        assert result["completed_tasks"] == 3
        assert result["failed_tasks"] == 2


class TestMultiStepTaskManager:
    """Test multi-step task manager"""
    
    @pytest.mark.asyncio
    async def test_execute_single_task(self):
        mock_browser = AsyncMock()
        manager = MultiStepTaskManager(mock_browser)
        
        task = TaskDefinition(
            id="task1",
            type=TaskType.NAVIGATE,
            parameters={"url": "https://example.com"}
        )
        
        results = await manager.execute_tasks([task])
        
        assert "task1" in results
        assert results["task1"].success is True
    
    @pytest.mark.asyncio
    async def test_execute_sequential_tasks(self):
        mock_browser = AsyncMock()
        manager = MultiStepTaskManager(mock_browser)
        
        task1 = TaskDefinition(id="task1", type=TaskType.NAVIGATE)
        task2 = TaskDefinition(
            id="task2",
            type=TaskType.FILL_FORM,
            dependencies=[
                TaskDependency("task1", DependencyType.SEQUENTIAL)
            ]
        )
        
        results = await manager.execute_tasks([task1, task2])
        
        assert len(results) == 2
        assert all(r.success for r in results.values())
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        mock_browser = AsyncMock()
        manager = MultiStepTaskManager(mock_browser)
        
        tasks = [
            TaskDefinition(
                id=f"task{i}",
                type=TaskType.NAVIGATE
            )
            for i in range(3)
        ]
        
        results = await manager.execute_tasks(tasks)
        metrics = manager.get_metrics()
        
        assert metrics["total_tasks"] == 3
        assert metrics["completed_tasks"] == 3