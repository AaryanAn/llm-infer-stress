"""Hugging Face local model client for LLM inference stress testing."""

import logging
import time
import warnings
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from llm_infer.utils import setup_logging

# Suppress specific warnings that can clutter logs
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

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
        self.device_info = self._get_device_info()
        self._initialize_model()
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get device and PyTorch compatibility information."""
        info = {
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device": "cpu",
            "dtype": torch.float32,
            "mps_available": hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        }
        
        # Determine best device and dtype
        if info["cuda_available"]:
            info["device"] = "cuda"
            info["dtype"] = torch.float16  # Use FP16 on GPU
        elif info["mps_available"]:
            info["device"] = "mps"  # Apple Silicon
            info["dtype"] = torch.float32  # MPS doesn't support FP16 well
        else:
            info["device"] = "cpu"
            info["dtype"] = torch.float32  # Always use FP32 on CPU
        
        logger.info(f"🔧 PyTorch {info['torch_version']}, Device: {info['device']}, Dtype: {info['dtype']}")
        return info
    
    def _initialize_model(self) -> None:
        """Initialize the model and tokenizer with enhanced compatibility."""
        try:
            logger.info(f"🚀 Loading Hugging Face model: {self.model_name}")
            
            # Load tokenizer first
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=False  # Use slow tokenizer for better compatibility
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                logger.info("Added padding token (using EOS token)")
            
            # Prepare model loading arguments for CPU compatibility
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": self.device_info["dtype"],
                "low_cpu_mem_usage": True,  # Important for CPU inference
            }
            
            # CPU-specific optimizations
            if self.device_info["device"] == "cpu":
                model_kwargs.update({
                    "device_map": None,  # Don't use device_map on CPU
                    "torch_dtype": torch.float32,  # Force FP32 on CPU
                })
                logger.info("🔧 Using CPU optimizations (FP32, no device_map)")
            
            # Create pipeline with enhanced error handling
            try:
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model_name,
                    tokenizer=self.tokenizer,
                    device=0 if self.device_info["device"] == "cuda" else -1,
                    model_kwargs=model_kwargs,
                    do_sample=True,
                    temperature=0.7,
                    max_new_tokens=min(self.max_length, 100),  # Conservative limit
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False  # Only return generated text
                )
                
                logger.info(f"✅ Successfully loaded model: {self.model_name}")
                
            except Exception as pipeline_error:
                logger.warning(f"Pipeline creation failed: {pipeline_error}")
                logger.info("🔄 Attempting fallback model loading...")
                self._initialize_fallback_model()
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Hugging Face model: {e}")
            logger.info("💡 Consider using a smaller model like 'distilgpt2' or 'microsoft/DialoGPT-small'")
            raise
    
    def _initialize_fallback_model(self) -> None:
        """Initialize with a more conservative approach for problematic models."""
        try:
            # Load model and tokenizer separately with maximum compatibility
            logger.info("🔄 Using fallback initialization method...")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,  # Always use FP32 for compatibility
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                device_map=None  # No automatic device mapping
            )
            
            # Move to CPU explicitly
            self.model = self.model.to('cpu')
            self.model.eval()  # Set to evaluation mode
            
            logger.info("✅ Fallback model loading successful")
            
        except Exception as e:
            logger.error(f"❌ Fallback model loading also failed: {e}")
            raise
    
    def run_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Run inference on the given prompt with enhanced error handling.
        
        Args:
            prompt: The input prompt text
            
        Returns:
            Dictionary containing response, latency, tokens, and metadata
        """
        start_time = time.time()
        
        try:
            # Prepare the prompt
            formatted_prompt = f"Human: {prompt}\nAssistant:"
            
            if self.pipeline is not None:
                # Use pipeline if available
                result = self._run_with_pipeline(formatted_prompt)
            elif self.model is not None:
                # Use direct model inference as fallback
                result = self._run_with_model(formatted_prompt)
            else:
                raise RuntimeError("No model or pipeline available")
            
            # Calculate metrics
            latency = time.time() - start_time
            
            # Count tokens safely
            try:
                input_tokens = len(self.tokenizer.encode(prompt))
                output_tokens = len(self.tokenizer.encode(result))
                total_tokens = input_tokens + output_tokens
            except Exception:
                # Fallback token counting
                input_tokens = len(prompt.split()) * 1.3
                output_tokens = len(result.split()) * 1.3
                total_tokens = int(input_tokens + output_tokens)
                input_tokens = int(input_tokens)
                output_tokens = int(output_tokens)
            
            return {
                "response": result,
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "model": self.model_name,
                "error": None,
                "metadata": {
                    "device": self.device_info["device"],
                    "dtype": str(self.device_info["dtype"]),
                    "torch_version": self.device_info["torch_version"],
                    "max_length": self.max_length,
                    "temperature": 0.7,
                    "backend": "huggingface"
                }
            }
            
        except Exception as e:
            latency = time.time() - start_time
            error_msg = f"Error during Hugging Face inference: {str(e)}"
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
                "metadata": {
                    "device": self.device_info["device"],
                    "dtype": str(self.device_info["dtype"]),
                    "torch_version": self.device_info["torch_version"],
                    "max_length": self.max_length,
                    "temperature": 0.7,
                    "backend": "huggingface"
                }
            }
    
    def _run_with_pipeline(self, formatted_prompt: str) -> str:
        """Run inference using the pipeline."""
        try:
            result = self.pipeline(
                formatted_prompt,
                max_new_tokens=min(self.max_length, 50),  # Conservative limit
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', '')
                # Remove the original prompt from the response
                if formatted_prompt in generated_text:
                    response = generated_text[len(formatted_prompt):].strip()
                else:
                    response = generated_text.strip()
                return response
            else:
                return "No response generated"
                
        except Exception as e:
            logger.warning(f"Pipeline inference failed: {e}")
            raise
    
    def _run_with_model(self, formatted_prompt: str) -> str:
        """Run inference using direct model calls (fallback)."""
        try:
            # Tokenize input
            inputs = self.tokenizer.encode(formatted_prompt, return_tensors='pt')
            
            # Generate with conservative settings
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=min(self.max_length, 30),  # Very conservative
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs)  # Explicit attention mask
                )
            
            # Decode output
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt from the response
            if formatted_prompt in generated_text:
                response = generated_text[len(formatted_prompt):].strip()
            else:
                response = generated_text.strip()
                
            return response
            
        except Exception as e:
            logger.warning(f"Direct model inference failed: {e}")
            raise


