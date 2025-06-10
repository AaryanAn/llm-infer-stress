"""Prompt generator for different types of LLM stress tests."""

import logging
import random
from enum import Enum
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of prompts for stress testing."""
    SHORT_QA = "short_qa"
    LONG_FORM = "long_form"
    CODE_GENERATION = "code_generation"


class PromptGenerator:
    """Generator for different types of prompts for LLM stress testing."""
    
    def __init__(self) -> None:
        """Initialize the prompt generator with predefined prompt templates."""
        self._short_qa_prompts = [
            "What is the capital of France?",
            "Explain the concept of gravity in one sentence.",
            "What is 15 + 27?",
            "Name three programming languages.",
            "What year was the internet invented?",
            "Define artificial intelligence briefly.",
            "What is the largest planet in our solar system?",
            "How many sides does a hexagon have?",
            "What is the chemical symbol for gold?",
            "Name the four seasons.",
        ]
        
        self._long_form_prompts = [
            "Write a detailed essay about the impact of climate change on global agriculture, including specific examples and potential solutions.",
            "Explain the history and significance of the Renaissance period, covering art, science, and cultural developments.",
            "Describe the process of photosynthesis in plants, including the molecular mechanisms and environmental factors involved.",
            "Write a comprehensive analysis of the causes and consequences of World War II, focusing on major battles and political decisions.",
            "Explain the principles of machine learning, including different algorithms, applications, and ethical considerations.",
            "Describe the evolution of human language, from prehistoric communication to modern linguistic diversity.",
            "Write about the economic implications of cryptocurrency and blockchain technology on traditional financial systems.",
            "Explain the structure and function of the human brain, including neurotransmitters and cognitive processes.",
            "Describe the challenges and opportunities of space exploration in the 21st century.",
            "Write about the role of renewable energy in addressing global environmental challenges.",
        ]
        
        self._code_generation_prompts = [
            "Write a Python function that sorts a list of dictionaries by a specified key.",
            "Create a JavaScript function that validates an email address using regular expressions.",
            "Write a Python class to implement a simple stack data structure with push, pop, and peek methods.",
            "Create a SQL query to find the top 5 customers by total purchase amount from an e-commerce database.",
            "Write a Python function that calculates the Fibonacci sequence up to n terms.",
            "Create a JavaScript function that debounces user input with a specified delay.",
            "Write a Python script that reads a CSV file and calculates basic statistics for numeric columns.",
            "Create a function in any language that implements binary search on a sorted array.",
            "Write a Python decorator that measures and logs the execution time of functions.",
            "Create a REST API endpoint using Flask that handles user authentication and returns JSON responses.",
        ]
        
        logger.info("Initialized PromptGenerator with predefined prompt templates")
    
    def get_prompt(self, prompt_type: PromptType, custom_prompt: str = None) -> str:
        """Get a prompt of the specified type.
        
        Args:
            prompt_type: The type of prompt to generate.
            custom_prompt: Optional custom prompt to use instead of predefined ones.
            
        Returns:
            A prompt string of the specified type.
            
        Raises:
            ValueError: If prompt_type is not supported.
        """
        if custom_prompt:
            logger.debug(f"Using custom prompt: {custom_prompt[:50]}...")
            return custom_prompt
        
        if prompt_type == PromptType.SHORT_QA:
            prompt = random.choice(self._short_qa_prompts)
        elif prompt_type == PromptType.LONG_FORM:
            prompt = random.choice(self._long_form_prompts)
        elif prompt_type == PromptType.CODE_GENERATION:
            prompt = random.choice(self._code_generation_prompts)
        else:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
        
        logger.debug(f"Generated {prompt_type.value} prompt: {prompt[:50]}...")
        return prompt
    
    def get_multiple_prompts(
        self, 
        prompt_type: PromptType, 
        count: int,
        allow_duplicates: bool = True
    ) -> List[str]:
        """Get multiple prompts of the specified type.
        
        Args:
            prompt_type: The type of prompts to generate.
            count: Number of prompts to generate.
            allow_duplicates: Whether to allow duplicate prompts.
            
        Returns:
            List of prompt strings.
            
        Raises:
            ValueError: If count is invalid or prompt_type is not supported.
        """
        if count <= 0:
            raise ValueError("Count must be greater than 0")
        
        prompts = []
        available_prompts = self._get_prompts_by_type(prompt_type)
        
        if not allow_duplicates and count > len(available_prompts):
            raise ValueError(
                f"Cannot generate {count} unique prompts of type {prompt_type.value}. "
                f"Only {len(available_prompts)} available."
            )
        
        if allow_duplicates:
            prompts = [random.choice(available_prompts) for _ in range(count)]
        else:
            prompts = random.sample(available_prompts, count)
        
        logger.info(f"Generated {len(prompts)} {prompt_type.value} prompts")
        return prompts
    
    def _get_prompts_by_type(self, prompt_type: PromptType) -> List[str]:
        """Get the list of prompts for a given type.
        
        Args:
            prompt_type: The type of prompts to retrieve.
            
        Returns:
            List of prompt strings for the specified type.
            
        Raises:
            ValueError: If prompt_type is not supported.
        """
        if prompt_type == PromptType.SHORT_QA:
            return self._short_qa_prompts
        elif prompt_type == PromptType.LONG_FORM:
            return self._long_form_prompts
        elif prompt_type == PromptType.CODE_GENERATION:
            return self._code_generation_prompts
        else:
            raise ValueError(f"Unsupported prompt type: {prompt_type}")
    
    def get_available_types(self) -> List[str]:
        """Get list of available prompt types.
        
        Returns:
            List of available prompt type names.
        """
        return [prompt_type.value for prompt_type in PromptType]
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """Get information about available prompts.
        
        Returns:
            Dictionary with prompt type statistics.
        """
        return {
            "available_types": self.get_available_types(),
            "short_qa_count": len(self._short_qa_prompts),
            "long_form_count": len(self._long_form_prompts),
            "code_generation_count": len(self._code_generation_prompts),
            "total_prompts": (
                len(self._short_qa_prompts) + 
                len(self._long_form_prompts) + 
                len(self._code_generation_prompts)
            )
        } 