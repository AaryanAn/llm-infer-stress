"""Hugging Face local model client for LLM inference stress testing."""

import logging
import time
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from llm_infer.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class HuggingFaceClient:
    """Client for running inference with local Hugging Face models."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", max_length: int = 512):
        """
        Initialize the Hugging Face client.
        
        Args:
            model_name: Name of the Hugging Face model to use
            max_length: Maximum length for generated responses
        """
        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize the model and tokenizer."""
        try:
            logger.info(f"Loading Hugging Face model: {self.model_name}")
            
            # Check if CUDA is available
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"Using device: {device_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Create pipeline for text generation
            self.pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=device,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                do_sample=True,
                temperature=0.7,
                max_new_tokens=self.max_length,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info(f"Successfully loaded model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face model: {e}")
            raise
    
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
            # Prepare the prompt
            formatted_prompt = f"Human: {prompt}\nAssistant:"
            
            # Generate response
            result = self.pipeline(
                formatted_prompt,
                max_new_tokens=min(self.max_length, 200),
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            generated_text = result[0]['generated_text']
            
            # Remove the original prompt from the response
            if formatted_prompt in generated_text:
                response = generated_text[len(formatted_prompt):].strip()
            else:
                response = generated_text.strip()
            
            # Calculate metrics
            latency = time.time() - start_time
            
            # Count tokens
            input_tokens = len(self.tokenizer.encode(prompt))
            output_tokens = len(self.tokenizer.encode(response))
            total_tokens = input_tokens + output_tokens
            
            return {
                "response": response,
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "model": self.model_name,
                "error": None,
                "metadata": {
                    "device": "GPU" if torch.cuda.is_available() else "CPU",
                    "max_length": self.max_length,
                    "temperature": 0.7
                }
            }
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"Error during Hugging Face inference: {e}")
            
            return {
                "response": "",
                "success": False,
                "latency": latency,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "model": self.model_name,
                "error": str(e),
                "metadata": {
                    "device": "GPU" if torch.cuda.is_available() else "CPU",
                    "max_length": self.max_length,
                    "temperature": 0.7
                }
            }


class LocalModelClient(HuggingFaceClient):
    """Convenient wrapper for common local models."""
    
    # Popular local models that work well for conversation
    SUPPORTED_MODELS = {
        "microsoft/DialoGPT-small": {
            "name": "DialoGPT Small", 
            "description": "Smaller conversational model, fastest inference",
            "size": "~150MB"
        },
        "microsoft/DialoGPT-medium": {
            "name": "DialoGPT Medium",
            "description": "Conversational AI model, good for chat",
            "size": "~400MB"
        },
        "distilgpt2": {
            "name": "DistilGPT-2",
            "description": "Distilled GPT-2, good balance of size/performance",
            "size": "~320MB"
        },
        "gpt2": {
            "name": "GPT-2",
            "description": "Original GPT-2 model, good text generation",
            "size": "~500MB"
        },
        "gpt2-medium": {
            "name": "GPT-2 Medium",
            "description": "Larger GPT-2 model, better quality",
            "size": "~1.5GB"
        },
        "microsoft/CodeGPT-small-java": {
            "name": "CodeGPT Java",
            "description": "Code generation model specialized for Java",
            "size": "~500MB"
        },
        "microsoft/CodeGPT-small-py": {
            "name": "CodeGPT Python",
            "description": "Code generation model specialized for Python",
            "size": "~500MB"
        },
        "EleutherAI/gpt-neo-125M": {
            "name": "GPT-Neo 125M",
            "description": "Open source GPT-like model by EleutherAI",
            "size": "~500MB"
        }
    }
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, str]]:
        """Get list of supported local models."""
        return cls.SUPPORTED_MODELS
    
    @classmethod
    def create_client(cls, model_key: str, max_length: int = 512) -> 'LocalModelClient':
        """
        Create a client for a supported local model.
        
        Args:
            model_key: Key from SUPPORTED_MODELS
            max_length: Maximum response length
            
        Returns:
            LocalModelClient instance
        """
        if model_key not in cls.SUPPORTED_MODELS:
            raise ValueError(f"Model {model_key} not supported. Available models: {list(cls.SUPPORTED_MODELS.keys())}")
        
        return cls(model_name=model_key, max_length=max_length) 