"""Ollama client for local LLM inference stress testing."""

import logging
import time
import requests
import json
import subprocess
from typing import Dict, Any, List, Optional

from llm_infer.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for running inference with Ollama local models."""
    
    def __init__(self, 
                 model_name: str = "llama2:7b", 
                 base_url: str = "http://localhost:11434",
                 timeout: int = 60,
                 auto_pull: bool = True):
        """
        Initialize the Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use (e.g., "llama2:7b", "codellama:7b")
            base_url: Base URL for Ollama API
            timeout: Request timeout in seconds
            auto_pull: Whether to automatically pull missing models
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.auto_pull = auto_pull
        self._check_connection()
    
    def _check_connection(self) -> None:
        """Check if Ollama is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama at {self.base_url}")
                self._ensure_model_available()
            else:
                logger.warning(f"Ollama API returned status {response.status_code}")
        except requests.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running.")
            raise ConnectionError(f"Ollama not accessible at {self.base_url}")
        except Exception as e:
            logger.error(f"Error checking Ollama connection: {e}")
            raise
    
    def _ensure_model_available(self) -> None:
        """Ensure the specified model is available, pull if necessary."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                if self.model_name in available_models:
                    logger.info(f"✅ Model {self.model_name} is available")
                    return
                
                # Model not found - try to pull it
                logger.warning(f"❌ Model {self.model_name} not found. Available models: {available_models}")
                
                if self.auto_pull:
                    logger.info(f"🔄 Attempting to pull model {self.model_name}...")
                    success = self._pull_model()
                    if not success:
                        # Suggest alternative models
                        self._suggest_alternatives(available_models)
                else:
                    logger.info(f"💡 To pull the model manually, run: ollama pull {self.model_name}")
                    self._suggest_alternatives(available_models)
                    
        except Exception as e:
            logger.warning(f"Could not check model availability: {e}")
    
    def _pull_model(self) -> bool:
        """
        Attempt to pull the missing model.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Pulling model {self.model_name}... This may take a few minutes.")
            
            # Use subprocess to run ollama pull command
            result = subprocess.run(
                ["ollama", "pull", self.model_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully pulled model {self.model_name}")
                return True
            else:
                logger.error(f"❌ Failed to pull model {self.model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Timeout pulling model {self.model_name} (5 minutes)")
            return False
        except FileNotFoundError:
            logger.error("❌ 'ollama' command not found. Make sure Ollama CLI is installed.")
            return False
        except Exception as e:
            logger.error(f"❌ Error pulling model {self.model_name}: {e}")
            return False
    
    def _suggest_alternatives(self, available_models: List[str]) -> None:
        """Suggest alternative models based on what's available."""
        if not available_models:
            logger.info("💡 No models currently installed. Popular starter models:")
            recommendations = [
                "llama3.2:1b (fast, lightweight)",
                "llama3.2:3b (good balance)",
                "codellama:7b (for code generation)",
                "mistral:7b (high quality)"
            ]
            for rec in recommendations:
                logger.info(f"   - {rec}")
            return
        
        # Find similar models
        model_base = self.model_name.split(':')[0]  # e.g., "llama3.2" from "llama3.2:3b"
        similar_models = [m for m in available_models if model_base in m]
        
        if similar_models:
            logger.info(f"💡 Similar available models: {similar_models}")
        else:
            logger.info(f"💡 Available models: {available_models[:3]}{'...' if len(available_models) > 3 else ''}")
    
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
            # Double-check model availability before inference
            if not self._is_model_available():
                error_msg = f"Model {self.model_name} is not available. Please pull it first: ollama pull {self.model_name}"
                logger.error(error_msg)
                return self._create_error_response(error_msg, time.time() - start_time)
            
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
                return self._create_error_response(error_msg, latency)
                
        except requests.Timeout:
            latency = time.time() - start_time
            error_msg = f"Request timeout after {self.timeout} seconds"
            logger.error(error_msg)
            return self._create_error_response(error_msg, latency)
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Error during Ollama inference: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(error_msg, latency)
    
    def _is_model_available(self) -> bool:
        """Check if the model is currently available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                return self.model_name in available_models
            return False
        except Exception:
            return False
    
    def _create_error_response(self, error_msg: str, latency: float) -> Dict[str, Any]:
        """Create a standardized error response."""
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
        """Get a list of popular Ollama models with descriptions."""
        return {
            "llama3.2:1b": {
                "name": "Llama 3.2 1B",
                "description": "Fast, lightweight model perfect for testing",
                "size": "~1.3GB",
                "use_case": "Quick testing, development"
            },
            "llama3.2:3b": {
                "name": "Llama 3.2 3B", 
                "description": "Good balance of speed and quality",
                "size": "~2.0GB",
                "use_case": "General purpose, balanced performance"
            },
            "llama3.1:8b": {
                "name": "Llama 3.1 8B",
                "description": "High quality responses, slower inference",
                "size": "~4.7GB",
                "use_case": "Production quality responses"
            },
            "codellama:7b": {
                "name": "Code Llama 7B",
                "description": "Specialized for code generation",
                "size": "~3.8GB",
                "use_case": "Code completion, programming tasks"
            },
            "mistral:7b": {
                "name": "Mistral 7B",
                "description": "High performance general model",
                "size": "~4.1GB",
                "use_case": "General purpose, high quality"
            },
            "phi3:mini": {
                "name": "Phi-3 Mini",
                "description": "Microsoft's efficient small model",
                "size": "~2.3GB",
                "use_case": "Efficient inference, good quality"
            }
        }

    @classmethod
    def is_ollama_available(cls, base_url: str = "http://localhost:11434") -> bool:
        """
        Check if Ollama is running and accessible.
        
        Args:
            base_url: Base URL for Ollama API
            
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    @classmethod
    def get_quick_start_model(cls) -> str:
        """Get the recommended model for quick start/testing."""
        return "llama3.2:1b"  # Fast, lightweight, good for demos 