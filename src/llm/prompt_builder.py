"""Build intelligent prompts for GLM from page structure."""

from typing import List, Optional
from src.browser.models import PageStructure, Button, Form, Link
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Build prompts for GLM based on page structure and goals."""
    
    SYSTEM_PROMPT = """You are an intelligent web browser agent. Your task is to analyze a webpage and decide what action to take next.

You can perform these actions:
- CLICK: Click a button or link
- FILL: Fill a form field
- SUBMIT: Submit a form
- SCROLL: Scroll the page (up, down, left, right)
- WAIT: Wait for page to load
- DONE: Task is complete

When responding, ALWAYS use this format:
ACTION: [action name]
TARGET: [selector or element id]
REASON: [brief explanation why this action]
CONFIDENCE: [0.0 to 1.0]

Be concise and direct."""
    
    @staticmethod
    def build_prompt(
        structure: PageStructure,
        goal: str,
        history: Optional[List[str]] = None,
        context_window: int = 4000
    ) -> str:
        """Build a prompt for GLM decision making.
        
        Args:
            structure: Page structure from analyzer
            goal: User's goal/task
            history: Previous actions taken
            context_window: Max tokens for prompt
            
        Returns:
            Formatted prompt string
        """
        
        prompt_parts = []
        
        # Add current page info
        page_info = PromptBuilder._format_page_info(structure)
        prompt_parts.append(page_info)
        
        # Add available actions
        actions_section = PromptBuilder._format_actions(structure)
        prompt_parts.append(actions_section)
        
        # Add goal
        goal_section = f"\nUSER GOAL:\n{goal}\n"
        prompt_parts.append(goal_section)
        
        # Add history if available
        if history:
            history_section = PromptBuilder._format_history(history)
            prompt_parts.append(history_section)
        
        # Combine and truncate to context window
        prompt = "\n".join(prompt_parts)
        
        if len(prompt) > context_window * 4:  # Rough token estimate
            logger.warning(f"Prompt exceeds context window, truncating")
            prompt = prompt[:context_window * 4]
        
        return prompt
    
    @staticmethod
    def _format_page_info(structure: PageStructure) -> str:
        """Format page information."""
        return f"""CURRENT PAGE:
URL: {structure.url}
Title: {structure.title}
Paragraphs: {structure.paragraphs}
"""
    
    @staticmethod
    def _format_actions(structure: PageStructure) -> str:
        """Format available actions."""
        parts = ["AVAILABLE ACTIONS:"]
        
        # Buttons
        if structure.buttons:
            parts.append("\nBUTTONS:")
            for btn in structure.buttons[:10]:  # Limit to 10
                selector_hint = f" [{btn.selector}]" if btn.selector else ""
                parts.append(f"  - {btn.text}{selector_hint}")
        
        # Forms
        if structure.forms:
            parts.append("\nFORMS:")
            for form in structure.forms[:5]:  # Limit to 5
                inputs_str = ", ".join([
                    f"{inp.name} ({inp.type})"
                    for inp in form.inputs[:3]
                ])
                selector_hint = f" [{form.selector}]" if form.selector else ""
                parts.append(f"  - Form{selector_hint}: {inputs_str}")
        
        # Links
        if structure.links:
            parts.append("\nLINKS:")
            for link in structure.links[:10]:  # Limit to 10
                selector_hint = f" [{link.selector}]" if link.selector else ""
                parts.append(f"  - {link.text} → {link.href}{selector_hint}")
        
        # Scroll options
        parts.append("\nSCROLL OPTIONS:")
        parts.append("  - scroll_up, scroll_down, scroll_left, scroll_right")
        
        # Wait option
        parts.append("\nOTHER:")
        parts.append("  - wait_[seconds]: Wait for content to load")
        parts.append("  - done: Mark task as complete")
        
        return "\n".join(parts)
    
    @staticmethod
    def _format_history(history: List[str]) -> str:
        """Format action history."""
        if not history:
            return ""
        
        parts = ["\nPREVIOUS ACTIONS:"]
        for i, action in enumerate(history[-5:], 1):  # Last 5 actions
            parts.append(f"  {i}. {action}")
        
        return "\n".join(parts)


class SmartPromptBuilder(PromptBuilder):
    """Extended prompt builder with smarter analysis."""
    
    @staticmethod
    def build_smart_prompt(
        structure: PageStructure,
        goal: str,
        history: Optional[List[str]] = None,
        relevant_keywords: Optional[List[str]] = None
    ) -> str:
        """Build a smarter prompt that highlights relevant elements.
        
        Args:
            structure: Page structure
            goal: User goal
            history: Previous actions
            relevant_keywords: Keywords to match against buttons/links
            
        Returns:
            Enhanced prompt
        """
        
        # Extract relevant keywords from goal if not provided
        if not relevant_keywords:
            relevant_keywords = goal.lower().split()
        
        # Filter buttons by relevance
        relevant_buttons = SmartPromptBuilder._filter_relevant_buttons(
            structure.buttons,
            relevant_keywords
        )
        
        # Filter links by relevance
        relevant_links = SmartPromptBuilder._filter_relevant_links(
            structure.links,
            relevant_keywords
        )
        
        # Build base prompt
        prompt = PromptBuilder.build_prompt(structure, goal, history)
        
        # Add relevance hints
        if relevant_buttons or relevant_links:
            relevance_section = "\nRELEVANT ELEMENTS (Likely candidates):\n"
            
            if relevant_buttons:
                relevance_section += "BUTTONS:\n"
                for btn in relevant_buttons[:3]:
                    relevance_section += f"  ⭐ {btn.text} [{btn.selector}]\n"
            
            if relevant_links:
                relevance_section += "LINKS:\n"
                for link in relevant_links[:3]:
                    relevance_section += f"  ⭐ {link.text} → {link.href}\n"
            
            prompt += relevance_section
        
        return prompt
    
    @staticmethod
    def _filter_relevant_buttons(
        buttons: List[Button],
        keywords: List[str]
    ) -> List[Button]:
        """Filter buttons that match keywords."""
        relevant = []
        button_text_lower = [b.text.lower() for b in buttons]
        
        for btn in buttons:
            text_lower = btn.text.lower()
            for keyword in keywords:
                if keyword in text_lower and len(keyword) > 2:
                    relevant.append(btn)
                    break
        
        return relevant
    
    @staticmethod
    def _filter_relevant_links(
        links: List[Link],
        keywords: List[str]
    ) -> List[Link]:
        """Filter links that match keywords."""
        relevant = []
        
        for link in links:
            text_lower = link.text.lower()
            href_lower = link.href.lower()
            
            for keyword in keywords:
                if (keyword in text_lower or keyword in href_lower) and len(keyword) > 2:
                    relevant.append(link)
                    break
        
        return relevant