"""Ollama client for local LLM inference stress testing."""

import logging
import time
import requests
import json
from typing import Dict, Any, List, Optional

from llm_infer.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for running inference with Ollama local models."""
    
    def __init__(self, 
                 model_name: str = "llama2:7b", 
                 base_url: str = "http://localhost:11434",
                 timeout: int = 60):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use (e.g., "llama2:7b", "codellama:7b")
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._check_connection()
    
    def _check_connection(self) -> None:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama at {self.base_url}")
                self._check_model_availability()
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
        except requests.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running.")
            raise ConnectionError(f"Ollama not accessible at {self.base_url}")
        except Exception as e:
            logger.error(f"Error checking Ollama connection: {e}")
            raise
    
    def _check_model_availability(self) -> None:
        """Check if the specified model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                if self.model_name in available_models:
                    logger.info(f"Model {self.model_name} is available")
                else:
                    logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                    logger.info(f"To pull the model, run: ollama pull {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not check model availability: {e}")
    
    def run_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Run inference on the given prompt.
        
        Args:
            prompt: The input prompt text
            
        Returns:
            Dictionary containing response, latency, tokens, and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40
                }
            }
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                response_text = result.get('response', '')
                
                # Extract token counts if available
                eval_count = result.get('eval_count', 0)  # Output tokens
                prompt_eval_count = result.get('prompt_eval_count', 0)  # Input tokens
                
                # Estimate tokens if not provided
                if eval_count == 0:
                    eval_count = len(response_text.split()) * 1.3  # Rough estimate
                if prompt_eval_count == 0:
                    prompt_eval_count = len(prompt.split()) * 1.3  # Rough estimate
                
                total_tokens = int(eval_count + prompt_eval_count)
                
                return {
                    "response": response_text,
                    "success": True,
                    "latency": latency,
                    "input_tokens": int(prompt_eval_count),
                    "output_tokens": int(eval_count),
                    "total_tokens": total_tokens,
                    "model": self.model_name,
                    "error": None,
                    "metadata": {
                        "eval_duration": result.get('eval_duration', 0),
                        "load_duration": result.get('load_duration', 0),
                        "prompt_eval_duration": result.get('prompt_eval_duration', 0),
                        "total_duration": result.get('total_duration', 0),
                        "temperature": 0.7,
                        "backend": "ollama"
                    }
                }
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                return {
                    "response": "",
                    "success": False,
                    "latency": latency,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "model": self.model_name,
                    "error": error_msg,
                    "metadata": {"backend": "ollama"}
                }
                
        except requests.Timeout:
            latency = time.time() - start_time
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            
            return {
                "response": "",
                "success": False,
                "latency": latency,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "model": self.model_name,
                "error": error_msg,
                "metadata": {"backend": "ollama"}
            }
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Error during Ollama inference: {str(e)}"
            logger.error(error_msg)
            
            return {
                "response": "",
                "success": False,
                "latency": latency,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "model": self.model_name,
                "error": error_msg,
                "metadata": {"backend": "ollama"}
            }
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models in Ollama.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return response.json().get('models', [])
            else:
                logger.error(f"Failed to list models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    @staticmethod
    def get_popular_models() -> Dict[str, Dict[str, str]]:
        """Get a list of popular Ollama models for easy selection."""
        return {
            "llama3.2:3b": {
                "name": "Llama 3.2 3B",
                "description": "Latest Llama 3.2 model, fast and efficient",
                "size": "~2.0GB"
            },
            "llama3.2:1b": {
                "name": "Llama 3.2 1B",
                "description": "Smallest Llama 3.2, ultra-fast inference",
                "size": "~1.3GB"
            },
            "deepseek-coder-v2:16b": {
                "name": "DeepSeek Coder V2 16B",
                "description": "Latest DeepSeek coding model, excellent for code",
                "size": "~9.0GB"
            },
            "deepseek-coder:6.7b": {
                "name": "DeepSeek Coder 6.7B",
                "description": "Smaller DeepSeek coding model",
                "size": "~3.8GB"
            },
            "qwen2.5:7b": {
                "name": "Qwen 2.5 7B",
                "description": "Alibaba's latest model, great performance",
                "size": "~4.4GB"
            },
            "mistral:7b": {
                "name": "Mistral 7B",
                "description": "Mistral AI's popular 7B model",
                "size": "~4.1GB"
            },
            "codellama:7b": {
                "name": "Code Llama 7B",
                "description": "Meta's code-specialized model",
                "size": "~3.8GB"
            },
            "llama2:7b": {
                "name": "Llama 2 7B",
                "description": "Meta's Llama 2 (stable, well-tested)",
                "size": "~3.8GB"
            },
            "phi3:3.8b": {
                "name": "Phi-3 3.8B",
                "description": "Microsoft's efficient small model",
                "size": "~2.3GB"
            },
            "granite-code:8b": {
                "name": "Granite Code 8B",
                "description": "IBM's open-source coding model",
                "size": "~4.6GB"
            }
        }
    
    @classmethod
    def is_ollama_available(cls, base_url: str = "http://localhost:11434") -> bool:
        """
        Check if Ollama is running and accessible.
        
        Args:
            base_url: Ollama base URL to check
            
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False 