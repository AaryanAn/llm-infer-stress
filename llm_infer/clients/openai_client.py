"""OpenAI client for LLM inference stress testing."""

import logging
import os
import time
from typing import Dict, Any, Optional

import openai
from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for stress testing LLM inference."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_retries: int = 3,
        timeout: float = 30.0
    ) -> None:
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key. If None, loads from OPENAI_API_KEY env var.
            model: Model name to use for inference.
            max_retries: Maximum number of retries on failure.
            timeout: Request timeout in seconds.
            
        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
            
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI client with model: {self.model}")
    
    def run_prompt(self, prompt: str) -> Dict[str, Any]:
        """Run a prompt against the OpenAI model.
        
        Args:
            prompt: The prompt text to send to the model.
            
        Returns:
            Dict containing:
                - response: The model's response text
                - latency: Response time in seconds
                - success: Boolean indicating if request succeeded
                - error: Error message if any
                - model: Model name used
                - token_count: Approximate token count if available
        """
        start_time = time.time()
        result = {
            "response": "",
            "latency": 0.0,
            "success": False,
            "error": None,
            "model": self.model,
            "token_count": 0
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Sending prompt to OpenAI (attempt {attempt + 1}): {prompt[:50]}...")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=self.timeout
                )
                
                end_time = time.time()
                result["latency"] = end_time - start_time
                result["response"] = response.choices[0].message.content
                result["success"] = True
                
                # Extract token usage if available
                if response.usage:
                    result["token_count"] = response.usage.total_tokens
                
                logger.debug(f"OpenAI request succeeded in {result['latency']:.2f}s")
                break
                
            except openai.RateLimitError as e:
                error_msg = f"Rate limit exceeded: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
            except openai.APITimeoutError as e:
                error_msg = f"Request timeout: {str(e)}"
                logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                if attempt < self.max_retries:
                    time.sleep(1)
                    
            except openai.APIError as e:
                error_msg = f"OpenAI API error: {str(e)}"
                logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                if attempt < self.max_retries:
                    time.sleep(1)
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(f"Attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                if attempt < self.max_retries:
                    time.sleep(1)
        
        if not result["success"]:
            end_time = time.time()
            result["latency"] = end_time - start_time
            logger.error(f"All {self.max_retries + 1} attempts failed for OpenAI request")
        
        return result 