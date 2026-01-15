import asyncio
import logging
from datetime import datetime
from typing import Optional, Any

from src.agent.multi_step.models import (
    TaskDefinition, TaskResult, TaskStatus
)
from src.agent.multi_step.enums import TaskType

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes individual tasks"""
    
    def __init__(self, browser_agent):
        self.browser_agent = browser_agent
    
    async def execute(self, task: TaskDefinition) -> TaskResult:
        """Execute a single task"""
        start_time = datetime.now()
        
        try:
            result = await self._execute_task(task)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.SUCCESS,
                success=True,
                result=result,
                execution_time_ms=elapsed * 1000
            )
        
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Task {task.id} failed: {str(e)}")
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                success=False,
                error=str(e),
                execution_time_ms=elapsed * 1000
            )
    
    async def _execute_task(self, task: TaskDefinition) -> Any:
        """Execute task based on type"""
        
        if task.type == TaskType.NAVIGATE:
            url = task.parameters.get("url")
            await self.browser_agent.navigate(url)
            return {"navigated_to": url}
        
        elif task.type == TaskType.FILL_FORM:
            selector = task.parameters.get("selector")
            value = task.parameters.get("value")
            await self.browser_agent.fill_form(selector, value)
            return {"filled": selector}
        
        elif task.type == TaskType.CLICK_ELEMENT:
            selector = task.parameters.get("selector")
            await self.browser_agent.click(selector)
            return {"clicked": selector}
        
        elif task.type == TaskType.EXTRACT_DATA:
            selector = task.parameters.get("selector")
            data = await self.browser_agent.extract_data(selector)
            return {"extracted": data}
        
        elif task.type == TaskType.WAIT_FOR_CONDITION:
            condition = task.parameters.get("condition")
            timeout = task.parameters.get("timeout", task.timeout)
            await self.browser_agent.wait_for(condition, timeout)
            return {"condition_met": True}
        
        else:
            raise ValueError(f"Unknown task type: {task.type}")