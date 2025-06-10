"""Prometheus metrics exporter for LLM inference stress testing."""

import logging
import threading
import time
from typing import Dict, Any, Optional

from prometheus_client import (
    Counter, 
    Histogram, 
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collector for LLM stress testing."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None) -> None:
        """Initialize Prometheus metrics.
        
        Args:
            registry: Optional custom registry. Uses default if None.
        """
        # Create a fresh registry for each instance to avoid duplicates
        self.registry = CollectorRegistry()
        self._lock = threading.Lock()
        
        # Initialize metrics with labels
        self.request_counter = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['model', 'prompt_type', 'status'],
            registry=self.registry
        )
        
        self.failure_counter = Counter(
            'llm_failure_count',
            'Total number of failed LLM requests',
            ['model', 'prompt_type', 'error_type'],
            registry=self.registry
        )
        
        self.latency_histogram = Histogram(
            'llm_latency_seconds',
            'LLM request latency in seconds',
            ['model', 'prompt_type'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float('inf')),
            registry=self.registry
        )
        
        # Additional useful metrics
        self.token_counter = Counter(
            'llm_tokens_total',
            'Total number of tokens processed',
            ['model', 'prompt_type'],
            registry=self.registry
        )
        
        self.active_requests = Gauge(
            'llm_active_requests',
            'Number of currently active requests',
            ['model'],
            registry=self.registry
        )
        
        logger.info("Initialized Prometheus metrics")
    
    def record_request(
        self,
        model: str,
        prompt_type: str,
        latency: float,
        success: bool,
        error_type: Optional[str] = None,
        token_count: int = 0
    ) -> None:
        """Record metrics for a single LLM request.
        
        Args:
            model: Name of the LLM model used.
            prompt_type: Type of prompt (short_qa, long_form, code_generation).
            latency: Request latency in seconds.
            success: Whether the request was successful.
            error_type: Type of error if request failed.
            token_count: Number of tokens processed.
        """
        with self._lock:
            status = "success" if success else "failure"
            
            # Record request count
            self.request_counter.labels(
                model=model,
                prompt_type=prompt_type,
                status=status
            ).inc()
            
            # Record latency for successful requests
            if success:
                self.latency_histogram.labels(
                    model=model,
                    prompt_type=prompt_type
                ).observe(latency)
                
                # Record token count
                if token_count > 0:
                    self.token_counter.labels(
                        model=model,
                        prompt_type=prompt_type
                    ).inc(token_count)
            
            # Record failures
            if not success and error_type:
                self.failure_counter.labels(
                    model=model,
                    prompt_type=prompt_type,
                    error_type=error_type
                ).inc()
    
    def record_batch_results(self, results: list) -> None:
        """Record metrics for a batch of results.
        
        Args:
            results: List of result dictionaries from stress test.
        """
        for result in results:
            model = result.get("model", "unknown")
            # Extract prompt type from prompt or use default
            prompt_type = self._extract_prompt_type(result.get("prompt", ""))
            latency = result.get("latency", 0.0)
            success = result.get("success", False)
            error_type = self._categorize_error(result.get("error"))
            token_count = result.get("token_count", 0)
            
            self.record_request(
                model=model,
                prompt_type=prompt_type,
                latency=latency,
                success=success,
                error_type=error_type,
                token_count=token_count
            )
    
    def increment_active_requests(self, model: str) -> None:
        """Increment active request counter for a model.
        
        Args:
            model: Name of the model.
        """
        with self._lock:
            self.active_requests.labels(model=model).inc()
    
    def decrement_active_requests(self, model: str) -> None:
        """Decrement active request counter for a model.
        
        Args:
            model: Name of the model.
        """
        with self._lock:
            self.active_requests.labels(model=model).dec()
    
    def _extract_prompt_type(self, prompt: str) -> str:
        """Extract or infer prompt type from the prompt text.
        
        Args:
            prompt: The prompt text.
            
        Returns:
            Inferred prompt type.
        """
        if not prompt:
            return "unknown"
        
        prompt_lower = prompt.lower()
        
        # Simple heuristics to categorize prompts
        if any(keyword in prompt_lower for keyword in ["write", "essay", "explain", "describe", "analysis"]):
            if len(prompt) > 200:  # Long prompts are likely long-form
                return "long_form"
        
        if any(keyword in prompt_lower for keyword in ["function", "code", "python", "javascript", "sql", "script", "class"]):
            return "code_generation"
        
        # Default to short_qa for short questions
        if len(prompt) < 100 and "?" in prompt:
            return "short_qa"
        
        # If we can't determine, try to guess based on length
        if len(prompt) > 200:
            return "long_form"
        elif any(keyword in prompt_lower for keyword in ["write", "create", "implement"]):
            return "code_generation"
        else:
            return "short_qa"
    
    def _categorize_error(self, error_message: Optional[str]) -> Optional[str]:
        """Categorize error messages into types.
        
        Args:
            error_message: The error message to categorize.
            
        Returns:
            Categorized error type or None if no error.
        """
        if not error_message:
            return None
        
        error_lower = error_message.lower()
        
        if "rate limit" in error_lower:
            return "rate_limit"
        elif "timeout" in error_lower:
            return "timeout"
        elif "api" in error_lower and ("error" in error_lower or "invalid" in error_lower):
            return "api_error"
        elif "network" in error_lower or "connection" in error_lower:
            return "network_error"
        elif "authentication" in error_lower or "unauthorized" in error_lower:
            return "auth_error"
        else:
            return "unknown_error"
    
    def get_metrics(self) -> str:
        """Get current metrics in Prometheus format.
        
        Returns:
            Metrics data in Prometheus exposition format.
        """
        return generate_latest(self.registry).decode('utf-8')
    
    def get_content_type(self) -> str:
        """Get the content type for Prometheus metrics.
        
        Returns:
            Content type string for HTTP response.
        """
        return CONTENT_TYPE_LATEST
    
    def reset_metrics(self) -> None:
        """Reset all metrics. Useful for testing.
        
        Note: This creates a new registry and reinitializes all metrics.
        """
        logger.warning("Resetting all Prometheus metrics")
        self.registry = CollectorRegistry()
        self.__init__(registry=self.registry)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current statistics summary.
        
        Returns:
            Dictionary with current metric values.
        """
        metrics_text = self.get_metrics()
        
        # Parse basic stats from metrics (this is a simplified version)
        stats = {
            "total_requests": 0,
            "total_failures": 0,
            "active_requests": 0,
            "metrics_available": True
        }
        
        try:
            for line in metrics_text.split('\n'):
                if line.startswith('llm_requests_total') and not line.startswith('#'):
                    value = float(line.split(' ')[-1])
                    stats["total_requests"] += value
                elif line.startswith('llm_failure_count') and not line.startswith('#'):
                    value = float(line.split(' ')[-1])
                    stats["total_failures"] += value
                elif line.startswith('llm_active_requests') and not line.startswith('#'):
                    value = float(line.split(' ')[-1])
                    stats["active_requests"] += value
        except Exception as e:
            logger.error(f"Error parsing metrics: {e}")
            stats["metrics_available"] = False
        
        return stats 