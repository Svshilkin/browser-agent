import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Set, Optional

from src.agent.multi_step.models import (
    TaskDefinition, TaskResult, TaskMetrics, TaskStatus
)
from src.agent.multi_step.dependency_graph import DependencyGraph
from src.agent.multi_step.task_executor import TaskExecutor

logger = logging.getLogger(__name__)


class MultiStepTaskManager:
    """Manages execution of multi-step tasks"""
    
    def __init__(self, browser_agent):
        self.browser_agent = browser_agent
        self.executor = TaskExecutor(browser_agent)
        self.metrics = TaskMetrics()
        self.results: Dict[str, TaskResult] = {}
    
    async def execute_tasks(
        self,
        tasks: List[TaskDefinition]
    ) -> Dict[str, TaskResult]:
        """Execute list of tasks respecting dependencies"""
        
        start_time = datetime.now()
        
        # Build dependency graph
        graph = DependencyGraph()
        for task in tasks:
            graph.add_task(task)
        
        # Check for cycles
        cycles = graph.detect_cycles()
        if cycles:
            raise ValueError(f"Cyclic dependencies detected: {cycles}")
        
        # Execute tasks
        completed: Set[str] = set()
        failed: Set[str] = set()
        
        while len(completed) + len(failed) < len(tasks):
            # Get ready tasks
            ready = graph.get_ready_tasks(completed)
            
            if not ready:
                # No ready tasks but not finished = deadlock
                pending = [
                    t.id for t in tasks 
                    if t.id not in completed and t.id not in failed
                ]
                raise RuntimeError(f"Task deadlock: {pending}")
            
            # Execute ready tasks (can be parallel)
            tasks_to_run = ready
            results = await asyncio.gather(
                *[self.executor.execute(t) for t in tasks_to_run],
                return_exceptions=False
            )
            
            # Process results
            for task, result in zip(tasks_to_run, results):
                self.results[task.id] = result
                
                if result.success:
                    completed.add(task.id)
                else:
                    if task.priority.value == 3:  # CRITICAL
                        self.metrics.critical_failures += 1
                    failed.add(task.id)
        
        # Update metrics
        elapsed = (datetime.now() - start_time).total_seconds()
        self._update_metrics(tasks, elapsed)
        
        return self.results
    
    def _update_metrics(self, tasks: List[TaskDefinition], 
                       total_time_ms: float) -> None:
        """Update execution metrics"""
        self.metrics.total_tasks = len(tasks)
        self.metrics.completed_tasks = len([
            r for r in self.results.values() 
            if r.success
        ])
        self.metrics.failed_tasks = len([
            r for r in self.results.values() 
            if not r.success
        ])
        self.metrics.total_time_ms = total_time_ms * 1000
        
        # By type
        for task in tasks:
            type_name = task.type.value
            self.metrics.tasks_by_type[type_name] = \
                self.metrics.tasks_by_type.get(type_name, 0) + 1
        
        # By priority
        for task in tasks:
            priority_name = task.priority.name
            self.metrics.tasks_by_priority[priority_name] = \
                self.metrics.tasks_by_priority.get(priority_name, 0) + 1
        
        # By status
        for result in self.results.values():
            status_name = result.status.value
            self.metrics.tasks_by_status[status_name] = \
                self.metrics.tasks_by_status.get(status_name, 0) + 1
        
        # Calculate success rate
        if self.metrics.total_tasks > 0:
            self.metrics.success_rate = (
                self.metrics.completed_tasks / self.metrics.total_tasks
            )
        
        # Calculate average time
        if self.results:
            times = [r.execution_time_ms for r in self.results.values()]
            self.metrics.avg_task_time_ms = sum(times) / len(times)
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.to_dict()