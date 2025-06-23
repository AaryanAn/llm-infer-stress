"""Utility functions for LLM inference stress testing."""

import logging
import os
import sys
from typing import Dict, Any, List, Optional


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured at %s level", logging.getLevelName(level))


class ModelManager:
    """Intelligent model management and recommendation system."""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information for model recommendations."""
        import psutil
        
        info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": os.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "available_memory_gb": round(psutil.virtual_memory().available / (1024**3), 1)
        }
        
        # Try to import torch safely
        try:
            import torch
            info["torch_version"] = torch.__version__
            info["cuda_available"] = torch.cuda.is_available()
            info["mps_available"] = hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
            
            if info["cuda_available"]:
                info["gpu_name"] = torch.cuda.get_device_name(0)
                info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
        except ImportError:
            info["torch_version"] = "not installed"
            info["cuda_available"] = False
            info["mps_available"] = False
        except Exception:
            # PyTorch import/CUDA check failed - safe fallback
            info["torch_version"] = "import failed"
            info["cuda_available"] = False
            info["mps_available"] = False
        
        return info
    
    @staticmethod
    def recommend_models() -> Dict[str, List[Dict[str, str]]]:
        """Recommend models based on system capabilities."""
        system_info = ModelManager.get_system_info()
        recommendations = {
            "ollama": [],
            "huggingface": [],
            "priority": "mock"  # Default safe option
        }
        
        # Memory-based recommendations
        memory_gb = system_info["available_memory_gb"]
        
        # Ollama recommendations
        if memory_gb >= 8:
            recommendations["ollama"].extend([
                {"model": "llama3.2:3b", "reason": "Good balance, fits in 8GB RAM"},
                {"model": "mistral:7b", "reason": "High quality, requires 8GB+ RAM"},
                {"model": "codellama:7b", "reason": "Code-specialized, 8GB+ RAM"}
            ])
            recommendations["priority"] = "ollama"
        elif memory_gb >= 4:
            recommendations["ollama"].extend([
                {"model": "llama3.2:1b", "reason": "Lightweight, fast, fits in 4GB RAM"},
                {"model": "phi3:mini", "reason": "Efficient Microsoft model, 4GB RAM"}
            ])
            recommendations["priority"] = "ollama"
        else:
            recommendations["ollama"].append({
                "model": "llama3.2:1b", 
                "reason": "Only lightweight model recommended for <4GB RAM"
            })
        
        # HuggingFace recommendations
        if memory_gb >= 4:
            recommendations["huggingface"].extend([
                {"model": "distilgpt2", "reason": "Most compatible, reliable"},
                {"model": "microsoft/DialoGPT-small", "reason": "Fast conversational model"},
                {"model": "gpt2", "reason": "Reliable, well-tested"}
            ])
        else:
            recommendations["huggingface"].extend([
                {"model": "distilgpt2", "reason": "Lightweight, best for low memory"},
                {"model": "microsoft/DialoGPT-small", "reason": "Smallest conversational model"}
            ])
        
        # Adjust priority based on GPU availability
        if system_info["cuda_available"] and memory_gb >= 8:
            recommendations["priority"] = "ollama"  # Prefer Ollama with GPU
        elif memory_gb < 2:
            recommendations["priority"] = "mock"  # Too little memory for local models
        
        return recommendations
    
    @staticmethod
    def check_ollama_status() -> Dict[str, Any]:
        """Check Ollama installation and running status."""
        from llm_infer.clients.ollama_client import OllamaClient
        
        status = {
            "installed": False,
            "running": False,
            "models": [],
            "recommended_action": ""
        }
        
        try:
            # Check if Ollama is running
            if OllamaClient.is_ollama_available():
                status["running"] = True
                status["installed"] = True
                
                # Get available models
                client = OllamaClient(model_name="dummy")  # Dummy model name
                models = client.list_available_models()
                status["models"] = [model.get("name", "unknown") for model in models]
                
                if not status["models"]:
                    status["recommended_action"] = f"Pull a model: ollama pull {OllamaClient.get_quick_start_model()}"
                else:
                    status["recommended_action"] = "Ready to use!"
            else:
                status["recommended_action"] = "Start Ollama: ollama serve"
                
        except Exception as e:
            status["recommended_action"] = f"Install Ollama from https://ollama.ai/ - Error: {str(e)}"
        
        return status
    
    @staticmethod
    def get_best_available_client() -> Dict[str, Any]:
        """Get the best available client configuration based on current system state."""
        recommendations = ModelManager.recommend_models()
        ollama_status = ModelManager.check_ollama_status()
        
        # Try Ollama first if it's running and has models
        if ollama_status["running"] and ollama_status["models"]:
            available_models = ollama_status["models"]
            
            # Find the best model from recommendations that's actually available
            for rec in recommendations["ollama"]:
                if rec["model"] in available_models:
                    return {
                        "type": "ollama",
                        "model": rec["model"],
                        "reason": f"Ollama running with {rec['model']} - {rec['reason']}",
                        "config": {"model_name": rec["model"], "auto_pull": True}
                    }
            
            # If no recommended models available, use the first available one
            if available_models:
                return {
                    "type": "ollama", 
                    "model": available_models[0],
                    "reason": f"Using available Ollama model: {available_models[0]}",
                    "config": {"model_name": available_models[0], "auto_pull": True}
                }
        
        # Try HuggingFace models
        try:
            from llm_infer.clients.huggingface_client import LocalModelClient
            recommended_model = LocalModelClient.get_recommended_model()
            
            return {
                "type": "huggingface",
                "model": recommended_model,
                "reason": f"HuggingFace {recommended_model} - most compatible local model",
                "config": {"model_name": recommended_model, "max_length": 256}
            }
        except Exception:
            pass
        
        # Fallback to mock client
        return {
            "type": "mock",
            "model": "mock-gpt-3.5",
            "reason": "Mock client - safe fallback, no model downloads required",
            "config": {"model_name": "mock-gpt-3.5"}
        }
    
    @staticmethod
    def print_system_report() -> None:
        """Print a comprehensive system report with recommendations."""
        logger = logging.getLogger(__name__)
        
        logger.info("🔍 System Analysis Report")
        logger.info("=" * 50)
        
        # System info
        system_info = ModelManager.get_system_info()
        logger.info(f"💻 Platform: {system_info['platform']}")
        logger.info(f"🧠 Memory: {system_info['available_memory_gb']:.1f}GB available / {system_info['memory_gb']:.1f}GB total")
        logger.info(f"⚡ CPU Cores: {system_info['cpu_count']}")
        
        if system_info["cuda_available"]:
            logger.info(f"🚀 GPU: {system_info.get('gpu_name', 'Unknown')} ({system_info.get('gpu_memory_gb', 0):.1f}GB)")
        elif system_info["mps_available"]:
            logger.info("🍎 Apple Silicon GPU (MPS) available")
        else:
            logger.info("💾 CPU-only inference")
        
        # Ollama status
        logger.info("\n🦙 Ollama Status:")
        ollama_status = ModelManager.check_ollama_status()
        if ollama_status["running"]:
            logger.info(f"✅ Running with {len(ollama_status['models'])} models: {ollama_status['models']}")
        else:
            logger.info(f"❌ Not running - {ollama_status['recommended_action']}")
        
        # Recommendations
        logger.info("\n💡 Recommendations:")
        recommendations = ModelManager.recommend_models()
        
        logger.info(f"🎯 Priority: {recommendations['priority'].upper()}")
        
        if recommendations["ollama"]:
            logger.info("🦙 Ollama models:")
            for rec in recommendations["ollama"][:3]:  # Top 3
                logger.info(f"   - {rec['model']}: {rec['reason']}")
        
        if recommendations["huggingface"]:
            logger.info("🤗 HuggingFace models:")
            for rec in recommendations["huggingface"][:3]:  # Top 3
                logger.info(f"   - {rec['model']}: {rec['reason']}")
        
        # Best available
        best = ModelManager.get_best_available_client()
        logger.info(f"\n🌟 Best Available: {best['type'].upper()} - {best['model']}")
        logger.info(f"   Reason: {best['reason']}")
        
        logger.info("=" * 50)


def validate_environment_variables() -> dict:
    """Validate that required environment variables are set.
    
    Returns:
        Dictionary with validation results.
    """
    import os
    
    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY")
    }
    
    results = {
        "all_set": True,
        "missing": [],
        "present": []
    }
    
    for var_name, var_value in required_vars.items():
        if var_value:
            results["present"].append(var_name)
        else:
            results["missing"].append(var_name)
            results["all_set"] = False
    
    return results


def format_bytes(bytes_value: int) -> str:
    """Format byte count as human-readable string.
    
    Args:
        bytes_value: Number of bytes.
        
    Returns:
        Formatted string (e.g., "1.5 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds as human-readable string.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted string (e.g., "2m 30s").
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s" 