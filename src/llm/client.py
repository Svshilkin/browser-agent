"""GLM API client for getting LLM decisions."""

import os
import asyncio
import logging
from typing import Optional, List
from time import sleep

try:
    from zhipuai import ZhipuAI
    import zhipuai
except ImportError as e:
    raise ImportError("Install zhipuai: pip install zhipuai") from e

from src.llm.models import GLMRequest, GLMResponse, GLMConfig, Message, MessageRole

logger = logging.getLogger(__name__)


class GLMClient:
    """Client for ZhipuAI GLM API."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[GLMConfig] = None):
        """Initialize GLM client.
        
        Args:
            api_key: ZhipuAI API key (from .env API_KEY or parameter)
            config: GLMConfig object (optional)
        """
        
        if config:
            self.config = config
        else:
            api_key = api_key or os.getenv("API_KEY")
            if not api_key:
                raise ValueError("API_KEY not found in environment or parameters")
            
            self.config = GLMConfig(api_key=api_key)
        
        self.client = ZhipuAI(api_key=self.config.api_key)
        logger.info(f"GLM client initialized with model: {self.config.model}")
    
    def get_decision(self, prompt: str, context_window: Optional[int] = None) -> str:
        """Get a decision from GLM (synchronous).
        
        Args:
            prompt: Prompt to send to GLM
            context_window: Token context limit (overrides config)
            
        Returns:
            GLM response text
            
        Raises:
            Exception: On API errors
        """
        
        context_window = context_window or 4000
        
        return self._get_decision_with_retry(
            prompt=prompt,
            max_retries=self.config.max_retries,
            backoff_factor=self.config.retry_backoff
        )
    
    async def get_decision_async(
        self,
        prompt: str,
        context_window: Optional[int] = None
    ) -> str:
        """Get a decision from GLM (asynchronous).
        
        Args:
            prompt: Prompt to send to GLM
            context_window: Token context limit
            
        Returns:
            GLM response text
        """
        
        return await asyncio.to_thread(
            self.get_decision,
            prompt,
            context_window
        )
    
    def _get_decision_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ) -> str:
        """Get decision with exponential backoff retry."""
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens
                )
                
                content = response.choices[0].message.content
                logger.info(f"GLM response received ({len(content)} chars)")
                return content
            
            except getattr(zhipuai, "APITimeoutError", Exception) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = (backoff_factor ** attempt)
                    logger.warning(
                        f"Timeout, waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                    )
                    sleep(wait_time)
                else:
                    raise

            except getattr(zhipuai, "APIStatusError", Exception) as e:
                # SDK: при 40x/50x выбрасывает APIStatusError (и наследников) [page:0][page:1]
                status_code = getattr(e, "status_code", None)
                last_error = e

                # retry on 429 (rate limit) and 503 (server overloaded) [page:0][page:1]
                if status_code in (429, 503) and attempt < max_retries - 1:
                    wait_time = (backoff_factor ** attempt)
                    logger.warning(
                        f"GLM status={status_code}, waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                    )
                    sleep(wait_time)
                    continue

                logger.error(f"GLM API status error (status={status_code}): {e}")
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        # All retries failed
        logger.error(f"Failed after {max_retries} retries: {last_error}")
        raise last_error
    
    def validate_api_key(self) -> bool:
        """Validate API key by making a test request."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{
                    "role": "user",
                    "content": "Hello, this is a test message."
                }],
                max_tokens=10
            )
            logger.info("API key validation successful")
            return True
        
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def get_token_usage(self) -> Optional[dict]:
        """Get token usage information from last request."""
        # ZhipuAI returns usage in response
        return None
    
    @classmethod
    def from_env(cls) -> "GLMClient":
        """Create client from environment variables."""
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY environment variable not set")
        
        return cls(api_key=api_key)