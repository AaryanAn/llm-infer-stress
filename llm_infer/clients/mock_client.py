"""Mock client for testing LLM stress testing without API costs."""

import logging
import random
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockClient:
    """Mock LLM client for testing without API costs."""
    
    def __init__(
        self, 
        model: str = "mock-model",
        simulate_latency: bool = True,
        error_rate: float = 0.1  # 10% error rate for realistic testing
    ) -> None:
        """Initialize mock client.
        
        Args:
            model: Model name to simulate.
            simulate_latency: Whether to simulate realistic response times.
            error_rate: Probability of simulating errors (0.0 to 1.0).
        """
        self.model = model
        self.simulate_latency = simulate_latency
        self.error_rate = error_rate
        
        logger.info(f"Initialized Mock client with model: {self.model}")
    
    def run_prompt(self, prompt: str) -> Dict[str, Any]:
        """Simulate running a prompt against an LLM.
        
        Args:
            prompt: The prompt text to send to the model.
            
        Returns:
            Dict containing simulated response data.
        """
        start_time = time.time()
        
        # Simulate processing time
        if self.simulate_latency:
            # Realistic latency: 0.5-3.0 seconds based on prompt length
            base_latency = 0.5 + (len(prompt) / 1000) * 2.0
            latency = base_latency + random.uniform(0, 0.5)
            time.sleep(latency)
        
        end_time = time.time()
        actual_latency = end_time - start_time
        
        # Simulate occasional errors
        if random.random() < self.error_rate:
            return self._generate_error_response(prompt, actual_latency)
        
        # Generate successful response
        return self._generate_success_response(prompt, actual_latency)
    
    def _generate_success_response(self, prompt: str, latency: float) -> Dict[str, Any]:
        """Generate a successful mock response."""
        # Simulate different response types based on prompt
        if "code" in prompt.lower() or "function" in prompt.lower():
            response = self._generate_code_response(prompt)
            token_count = len(response.split()) * 2  # Rough estimate
        elif len(prompt) > 200:  # Long form
            response = self._generate_long_response(prompt)
            token_count = len(response.split()) * 1.5
        else:  # Short QA
            response = self._generate_short_response(prompt)
            token_count = len(response.split())
        
        return {
            "response": response,
            "latency": latency,
            "success": True,
            "error": None,
            "model": self.model,
            "input_tokens": len(prompt.split()),
            "output_tokens": int(token_count),
            "total_tokens": len(prompt.split()) + int(token_count),
            "metadata": {"backend": "mock"}
        }
    
    def _generate_error_response(self, prompt: str, latency: float) -> Dict[str, Any]:
        """Generate a mock error response."""
        error_types = [
            "Rate limit exceeded: Mock rate limit for testing",
            "Request timeout: Mock timeout error",
            "API error: Mock API error for testing",
            "Network error: Mock network issue"
        ]
        
        return {
            "response": "",
            "latency": latency,
            "success": False,
            "error": random.choice(error_types),
            "model": self.model,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "metadata": {"backend": "mock"}
        }
    
    def _generate_code_response(self, prompt: str) -> str:
        """Generate mock code response."""
        examples = [
            "def example_function(x):\n    return x * 2\n\n# This function doubles the input value",
            "const validateEmail = (email) => {\n    const regex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;\n    return regex.test(email);\n};",
            "SELECT customers.name, SUM(orders.amount) as total\nFROM customers\nJOIN orders ON customers.id = orders.customer_id\nGROUP BY customers.name\nORDER BY total DESC\nLIMIT 5;",
            "class Stack:\n    def __init__(self):\n        self.items = []\n    \n    def push(self, item):\n        self.items.append(item)\n    \n    def pop(self):\n        return self.items.pop() if self.items else None"
        ]
        return random.choice(examples)
    
    def _generate_long_response(self, prompt: str) -> str:
        """Generate mock long-form response."""
        examples = [
            "Climate change represents one of the most significant challenges facing global agriculture today. Rising temperatures, changing precipitation patterns, and increased frequency of extreme weather events are affecting crop yields worldwide. For example, wheat production in Australia has declined by 27% since 1990 due to reduced rainfall. Potential solutions include developing drought-resistant crop varieties, implementing precision agriculture techniques, and adopting sustainable farming practices that build soil health and resilience.",
            "The Renaissance period, spanning roughly from the 14th to the 17th century, marked a profound transformation in European culture, art, and science. This era saw the emergence of humanistic philosophy, revolutionary artistic techniques like linear perspective, and groundbreaking scientific discoveries. Artists like Leonardo da Vinci and Michelangelo created masterpieces that still inspire us today, while scientists like Galileo challenged traditional views of the cosmos. The Renaissance represented a bridge between medieval and modern thinking.",
            "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. Key algorithms include supervised learning (like decision trees and neural networks), unsupervised learning (such as clustering), and reinforcement learning. Applications range from image recognition and natural language processing to recommendation systems and autonomous vehicles. However, ethical considerations around bias, privacy, and transparency remain important challenges in the field."
        ]
        return random.choice(examples)
    
    def _generate_short_response(self, prompt: str) -> str:
        """Generate mock short response."""
        examples = [
            "Paris is the capital of France.",
            "Gravity is the force that attracts objects toward the center of the Earth.",
            "15 + 27 = 42",
            "Three popular programming languages are Python, JavaScript, and Java.",
            "The internet was invented in 1969 with ARPANET.",
            "Artificial intelligence is the simulation of human intelligence by machines.",
            "Jupiter is the largest planet in our solar system.",
            "A hexagon has six sides.",
            "The chemical symbol for gold is Au.",
            "The four seasons are spring, summer, autumn (fall), and winter."
        ]
        return random.choice(examples) 