"""Tests for Phase 4 LLM integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.agent.action_types import ActionType, ActionDecision, ActionResult
from src.llm.models import GLMRequest, GLMResponse, GLMConfig, Message, MessageRole
from src.llm.prompt_builder import PromptBuilder, SmartPromptBuilder
from src.llm.decision_parser import DecisionParser, RobustDecisionParser
from src.llm.client import GLMClient
from src.browser.models import PageStructure, Button, Form, Input, Link


@pytest.fixture
def sample_page_structure():
    """Sample page structure for testing."""
    return PageStructure(
        url="https://example.com/login",
        title="Login Page",
        buttons=[
            Button(text="Sign In", selector="#signin-btn", type="button"),
            Button(text="Register", selector="#register-btn", type="button"),
            Button(text="Forgot Password", selector="#forgot-btn", type="link"),
        ],
        forms=[
            Form(
                selector="#login-form",
                action="/login",
                method="POST",
                inputs=[
                    Input(name="email", type="email", selector="input[name='email']"),
                    Input(name="password", type="password", selector="input[name='password']"),
                ]
            )
        ],
        links=[
            Link(text="Home", href="/", selector="a[href='/']"),
            Link(text="Documentation", href="/docs", selector="a[href='/docs']"),
        ],
        headings=["Login", "Sign In to Your Account"],
        paragraphs=3
    )


@pytest.fixture
def glm_config():
    """GLM configuration for testing."""
    return GLMConfig(
        api_key="test-api-key",
        model="glm-4",
        temperature=0.7,
        max_retries=2
    )


class TestActionDecision:
    """Test ActionDecision model."""
    
    def test_action_decision_creation(self):
        """Test creating ActionDecision."""
        decision = ActionDecision(
            action=ActionType.CLICK,
            target="#signin-btn",
            reasoning="Click the Sign In button",
            confidence=0.95
        )
        
        assert decision.action == ActionType.CLICK
        assert decision.target == "#signin-btn"
        assert decision.confidence == 0.95
    
    def test_action_decision_to_dict(self):
        """Test converting ActionDecision to dict."""
        decision = ActionDecision(
            action=ActionType.CLICK,
            target="#signin-btn",
            reasoning="Test",
            confidence=0.95
        )
        
        result = decision.to_dict()
        assert result["action"] == "click"
        assert result["target"] == "#signin-btn"
        assert result["confidence"] == 0.95
    
    def test_action_decision_from_dict(self):
        """Test creating ActionDecision from dict."""
        data = {
            "action": "click",
            "target": "#signin-btn",
            "reasoning": "Test",
            "confidence": 0.95
        }
        
        decision = ActionDecision.from_dict(data)
        assert decision.action == ActionType.CLICK
        assert decision.target == "#signin-btn"


class TestPromptBuilder:
    """Test PromptBuilder."""
    
    def test_build_simple_prompt(self, sample_page_structure):
        """Test building a simple prompt."""
        prompt = PromptBuilder.build_prompt(
            structure=sample_page_structure,
            goal="Sign in to the website"
        )
        
        assert "Sign in to the website" in prompt
        assert "example.com/login" in prompt
        assert len(prompt) > 100
    
    def test_build_prompt_includes_buttons(self, sample_page_structure):
        """Test that prompt includes buttons."""
        prompt = PromptBuilder.build_prompt(
            structure=sample_page_structure,
            goal="Sign in"
        )
        
        assert "Sign In" in prompt
        assert "Register" in prompt
    
    def test_build_prompt_includes_forms(self, sample_page_structure):
        """Test that prompt includes forms."""
        prompt = PromptBuilder.build_prompt(
            structure=sample_page_structure,
            goal="Sign in"
        )
        
        assert "email" in prompt
        assert "password" in prompt
    
    def test_build_prompt_with_history(self, sample_page_structure):
        """Test building prompt with action history."""
        history = [
            "ACTION: CLICK, TARGET: #email-field",
            "ACTION: FILL, TARGET: #email-field, VALUE: test@example.com"
        ]
        
        prompt = PromptBuilder.build_prompt(
            structure=sample_page_structure,
            goal="Sign in",
            history=history
        )
        
        assert "PREVIOUS ACTIONS" in prompt
        assert "test@example.com" in prompt


class TestSmartPromptBuilder:
    """Test SmartPromptBuilder."""
    
    def test_smart_prompt_highlights_relevant(self, sample_page_structure):
        """Test smart prompt highlights relevant elements."""
        prompt = SmartPromptBuilder.build_smart_prompt(
            structure=sample_page_structure,
            goal="Sign in to the website",
            relevant_keywords=["sign", "login", "signin"]
        )
        
        # Should highlight Sign In button
        assert "RELEVANT" in prompt or "Sign In" in prompt
    
    def test_filter_relevant_buttons(self, sample_page_structure):
        """Test filtering relevant buttons."""
        relevant = SmartPromptBuilder._filter_relevant_buttons(
            sample_page_structure.buttons,
            ["sign", "in"]
        )
        
        assert len(relevant) > 0
        assert relevant[0].text == "Sign In"


class TestDecisionParser:
    """Test DecisionParser."""
    
    def test_parse_click_action(self):
        """Test parsing CLICK action."""
        response = """ACTION: click
