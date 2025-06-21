"""Cost tracking and budgeting for LLM inference stress testing."""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class CostTier(Enum):
    """Cost tiers for different testing scenarios."""
    DEVELOPMENT = "development"
    DEMO = "demo"
    PRODUCTION = "production"


@dataclass
class TokenCost:
    """Token pricing structure for a model."""
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    currency: str = "USD"


@dataclass
class TestCost:
    """Cost breakdown for a single test."""
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    timestamp: str
    test_id: Optional[str] = None


@dataclass
class BudgetConfig:
    """Budget configuration for cost-aware testing."""
    daily_limit: float
    test_limit: float
    warning_threshold: float  # Percentage (0.8 = 80%)
    tier: CostTier
    auto_stop: bool = True


class CostTracker:
    """Tracks and manages costs for LLM API calls."""
    
    # Current pricing as of December 2024 (per 1K tokens)
    MODEL_PRICING = {
        # OpenAI Models
        "gpt-3.5-turbo": TokenCost(0.0015, 0.002),
        "gpt-3.5-turbo-1106": TokenCost(0.001, 0.002),
        "gpt-4": TokenCost(0.03, 0.06),
        "gpt-4-turbo": TokenCost(0.01, 0.03),
        "gpt-4-turbo-preview": TokenCost(0.01, 0.03),
        "gpt-4o": TokenCost(0.005, 0.015),
        "gpt-4o-mini": TokenCost(0.00015, 0.0006),
        
        # Anthropic Models
        "claude-3-haiku": TokenCost(0.00025, 0.00125),
        "claude-3-sonnet": TokenCost(0.003, 0.015),
        "claude-3-opus": TokenCost(0.015, 0.075),
        "claude-3-5-sonnet": TokenCost(0.003, 0.015),
        
        # Google Gemini Models
        "gemini-pro": TokenCost(0.0005, 0.0015),
        "gemini-pro-vision": TokenCost(0.0005, 0.0015),
        "gemini-1.5-pro": TokenCost(0.007, 0.021),
        "gemini-1.5-flash": TokenCost(0.00035, 0.00105),
        
        # Mock/Local Models (free)
        "mock-gpt-3.5": TokenCost(0.0, 0.0),
        "mock-gpt-4": TokenCost(0.0, 0.0),
        "local-model": TokenCost(0.0, 0.0),
        "ollama": TokenCost(0.0, 0.0),
    }
    
    # Predefined budget configurations
    BUDGET_TIERS = {
        CostTier.DEVELOPMENT: BudgetConfig(
            daily_limit=5.0,
            test_limit=1.0,
            warning_threshold=0.8,
            tier=CostTier.DEVELOPMENT,
            auto_stop=True
        ),
        CostTier.DEMO: BudgetConfig(
            daily_limit=25.0,
            test_limit=10.0,
            warning_threshold=0.75,
            tier=CostTier.DEMO,
            auto_stop=False
        ),
        CostTier.PRODUCTION: BudgetConfig(
            daily_limit=100.0,
            test_limit=50.0,
            warning_threshold=0.9,
            tier=CostTier.PRODUCTION,
            auto_stop=False
        )
    }
    
    def __init__(self, budget_tier: CostTier = CostTier.DEVELOPMENT) -> None:
        """Initialize cost tracker with budget configuration.
        
        Args:
            budget_tier: Budget tier for cost limits and warnings.
        """
        self.budget_config = self.BUDGET_TIERS[budget_tier]
        self.costs_history: List[TestCost] = []
        self.daily_costs: Dict[str, float] = {}  # date -> total_cost
        self.current_test_cost = 0.0
        
        # Load historical costs if available
        self._load_cost_history()
        
        logger.info(f"Initialized CostTracker with {budget_tier.value} tier")
        logger.info(f"Budget limits: ${self.budget_config.daily_limit}/day, "
                   f"${self.budget_config.test_limit}/test")
    
    def calculate_request_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> TestCost:
        """Calculate cost for a single API request.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3-sonnet').
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            
        Returns:
            TestCost object with detailed cost breakdown.
        """
        # Get pricing for model (default to gpt-3.5-turbo if unknown)
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["gpt-3.5-turbo"])
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        test_cost = TestCost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            timestamp=datetime.now().isoformat()
        )
        
        logger.debug(f"Calculated cost for {model}: ${total_cost:.4f} "
                    f"({input_tokens} in + {output_tokens} out tokens)")
        
        return test_cost
    
    def record_test_cost(self, test_cost: TestCost, test_id: str = None) -> None:
        """Record a test cost in history and update running totals.
        
        Args:
            test_cost: TestCost object to record.
            test_id: Optional test identifier.
        """
        test_cost.test_id = test_id
        self.costs_history.append(test_cost)
        self.current_test_cost += test_cost.total_cost
        
        # Update daily costs
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_costs[today] = self.daily_costs.get(today, 0) + test_cost.total_cost
        
        logger.info(f"Recorded cost: ${test_cost.total_cost:.4f} for {test_cost.model}")
        
        # Check budget warnings
        self._check_budget_warnings()
    
    def start_test(self) -> None:
        """Start a new test session, resetting current test cost."""
        self.current_test_cost = 0.0
        logger.debug("Started new test cost tracking session")
    
    def get_current_test_cost(self) -> float:
        """Get the cost of the current test session.
        
        Returns:
            Current test cost in USD.
        """
        return self.current_test_cost
    
    def get_daily_cost(self, date: str = None) -> float:
        """Get total cost for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Total cost for the date.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.daily_costs.get(date, 0.0)
    
    def estimate_test_cost(
        self,
        model: str,
        num_requests: int,
        avg_input_tokens: int = 50,
        avg_output_tokens: int = 100
    ) -> float:
        """Estimate cost for a planned stress test.
        
        Args:
            model: Model name.
            num_requests: Number of requests in the test.
            avg_input_tokens: Average input tokens per request.
            avg_output_tokens: Average output tokens per request.
            
        Returns:
            Estimated total cost.
        """
        single_request_cost = self.calculate_request_cost(
            model, avg_input_tokens, avg_output_tokens
        ).total_cost
        
        estimated_cost = single_request_cost * num_requests
        logger.info(f"Estimated test cost: ${estimated_cost:.4f} "
                   f"({num_requests} requests × ${single_request_cost:.4f})")
        
        return estimated_cost
    
    def can_afford_test(
        self,
        model: str,
        num_requests: int,
        avg_input_tokens: int = 50,
        avg_output_tokens: int = 100
    ) -> Tuple[bool, str]:
        """Check if a test is within budget limits.
        
        Args:
            model: Model name.
            num_requests: Number of requests in the test.
            avg_input_tokens: Average input tokens per request.
            avg_output_tokens: Average output tokens per request.
            
        Returns:
            Tuple of (can_afford, reason).
        """
        estimated_cost = self.estimate_test_cost(
            model, num_requests, avg_input_tokens, avg_output_tokens
        )
        
        # Check test limit
        if estimated_cost > self.budget_config.test_limit:
            return False, (f"Test cost ${estimated_cost:.2f} exceeds test limit "
                          f"${self.budget_config.test_limit:.2f}")
        
        # Check daily limit
        today_cost = self.get_daily_cost()
        if (today_cost + estimated_cost) > self.budget_config.daily_limit:
            remaining = self.budget_config.daily_limit - today_cost
            return False, (f"Test would exceed daily limit. "
                          f"${remaining:.2f} remaining today")
        
        return True, "Test within budget"
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive cost summary.
        
        Args:
            days: Number of days to include in summary.
            
        Returns:
            Dictionary with cost statistics and breakdowns.
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_costs = [
            cost for cost in self.costs_history
            if datetime.fromisoformat(cost.timestamp) >= cutoff_date
        ]
        
        if not recent_costs:
            return {
                "total_cost": 0.0,
                "avg_daily_cost": 0.0,
                "total_requests": 0,
                "avg_cost_per_request": 0.0,
                "model_breakdown": {},
                "daily_costs": {},
                "budget_status": self._get_budget_status()
            }
        
        total_cost = sum(cost.total_cost for cost in recent_costs)
        total_requests = len(recent_costs)
        
        # Model breakdown
        model_costs = {}
        for cost in recent_costs:
            if cost.model not in model_costs:
                model_costs[cost.model] = {"cost": 0.0, "requests": 0}
            model_costs[cost.model]["cost"] += cost.total_cost
            model_costs[cost.model]["requests"] += 1
        
        return {
            "total_cost": total_cost,
            "avg_daily_cost": total_cost / days,
            "total_requests": total_requests,
            "avg_cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
            "model_breakdown": model_costs,
            "daily_costs": dict(list(self.daily_costs.items())[-days:]),
            "budget_status": self._get_budget_status(),
            "current_test_cost": self.current_test_cost
        }
    
    def get_optimization_suggestions(self) -> List[str]:
        """Get cost optimization suggestions based on usage patterns.
        
        Returns:
            List of optimization suggestions.
        """
        suggestions = []
        summary = self.get_cost_summary(days=7)
        
        if summary["total_cost"] == 0:
            return ["Start tracking costs by running some tests!"]
        
        # Analyze model usage
        model_breakdown = summary["model_breakdown"]
        most_expensive_models = sorted(
            model_breakdown.items(),
            key=lambda x: x[1]["cost"],
            reverse=True
        )[:3]
        
        for model, stats in most_expensive_models:
            avg_cost = stats["cost"] / stats["requests"] if stats["requests"] > 0 else 0
            
            if "gpt-4" in model.lower() and avg_cost > 0.1:
                suggestions.append(
                    f"Consider using GPT-3.5-turbo instead of {model} for development testing "
                    f"(~10x cheaper: ${avg_cost:.3f} vs ~${avg_cost/10:.3f} per request)"
                )
            
            if stats["cost"] > summary["total_cost"] * 0.5:
                suggestions.append(
                    f"{model} accounts for {stats['cost']/summary['total_cost']*100:.1f}% "
                    f"of your costs. Consider using mock client for development"
                )
        
        # Budget warnings
        daily_usage = summary["avg_daily_cost"]
        if daily_usage > self.budget_config.daily_limit * 0.8:
            suggestions.append(
                f"Daily usage (${daily_usage:.2f}) approaching limit "
                f"(${self.budget_config.daily_limit:.2f}). Consider upgrading tier or optimizing tests"
            )
        
        # General optimization
        if summary["avg_cost_per_request"] > 0.01:
            suggestions.append(
                "Average cost per request is high. Try shorter prompts or cheaper models for development"
            )
        
        return suggestions or ["Your costs look optimized! 🎉"]
    
    def _check_budget_warnings(self) -> None:
        """Check budget limits and log warnings."""
        today_cost = self.get_daily_cost()
        daily_limit = self.budget_config.daily_limit
        test_limit = self.budget_config.test_limit
        
        # Daily budget warning
        if today_cost >= daily_limit * self.budget_config.warning_threshold:
            percentage = (today_cost / daily_limit) * 100
            logger.warning(f"Daily budget warning: ${today_cost:.2f} ({percentage:.1f}%) "
                          f"of ${daily_limit:.2f} limit used")
        
        # Test budget warning
        if self.current_test_cost >= test_limit * self.budget_config.warning_threshold:
            percentage = (self.current_test_cost / test_limit) * 100
            logger.warning(f"Test budget warning: ${self.current_test_cost:.2f} ({percentage:.1f}%) "
                          f"of ${test_limit:.2f} limit used")
    
    def _get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        today_cost = self.get_daily_cost()
        return {
            "daily_used": today_cost,
            "daily_limit": self.budget_config.daily_limit,
            "daily_remaining": max(0, self.budget_config.daily_limit - today_cost),
            "daily_percentage": min(100, (today_cost / self.budget_config.daily_limit) * 100),
            "test_used": self.current_test_cost,
            "test_limit": self.budget_config.test_limit,
            "test_remaining": max(0, self.budget_config.test_limit - self.current_test_cost),
            "test_percentage": min(100, (self.current_test_cost / self.budget_config.test_limit) * 100),
            "tier": self.budget_config.tier.value
        }
    
    def _load_cost_history(self) -> None:
        """Load cost history from file if available."""
        try:
            history_file = "results/cost_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.costs_history = [TestCost(**cost) for cost in data.get("costs", [])]
                    self.daily_costs = data.get("daily_costs", {})
                logger.info(f"Loaded {len(self.costs_history)} historical cost records")
        except Exception as e:
            logger.warning(f"Could not load cost history: {e}")
    
    def save_cost_history(self) -> None:
        """Save cost history to file."""
        try:
            os.makedirs("results", exist_ok=True)
            history_file = "results/cost_history.json"
            
            data = {
                "costs": [asdict(cost) for cost in self.costs_history],
                "daily_costs": self.daily_costs
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved cost history: {len(self.costs_history)} records")
        except Exception as e:
            logger.error(f"Could not save cost history: {e}") 