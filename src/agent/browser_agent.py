"""Browser automation agent with LLM decision-making."""

import asyncio
import logging
import time
from typing import Optional

from src.agent.config import AgentConfig, AgentMetrics
from src.agent.state import BrowserAgentState, PageSnapshot
from src.agent.executor import ActionExecutor, ActionExecutionError
from src.agent.action_types import ActionType, ActionDecision
from src.llm.client import GLMClient
from src.llm.prompt_builder import PromptBuilder
from src.llm.decision_parser import DecisionParser


logger = logging.getLogger(__name__)


class AgentResult:
    """Result of agent execution."""
    
    def __init__(
        self,
        success: bool,
        state: BrowserAgentState,
        metrics: AgentMetrics,
    ):
        self.success = success
        self.state = state
        self.metrics = metrics
    
    def to_dict(self):
        """Convert result to dict."""
        return {
            "success": self.success,
            "state": self.state.to_dict(),
            "metrics": self.metrics.to_dict(),
        }


class BrowserAgent:
    """Main browser automation agent with LLM integration."""
    
    def __init__(
        self,
        browser,
        analyzer,
        glm_client: GLMClient,
        config: Optional[AgentConfig] = None,
    ):
        """Initialize agent.
        
        Args:
            browser: AsyncBrowser from Phase 2
            analyzer: PageAnalyzer from Phase 3
            glm_client: GLMClient from Phase 4
            config: AgentConfig or None (uses defaults)
        """
        self.browser = browser
        self.analyzer = analyzer
        self.glm_client = glm_client
        self.config = config or AgentConfig()
        self.executor = ActionExecutor(browser)
    
    async def run(
        self,
        goal: str,
        url: str,
    ) -> AgentResult:
        """Run agent to achieve goal.
        
        Args:
            goal: Natural language task description
            url: Initial URL to navigate to
            
        Returns:
            AgentResult with success, state, and metrics
        """
        
        logger.info(f"🚀 Starting agent | Goal: {goal} | URL: {url}")
        
        # Initialize state and metrics
        state = BrowserAgentState(current_url=url, goal=goal)
        metrics = AgentMetrics()
        metrics.start_time = time.time()
        
        try:
            # Navigate to initial URL
            logger.info(f"Navigating to {url}")
            await self.browser.navigate(url)
            await asyncio.sleep(1.0)  # Wait for page load
            
            # Main loop
            while state.iteration_count < self.config.max_iterations:
                
                try:
                    # Run single iteration
                    decision = await self._run_iteration(state)
                    
                    # Check if should continue
                    if not self._should_continue(decision, state):
                        logger.info(
                            f"Stopping: {decision.action.name} or error limit"
                        )
                        break
                    
                    # Record metrics
                    metrics.record_iteration(
                        success=True,
                        action_type=decision.action.name,
                        confidence=decision.confidence,
                    )
                    
                    # Increment iteration
                    state.iteration_count += 1
                    
                except ActionExecutionError as e:
                    logger.error(f"Action error: {e}")
                    state.add_error(str(e))
                    metrics.record_iteration(
                        success=False,
                        action_type="ERROR",
                        confidence=0.0,
                    )
                    
                    # Optionally retry
                    if self.config.retry_on_error:
                        logger.info("Retrying next iteration...")
                        await asyncio.sleep(self.config.sleep_on_error)
                    else:
                        break
                    
                    state.iteration_count += 1
                
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    state.add_error(f"Critical: {str(e)}")
                    
                    if self.config.fail_fast:
                        raise
                    
                    state.iteration_count += 1
            
            # Determine success
            state.success = (
                len(state.action_history) > 0
                and state.action_history[-1].action == ActionType.DONE
            )
            
            # Final metrics
            metrics.total_time_ms = (
                (time.time() - metrics.start_time) * 1000
                if metrics.start_time
                else 0
            )
            
            logger.info(f"Agent finished | Success: {state.success}")
            logger.info(f"Metrics: {metrics.to_dict()}")
        
        except Exception as e:
            logger.error(f"Agent failed with exception: {e}")
            state.add_error(f"Fatal: {str(e)}")
            if self.config.fail_fast:
                raise
        
        return AgentResult(
            success=state.success,
            state=state,
            metrics=metrics,
        )
    
    async def _run_iteration(self, state: BrowserAgentState) -> ActionDecision:
        """Single iteration: analyze → decide → execute.
        
        Args:
            state: Current agent state
            
        Returns:
            ActionDecision from LLM
        """
        
        logger.debug(f"Iteration {state.iteration_count + 1}")
        
        # Step 1: Analyze current page
        logger.debug("Step 1: Analyzing page...")
        structure = await self.analyzer.get_page_structure()
        
        # Create snapshot
        snapshot = PageSnapshot(
            url=state.current_url,
            structure=structure,
            timestamp=time.time(),
        )
        state.add_snapshot(snapshot)
        
        # Step 2: Build prompt
        logger.debug("Step 2: Building prompt...")
        
        # Use smart builder if enabled
        if self.config.use_smart_prompt:
            from src.llm.prompt_builder import SmartPromptBuilder
            prompt = SmartPromptBuilder.build_prompt(
                structure=structure,
                goal=state.goal,
                history=state.get_last_actions(3),
            )
        else:
            prompt = PromptBuilder.build_prompt(
                structure=structure,
                goal=state.goal,
            )
        
        # Step 3: Get decision from GLM
        logger.debug("Step 3: Getting decision from GLM...")
        response = await self.glm_client.get_decision(prompt)
        decision = DecisionParser.parse_response(response)
        
        # Step 4: Execute action
        logger.debug("Step 4: Executing action...")
        try:
            await self.executor.execute(
                decision,
                timeout=self.config.action_timeout,
                auto_scroll=self.config.auto_scroll,
            )
            
            # Apply sleep based on action type
            if decision.action == ActionType.CLICK:
                await asyncio.sleep(self.config.sleep_after_click)
            elif decision.action == ActionType.FILL:
                await asyncio.sleep(self.config.sleep_after_fill)
            elif decision.action == ActionType.SCROLL:
                await asyncio.sleep(self.config.sleep_after_scroll)
            
        except ActionExecutionError as e:
            logger.error(f"Action execution failed: {e}")
            decision.success = False
            state.add_error(f"Execution: {str(e)}")
            raise
        
        # Step 5: Update state
        state.add_action(decision)
        state.current_url = await self.browser.current_url()
        
        logger.info(
            f"✓ Iteration {state.iteration_count}: "
            f"{decision.action.name} → {decision.target}"
        )
        
        return decision
    
    def _should_continue(
        self,
        decision: ActionDecision,
        state: BrowserAgentState,
    ) -> bool:
        """Determine if loop should continue.
        
        Args:
            decision: Last decision from LLM
            state: Current state
            
        Returns:
            True if should continue, False if should stop
        """
        
        # Stop if DONE action
        if decision.action == ActionType.DONE:
            logger.info("Agent completed task (DONE)")
            return False
        
        # Stop if too many errors
        if len(state.error_log) > 5:
            logger.error("Too many errors, stopping")
            return False
        
        # Stop if low confidence
        if decision.confidence < 0.3:
            logger.warning(f"Low confidence ({decision.confidence}), stopping")
            return False
        
        # Continue otherwise
        return True
    
    @classmethod
    def from_env(
        cls,
        browser,
        analyzer,
    ):
        """Create agent from environment config.
        
        Args:
            browser: AsyncBrowser instance
            analyzer: PageAnalyzer instance
            
        Returns:
            BrowserAgent instance
        """
        config = AgentConfig.from_env()
        glm_client = GLMClient.from_env()
        
        return cls(
            browser=browser,
            analyzer=analyzer,
            glm_client=glm_client,
            config=config,
        )