TARGET: #signin-btn
REASON: This is the Sign In button
CONFIDENCE: 0.95"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.CLICK
        assert decision.target == "#signin-btn"
        assert decision.confidence == 0.95
    
    def test_parse_fill_action(self):
        """Test parsing FILL action."""
        response = """ACTION: fill
TARGET: input[name='email']
VALUE: test@example.com
REASON: Fill the email field
CONFIDENCE: 0.9"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.FILL
        assert decision.target == "input[name='email']"
        assert decision.params.get("value") == "test@example.com"
    
    def test_parse_scroll_action(self):
        """Test parsing SCROLL action."""
        response = """ACTION: scroll
DIRECTION: down
REASON: Scroll to see more content
CONFIDENCE: 0.8"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.SCROLL
        assert decision.params.get("direction") == "down"
    
    def test_parse_wait_action(self):
        """Test parsing WAIT action."""
        response = """ACTION: wait
SECONDS: 2
REASON: Wait for page to load
CONFIDENCE: 0.7"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.WAIT
        assert decision.params.get("seconds") == 2
    
    def test_parse_done_action(self):
        """Test parsing DONE action."""
        response = """ACTION: done
REASON: Task completed
CONFIDENCE: 0.95"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.DONE
    
    def test_parse_invalid_action(self):
        """Test parsing invalid action defaults to INVALID."""
        response = """ACTION: unknown_action
TARGET: #something
CONFIDENCE: 0.5"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.action == ActionType.INVALID
    
    def test_parse_missing_confidence(self):
        """Test parsing with missing confidence defaults to 0.5."""
        response = """ACTION: click
TARGET: #button
REASON: Test"""
        
        decision = DecisionParser.parse_response(response)
        assert decision.confidence == 0.5


class TestRobustDecisionParser:
    """Test RobustDecisionParser."""
    
    def test_parse_alternative_format_click(self):
        """Test parsing alternative format for CLICK."""
        response = "Click the sign in button at the top right"
        
        decision = RobustDecisionParser.parse_response_robust(response)
        assert decision.action == ActionType.CLICK
    
    def test_parse_alternative_format_done(self):
        """Test parsing alternative format for DONE."""
        response = "The task is complete, we are done"
        
        decision = RobustDecisionParser.parse_response_robust(response)
        assert decision.action == ActionType.DONE


class TestGLMClient:
    """Test GLMClient."""
    
    @patch('zhipuai.ZhipuAI')
    def test_glm_client_initialization(self, mock_zhipu):
        """Test GLMClient initialization."""
        client = GLMClient(api_key="test-api-key")
        assert client.config.api_key == "test-api-key"
        assert client.config.model == "glm-4"
    
    @patch('src.llm.client.ZhipuAI')
    def test_glm_client_get_decision(self, mock_zhipu_class):
        """Test getting decision from GLM."""
        # Mock response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "ACTION: click\nTARGET: #btn\nCONFIDENCE: 0.9"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Mock the client instance
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_zhipu_class.return_value = mock_client_instance
        
        client = GLMClient(api_key="test-api-key")
        response = client.get_decision("Test prompt")
        
        assert "ACTION: click" in response
        # Verify API was called
        mock_client_instance.chat.completions.create.assert_called_once()
    
    @patch('src.llm.client.ZhipuAI')
    def test_glm_client_from_env(self, mock_zhipu_class):
        """Test creating client from environment."""
        import os
        
        # Mock the client instance
        mock_client_instance = MagicMock()
        mock_zhipu_class.return_value = mock_client_instance
        
        # Set env var
        os.environ["API_KEY"] = "env-api-key"
        
        client = GLMClient.from_env()
        assert client.config.api_key == "env-api-key"
        
        # Clean up
        del os.environ["API_KEY"]


class TestPhase4Integration:
    """Integration tests for Phase 4."""
    
    @patch('src.llm.client.ZhipuAI')
    def test_full_pipeline(self, mock_zhipu_class, sample_page_structure):
        """Test full Phase 4 pipeline: structure → prompt → GLM → decision."""
        
        # Mock GLM response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = """ACTION: click
    TARGET: #signin-btn
    REASON: Click the Sign In button
    CONFIDENCE: 0.95"""
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Mock the client instance
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_zhipu_class.return_value = mock_client_instance
        
        # 1. Build prompt from structure
        prompt = PromptBuilder.build_prompt(
            structure=sample_page_structure,
            goal="Sign in to the website"
        )
        assert len(prompt) > 0
        
        # 2. Get response from GLM
        client = GLMClient(api_key="test-api-key")
        glm_response = client.get_decision(prompt)
        assert "ACTION" in glm_response
        
        # 3. Parse decision
        decision = DecisionParser.parse_response(glm_response)
        assert decision.action == ActionType.CLICK
        assert decision.target == "#signin-btn"
        assert decision.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])