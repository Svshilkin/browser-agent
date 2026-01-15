from typing import Dict, List, Set
import logging
from src.agent.multi_step.models import TaskDefinition, TaskDependency

logger = logging.getLogger(__name__)


class DependencyGraph:
    """Manages task dependencies"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskDefinition] = {}
        self.graph: Dict[str, List[str]] = {}
        self.reverse_graph: Dict[str, List[str]] = {}
    
    def add_task(self, task: TaskDefinition) -> None:
        """Add task to graph"""
        self.tasks[task.id] = task
        self.graph[task.id] = []
        self.reverse_graph[task.id] = []
        
        # Add dependencies
        for dep in task.dependencies:
            if dep.task_id not in self.tasks:
                raise ValueError(f"Dependency task {dep.task_id} not found")
            
            self.graph[dep.task_id].append(task.id)
            self.reverse_graph[task.id].append(dep.task_id)
    
    def get_ready_tasks(self, 
                       completed: Set[str]) -> List[TaskDefinition]:
        """Get tasks that are ready to execute"""
        ready = []
        
        for task_id, task in self.tasks.items():
            if task_id in completed:
                continue
            
            # Check if all dependencies are completed
            deps = self.reverse_graph.get(task_id, [])
            if all(dep in completed for dep in deps):
                ready.append(task)
        
        # Sort by priority (highest first)
        ready.sort(key=lambda t: t.priority.value, reverse=True)
        return ready
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in dependency graph"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            rec_stack.remove(node)
        
        for task_id in self.tasks:
            if task_id not in visited:
                dfs(task_id, [])
        
        return cycles
    
    def get_execution_order(self) -> List[str]:
        """Get topological sort of tasks"""
        if self.detect_cycles():
            raise ValueError("Cyclic dependency detected")
        
        visited = set()
        order = []
        
        def dfs(node: str) -> None:
            visited.add(node)
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
            order.append(node)
        
        for task_id in self.tasks:
            if task_id not in visited:
                dfs(task_id)
        
        return order[::-1]