"""Tests for Phase 5: Agent Loop."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.config import AgentConfig, AgentMetrics
from src.agent.state import BrowserAgentState, PageSnapshot
from src.agent.executor import ActionExecutor, ActionExecutionError
from src.agent.action_types import ActionType, ActionDecision
from src.agent.browser_agent import BrowserAgent, AgentResult


# ============ FIXTURES ============

@pytest.fixture
def mock_browser():
    """Mock browser instance."""
    browser = AsyncMock()
    browser.navigate = AsyncMock()
    browser.find = AsyncMock()
    browser.scroll = AsyncMock()
    browser.current_url = AsyncMock(return_value="https://example.com")
    return browser


@pytest.fixture
def mock_analyzer():
    """Mock page analyzer."""
    analyzer = AsyncMock()
    analyzer.get_page_structure = AsyncMock(
        return_value=MagicMock(
            elements=[
                MagicMock(tag="button", text="Click me", attributes={"id": "btn"}),
            ],
            forms=[],
            links=[],
        )
    )
    return analyzer


@pytest.fixture
def mock_glm_client():
    """Mock GLM client."""
    client = MagicMock()
    client.get_decision = AsyncMock(
        return_value="ACTION: click\nTARGET: #btn\nCONFIDENCE: 0.95"
    )
    return client


@pytest.fixture
def agent_config():
    """Agent configuration."""
    return AgentConfig(
        max_iterations=10,
        verbose=False,
    )


# ============ TEST AGENT CONFIG ============

class TestAgentConfig:
    """Test AgentConfig."""
    
    def test_config_defaults(self):
        """Test default configuration."""
        config = AgentConfig()
        assert config.max_iterations == 20
        assert config.action_timeout == 10.0
        assert config.verbose == True
        assert config.retry_on_error == True
    
    def test_config_from_env(self):
        """Test config from environment."""
        import os
        os.environ["MAX_ITERATIONS"] = "15"
        os.environ["VERBOSE"] = "false"
        
        config = AgentConfig.from_env()
        assert config.max_iterations == 15
        assert config.verbose == False


# ============ TEST AGENT METRICS ============

class TestAgentMetrics:
    """Test AgentMetrics."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = AgentMetrics()
        assert metrics.total_iterations == 0
        assert metrics.successful_actions == 0
        assert metrics.failed_actions == 0
    
    def test_record_iteration(self):
        """Test recording iteration."""
        metrics = AgentMetrics()
        metrics.record_iteration(True, "CLICK", 0.9)
        
        assert metrics.total_iterations == 1
        assert metrics.successful_actions == 1
        assert metrics.failed_actions == 0
        assert metrics.actions_by_type["CLICK"] == 1
        assert metrics.avg_confidence == 0.9
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dict."""
        metrics = AgentMetrics()
        metrics.record_iteration(True, "CLICK", 0.9)
        
        result = metrics.to_dict()
        assert result["total_iterations"] == 1
        assert result["success_rate"] == 100.0


# ============ TEST AGENT STATE ============

class TestBrowserAgentState:
    """Test BrowserAgentState."""
    
    def test_state_initialization(self):
        """Test state initialization."""
        state = BrowserAgentState(
            current_url="https://example.com",
            goal="Test goal",
        )
        assert state.current_url == "https://example.com"
        assert state.goal == "Test goal"
        assert state.success == False
    
    def test_add_action(self):
        """Test adding action to history."""
        state = BrowserAgentState(current_url="https://example.com")
        action = ActionDecision(
            action=ActionType.CLICK,
            target="#button",
            confidence=0.9,
        )
        state.add_action(action)
        
        assert len(state.action_history) == 1
        assert state.action_history[0] == action
    
    def test_add_error(self):
        """Test adding error."""
        state = BrowserAgentState(current_url="https://example.com")
        state.iteration_count = 1
        state.add_error("Test error")
        
        assert len(state.error_log) == 1
        assert "Test error" in state.error_log[0]
    
    def test_get_last_actions(self):
        """Test getting last N actions."""
        state = BrowserAgentState(current_url="https://example.com")
        
        for i in range(5):
            action = ActionDecision(
                action=ActionType.CLICK,
                target=f"#btn{i}",
                confidence=0.9,
            )
            state.add_action(action)
        
        last_3 = state.get_last_actions(3)
        assert len(last_3) == 3
        assert last_3[0].target == "#btn2"


# ============ TEST ACTION EXECUTOR ============

class TestActionExecutor:
    """Test ActionExecutor."""
    
    @pytest.mark.asyncio
    async def test_execute_click(self, mock_browser):
        """Test executing click action."""
        mock_element = AsyncMock()
        mock_element.click = AsyncMock()
        mock_element.scroll_into_view = AsyncMock()
        mock_browser.find = AsyncMock(return_value=mock_element)
        
        executor = ActionExecutor(mock_browser)
        result = await executor.execute_click("#button")
        
        assert result == True
        mock_element.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_click_not_found(self, mock_browser):
        """Test click when element not found."""
        mock_browser.find = AsyncMock(return_value=None)
        
        executor = ActionExecutor(mock_browser)
        
        with pytest.raises(ActionExecutionError):
            await executor.execute_click("#notfound")
    
    @pytest.mark.asyncio
    async def test_execute_fill(self, mock_browser):
        """Test executing fill action."""
        mock_element = AsyncMock()
        mock_element.fill = AsyncMock()
        mock_element.clear = AsyncMock()
        mock_element.scroll_into_view = AsyncMock()
        mock_browser.find = AsyncMock(return_value=mock_element)
        
        executor = ActionExecutor(mock_browser)
        result = await executor.execute_fill("#input", "test value")
        
        assert result == True
        mock_element.fill.assert_called_once_with("test value")
    
    @pytest.mark.asyncio
    async def test_execute_scroll(self, mock_browser):
        """Test executing scroll action."""
        mock_browser.scroll = AsyncMock()
        
        executor = ActionExecutor(mock_browser)
        result = await executor.execute_scroll("down")
        
        assert result == True
        mock_browser.scroll.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_wait(self, mock_browser):
        """Test executing wait action."""
        executor = ActionExecutor(mock_browser)
        
        import time
        start = time.time()
        result = await executor.execute_wait(0.1)
        elapsed = time.time() - start
        
        assert result == True
        assert elapsed >= 0.09


# ============ TEST BROWSER AGENT ============

class TestBrowserAgent:
    """Test BrowserAgent."""
    
    def test_agent_initialization(self, mock_browser, mock_analyzer, mock_glm_client, agent_config):
        """Test agent initialization."""
        agent = BrowserAgent(
            browser=mock_browser,
            analyzer=mock_analyzer,
            glm_client=mock_glm_client,
            config=agent_config,
        )
        
        assert agent.browser == mock_browser
        assert agent.analyzer == mock_analyzer
        assert agent.glm_client == mock_glm_client
        assert agent.config == agent_config
    
    @pytest.mark.asyncio
    async def test_agent_run_basic(self, mock_browser, mock_analyzer, mock_glm_client, agent_config):
        """Test basic agent run."""
        # Setup mocks
        mock_browser.navigate = AsyncMock()
        mock_browser.current_url = AsyncMock(return_value="https://example.com")
        
        # Mock decision that says DONE
        mock_glm_client.get_decision = AsyncMock(
            return_value="ACTION: done\nCONFIDENCE: 0.95"
        )
        
        # Create agent
        agent = BrowserAgent(
            browser=mock_browser,
            analyzer=mock_analyzer,
            glm_client=mock_glm_client,
            config=agent_config,
        )
        
        # Run agent
        result = await agent.run(
            goal="Test goal",
            url="https://example.com",
        )
        
        # Verify
        assert isinstance(result, AgentResult)
        assert mock_browser.navigate.called
    
    @pytest.mark.asyncio
    async def test_agent_iteration_count(self, mock_browser, mock_analyzer, mock_glm_client, agent_config):
        """Test agent respects iteration limit."""
        agent_config.max_iterations = 3
        
        # Mock browser and analyzer
        mock_browser.navigate = AsyncMock()
        mock_browser.current_url = AsyncMock(return_value="https://example.com")
        
        # Mock GLM to never return DONE
        mock_glm_client.get_decision = AsyncMock(
            return_value="ACTION: wait\nVALUE: 0.1\nCONFIDENCE: 0.9"
        )
        
        # Create agent
        agent = BrowserAgent(
            browser=mock_browser,
            analyzer=mock_analyzer,
            glm_client=mock_glm_client,
            config=agent_config,
        )
        
        # Run agent
        result = await agent.run(
            goal="Test goal",
            url="https://example.com",
        )
        
        # Verify max iterations respected
        assert result.state.iteration_count <= agent_config.max_iterations


# ============ TEST INTEGRATION ============

class TestPhase5Integration:
    """Test Phase 5 full integration."""
    
    @pytest.mark.asyncio
    async def test_full_agent_pipeline(self, mock_browser, mock_analyzer, mock_glm_client, agent_config):
        """Test full agent pipeline: navigate → analyze → decide → execute."""
        
        # Setup mocks for multi-step process
        mock_browser.navigate = AsyncMock()
        mock_browser.current_url = AsyncMock(return_value="https://example.com")
        
        # Mock element
        mock_element = AsyncMock()
        mock_element.click = AsyncMock()
        mock_element.scroll_into_view = AsyncMock()
        
        # Track call sequence
        call_sequence = []
        
        async def find_sequence(selector):
            call_sequence.append(f"find:{selector}")
            return mock_element
        
        mock_browser.find = AsyncMock(side_effect=find_sequence)
        
        # Mock GLM decisions for multi-step flow
        glm_responses = [
            "ACTION: click\nTARGET: #login\nCONFIDENCE: 0.95",
            "ACTION: done\nCONFIDENCE: 0.95",
        ]
        mock_glm_client.get_decision = AsyncMock(side_effect=glm_responses)
        
        # Create and run agent
        agent = BrowserAgent(
            browser=mock_browser,
            analyzer=mock_analyzer,
            glm_client=mock_glm_client,
            config=agent_config,
        )
        
        result = await agent.run(
            goal="Sign in",
            url="https://example.com",
        )
        
        # Verify
        assert result.state.iteration_count >= 1
        assert len(result.state.action_history) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])