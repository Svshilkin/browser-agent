"""Parse GLM responses into action decisions."""

import re
from typing import Optional, Dict, Any
from src.agent.action_types import ActionDecision, ActionType
import logging

logger = logging.getLogger(__name__)


class DecisionParser:
    """Parse GLM responses into ActionDecision objects."""
    
    @staticmethod
    def parse_response(response: str) -> ActionDecision:
        """Parse GLM response into ActionDecision.
        
        Expected format:
        ACTION: click
        TARGET: #button-id
        REASON: This button is the login button
        CONFIDENCE: 0.95
        
        Args:
            response: GLM response text
            
        Returns:
            ActionDecision object
            
        Raises:
            ValueError: If response cannot be parsed
        """
        
        try:
            # Extract lines
            lines = response.strip().split('\n')
            data = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip().upper()] = value.strip()
            
            # Extract and validate action
            action_str = data.get('ACTION', 'INVALID').lower()
            try:
                action = ActionType(action_str)
            except ValueError:
                logger.warning(f"Invalid action: {action_str}, using INVALID")
                action = ActionType.INVALID
            
            # Extract target
            target = data.get('TARGET', '')
            
            # Extract reason
            reason = data.get('REASON', '')
            
            # Extract and validate confidence
            confidence_str = data.get('CONFIDENCE', '0.5')
            try:
                confidence = float(confidence_str)
                confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
            except ValueError:
                logger.warning(f"Invalid confidence: {confidence_str}, using 0.5")
                confidence = 0.5
            
            # Validate required fields
            if action == ActionType.INVALID:
                logger.warning("Parsed as INVALID action")
            
            if not target and action not in [ActionType.DONE, ActionType.SCROLL]:
                logger.warning(f"Missing target for action {action}")
            
            return ActionDecision(
                action=action,
                target=target,
                params=DecisionParser._extract_params(action, data),
                reasoning=reason,
                confidence=confidence
            )
        
        except Exception as e:
            logger.error(f"Failed to parse response: {e}\nResponse: {response}")
            # Return safe default
            return ActionDecision(
                action=ActionType.WAIT,
                target="",
                reasoning=f"Parse error: {str(e)}",
                confidence=0.1
            )
    
    @staticmethod
    def _extract_params(action: ActionType, data: Dict[str, str]) -> Dict[str, Any]:
        """Extract action-specific parameters."""
        params = {}
        
        if action == ActionType.FILL:
            # Expected: VALUE: some text
            if 'VALUE' in data:
                params['value'] = data['VALUE']
        
        elif action == ActionType.SCROLL:
            # Expected: DIRECTION: up/down/left/right
            direction = data.get('DIRECTION', 'down').lower()
            if direction in ['up', 'down', 'left', 'right']:
                params['direction'] = direction
        
        elif action == ActionType.WAIT:
            # Expected: SECONDS: number
            seconds_str = data.get('SECONDS', '1')
            try:
                params['seconds'] = int(seconds_str)
            except ValueError:
                params['seconds'] = 1
        
        return params
    
    @staticmethod
    def parse_multiple_responses(responses: list) -> list:
        """Parse multiple responses (for batched processing)."""
        return [DecisionParser.parse_response(r) for r in responses]


class RobustDecisionParser(DecisionParser):
    """More robust parser with fallback strategies."""
    
    @staticmethod
    def parse_response_robust(response: str) -> ActionDecision:
        """Parse with fallback strategies.
        
        Tries:
        1. Standard format parsing
        2. Alternative format parsing
        3. Keyword extraction
        4. Safe defaults
        """
        
        # Try standard parsing first
        try:
            decision = DecisionParser.parse_response(response)
            if decision.action != ActionType.INVALID and decision.target:
                return decision
        except Exception:
            pass
        
        # Try alternative formats
        decision = RobustDecisionParser._parse_alternative_format(response)
        if decision.action != ActionType.INVALID:
            return decision
        
        # Try keyword extraction
        decision = RobustDecisionParser._parse_by_keywords(response)
        if decision.action != ActionType.INVALID:
            return decision
        
        # Fallback to WAIT
        logger.warning("Could not parse response, defaulting to WAIT")
        return ActionDecision(
            action=ActionType.WAIT,
            target="",
            reasoning="Could not parse LLM response",
            confidence=0.1
        )
    
    @staticmethod
    def _parse_alternative_format(response: str) -> ActionDecision:
        """Try parsing alternative formats like 'Click the X button'."""
        response_lower = response.lower()
        
        # Pattern: "Click the ... button"
        if 'click' in response_lower:
            return ActionDecision(
                action=ActionType.CLICK,
                target="",
                reasoning=response,
                confidence=0.7
            )
        
        # Pattern: "Fill the ... field"
        if 'fill' in response_lower:
            return ActionDecision(
                action=ActionType.FILL,
                target="",
                params={},
                reasoning=response,
                confidence=0.7
            )
        
        # Pattern: "Done" or "Complete"
        if 'done' in response_lower or 'complete' in response_lower:
            return ActionDecision(
                action=ActionType.DONE,
                target="",
                reasoning=response,
                confidence=0.8
            )
        
        return ActionDecision(
            action=ActionType.INVALID,
            target="",
            reasoning=response,
            confidence=0.0
        )
    
    @staticmethod
    def _parse_by_keywords(response: str) -> ActionDecision:
        """Extract action by keyword matching."""
        response_lower = response.lower()
        
        # Try to find action keywords
        for action in ActionType:
            if action.value in response_lower:
                return ActionDecision(
                    action=action,
                    target="",
                    reasoning=response,
                    confidence=0.5
                )
        
        return ActionDecision(
            action=ActionType.INVALID,
            target="",
            reasoning=response,
            confidence=0.0
        )