class LocalModelClient(HuggingFaceClient):
    """Convenient wrapper for common local models."""
    
    # Popular local models that work well for conversation
    SUPPORTED_MODELS = {
        "distilgpt2": {
            "name": "DistilGPT-2",
            "description": "Lightweight, fast, good compatibility",
            "size": "~320MB",
            "compatibility": "excellent"
        },
        "microsoft/DialoGPT-small": {
            "name": "DialoGPT Small", 
            "description": "Small conversational model, very fast",
            "size": "~150MB",
            "compatibility": "excellent"
        },
        "microsoft/DialoGPT-medium": {
            "name": "DialoGPT Medium",
            "description": "Conversational AI model, good for chat",
            "size": "~400MB",
            "compatibility": "good"
        },
        "gpt2": {
            "name": "GPT-2",
            "description": "Original GPT-2 model, reliable",
            "size": "~500MB",
            "compatibility": "excellent"
        },
        "gpt2-medium": {
            "name": "GPT-2 Medium",
            "description": "Larger GPT-2 model, better quality",
            "size": "~1.5GB",
            "compatibility": "good"
        },
        "microsoft/CodeGPT-small-py": {
            "name": "CodeGPT Python",
            "description": "Code generation model for Python",
            "size": "~500MB",
            "compatibility": "good"
        },
        "EleutherAI/gpt-neo-125M": {
            "name": "GPT-Neo 125M",
            "description": "Open source GPT-like model",
            "size": "~500MB",
            "compatibility": "fair"
        }
    }
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, str]]:
        """Get list of supported local models."""
        return cls.SUPPORTED_MODELS
    
    @classmethod
    def get_recommended_model(cls) -> str:
        """Get the most compatible model for testing."""
        return "distilgpt2"  # Best compatibility and speed
    
    @classmethod
    def create_client(cls, model_key: str, max_length: int = 512) -> 'LocalModelClient':
        """
        Create a client with a supported model.
        
        Args:
            model_key: Key from SUPPORTED_MODELS
            max_length: Maximum response length
            
        Returns:
            LocalModelClient instance
        """
        if model_key not in cls.SUPPORTED_MODELS:
            available = list(cls.SUPPORTED_MODELS.keys())
            raise ValueError(f"Model {model_key} not supported. Available: {available}")
        
        return cls(model_name=model_key, max_length=max_length) 