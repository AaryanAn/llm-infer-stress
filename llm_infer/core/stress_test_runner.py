"""Stress test runner for LLM inference benchmarking."""

import asyncio
import csv
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable

from ..clients.openai_client import OpenAIClient
from .prompt_generator import PromptGenerator, PromptType
from .cost_tracker import CostTracker, CostTier

logger = logging.getLogger(__name__)


@dataclass
class StressTestConfig:
    """Configuration for stress test execution."""
    num_requests: int = 10
    concurrent_requests: int = 1
    prompt_type: PromptType = PromptType.SHORT_QA
    custom_prompts: Optional[List[str]] = None
    save_results: bool = True
    output_format: str = "json"  # "json" or "csv"
    output_dir: str = "results"
    test_name: Optional[str] = None
    budget_tier: CostTier = CostTier.DEVELOPMENT
    max_cost: Optional[float] = None  # Override budget limits


@dataclass
class StressTestResults:
    """Results from a stress test run."""
    test_name: str
    start_time: str
    end_time: str
    total_duration: float
    config: StressTestConfig
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    min_latency: float
    max_latency: float
    avg_latency: float
    median_latency: float
    p95_latency: float
    total_tokens: int
    requests_per_second: float
    errors: Dict[str, int]
    individual_results: List[Dict[str, Any]]
    total_cost: float = 0.0
    avg_cost_per_request: float = 0.0
    cost_breakdown: Dict[str, Any] = None


class StressTestRunner:
    """Runner for LLM inference stress tests."""
    
    def __init__(self, client: OpenAIClient, prompt_generator: PromptGenerator, 
                 cost_tracker: Optional[CostTracker] = None) -> None:
        """Initialize the stress test runner.
        
        Args:
            client: LLM client to test (currently supports OpenAIClient).
            prompt_generator: Generator for test prompts.
            cost_tracker: Optional cost tracker for budget management.
        """
        self.client = client
        self.prompt_generator = prompt_generator
        self.cost_tracker = cost_tracker
        logger.info("Initialized StressTestRunner")
    
    def run_stress_test(self, config: StressTestConfig) -> StressTestResults:
        """Run a stress test with the given configuration.
        
        Args:
            config: Configuration for the stress test.
            
        Returns:
            StressTestResults containing all metrics and results.
        """
        logger.info(f"Starting stress test with {config.num_requests} requests, "
                   f"{config.concurrent_requests} concurrent")
        
        # Initialize cost tracker if not provided
        if self.cost_tracker is None:
            self.cost_tracker = CostTracker(config.budget_tier)
        
        # Check budget before starting test
        model_name = getattr(self.client, 'model', 'unknown')
        can_afford, reason = self.cost_tracker.can_afford_test(
            model_name, config.num_requests, 50, 100
        )
        
        if not can_afford and config.max_cost is None:
            logger.error(f"Test blocked by budget: {reason}")
            raise ValueError(f"Budget exceeded: {reason}")
        
        # Start cost tracking session
        self.cost_tracker.start_test()
        
        start_time = datetime.now()
        start_timestamp = time.time()
        
        # Generate prompts
        prompts = self._generate_prompts(config)
        
        # Run requests
        if config.concurrent_requests > 1:
            results = self._run_concurrent_requests(prompts, config.concurrent_requests)
        else:
            results = self._run_sequential_requests(prompts)
        
        end_time = datetime.now()
        end_timestamp = time.time()
        total_duration = end_timestamp - start_timestamp
        
        # Calculate metrics
        stress_test_results = self._calculate_metrics(
            results, config, start_time, end_time, total_duration
        )
        
        # Calculate and add cost information
        if self.cost_tracker:
            total_cost = 0.0
            for result in results:
                if result.get('success', False):
                    input_tokens = result.get('input_tokens', 50)
                    output_tokens = result.get('token_count', 100) - input_tokens
                    
                    cost = self.cost_tracker.calculate_request_cost(
                        model_name, input_tokens, output_tokens
                    )
                    self.cost_tracker.record_test_cost(cost, stress_test_results.test_name)
                    total_cost += cost.total_cost
            
            stress_test_results.total_cost = total_cost
            stress_test_results.avg_cost_per_request = (
                total_cost / stress_test_results.total_requests 
                if stress_test_results.total_requests > 0 else 0
            )
            stress_test_results.cost_breakdown = self.cost_tracker.get_cost_summary(days=1)
            
            # Save cost history
            self.cost_tracker.save_cost_history()
        
        # Save results if requested
        if config.save_results:
            self._save_results(stress_test_results, config)
        
        logger.info(f"Stress test completed: {stress_test_results.successful_requests}/"
                   f"{stress_test_results.total_requests} successful, "
                   f"avg latency: {stress_test_results.avg_latency:.2f}s, "
                   f"total cost: ${stress_test_results.total_cost:.4f}")
        
        return stress_test_results
    
    def _generate_prompts(self, config: StressTestConfig) -> List[str]:
        """Generate prompts for the stress test.
        
        Args:
            config: Stress test configuration.
            
        Returns:
            List of prompts to use in the test.
        """
        if config.custom_prompts:
            prompts = config.custom_prompts[:config.num_requests]
            # Repeat prompts if we need more than provided
            while len(prompts) < config.num_requests:
                prompts.extend(config.custom_prompts[:config.num_requests - len(prompts)])
            return prompts[:config.num_requests]
        
        return self.prompt_generator.get_multiple_prompts(
            config.prompt_type, 
            config.num_requests,
            allow_duplicates=True
        )
    
    def _run_sequential_requests(self, prompts: List[str]) -> List[Dict[str, Any]]:
        """Run requests sequentially.
        
        Args:
            prompts: List of prompts to send.
            
        Returns:
            List of results from each request.
        """
        results = []
        for i, prompt in enumerate(prompts):
            logger.debug(f"Running request {i+1}/{len(prompts)}")
            result = self.client.run_prompt(prompt)
            result["request_id"] = i + 1
            result["prompt"] = prompt
            results.append(result)
        
        return results
    
    def _run_concurrent_requests(
        self, 
        prompts: List[str], 
        max_workers: int
    ) -> List[Dict[str, Any]]:
        """Run requests concurrently using thread pool.
        
        Args:
            prompts: List of prompts to send.
            max_workers: Maximum number of concurrent workers.
            
        Returns:
            List of results from each request.
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all requests
            future_to_request = {
                executor.submit(self.client.run_prompt, prompt): {
                    "request_id": i + 1,
                    "prompt": prompt
                }
                for i, prompt in enumerate(prompts)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_request):
                request_info = future_to_request[future]
                try:
                    result = future.result()
                    result["request_id"] = request_info["request_id"]
                    result["prompt"] = request_info["prompt"]
                    results.append(result)
                    logger.debug(f"Completed request {request_info['request_id']}")
                except Exception as e:
                    logger.error(f"Request {request_info['request_id']} failed with exception: {e}")
                    error_result = {
                        "request_id": request_info["request_id"],
                        "prompt": request_info["prompt"],
                        "response": "",
                        "latency": 0.0,
                        "success": False,
                        "error": str(e),
                        "model": self.client.model,
                        "token_count": 0
                    }
                    results.append(error_result)
        
        # Sort results by request_id to maintain order
        results.sort(key=lambda x: x["request_id"])
        return results
    
    def _calculate_metrics(
        self,
        results: List[Dict[str, Any]],
        config: StressTestConfig,
        start_time: datetime,
        end_time: datetime,
        total_duration: float
    ) -> StressTestResults:
        """Calculate stress test metrics from results.
        
        Args:
            results: List of individual request results.
            config: Test configuration.
            start_time: Test start time.
            end_time: Test end time.
            total_duration: Total test duration in seconds.
            
        Returns:
            StressTestResults with calculated metrics.
        """
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        # Basic counts
        total_requests = len(results)
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        
        # Latency metrics (only for successful requests)
        latencies = [r["latency"] for r in successful_results]
        if latencies:
            min_latency = min(latencies)
            max_latency = max(latencies)
            avg_latency = statistics.mean(latencies)
            median_latency = statistics.median(latencies)
            p95_latency = self._calculate_percentile(latencies, 95)
        else:
            min_latency = max_latency = avg_latency = median_latency = p95_latency = 0.0
        
        # Token count
        total_tokens = sum(r.get("token_count", 0) for r in successful_results)
        
        # Throughput
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0.0
        
        # Error analysis
        errors = {}
        for result in failed_results:
            error_type = result.get("error", "Unknown error")
            errors[error_type] = errors.get(error_type, 0) + 1
        
        # Test name
        test_name = config.test_name or f"stress_test_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        return StressTestResults(
            test_name=test_name,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration=total_duration,
            config=config,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            min_latency=min_latency,
            max_latency=max_latency,
            avg_latency=avg_latency,
            median_latency=median_latency,
            p95_latency=p95_latency,
            total_tokens=total_tokens,
            requests_per_second=requests_per_second,
            errors=errors,
            individual_results=results
        )
    
    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """Calculate the nth percentile of a dataset.
        
        Args:
            data: List of numeric values.
            percentile: Percentile to calculate (0-100).
            
        Returns:
            The percentile value.
        """
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def _save_results(self, results: StressTestResults, config: StressTestConfig) -> None:
        """Save stress test results to file.
        
        Args:
            results: Results to save.
            config: Test configuration.
        """
        output_dir = Path(config.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{results.test_name}_{timestamp}"
        
        if config.output_format.lower() == "json":
            filepath = output_dir / f"{base_filename}.json"
            self._save_json_results(results, filepath)
        elif config.output_format.lower() == "csv":
            filepath = output_dir / f"{base_filename}.csv"
            self._save_csv_results(results, filepath)
        else:
            logger.warning(f"Unknown output format: {config.output_format}. Saving as JSON.")
            filepath = output_dir / f"{base_filename}.json"
            self._save_json_results(results, filepath)
        
        logger.info(f"Results saved to: {filepath}")
    
    def _save_json_results(self, results: StressTestResults, filepath: Path) -> None:
        """Save results as JSON file.
        
        Args:
            results: Results to save.
            filepath: Path to save file.
        """
        with open(filepath, "w") as f:
            json.dump(asdict(results), f, indent=2, default=str)
    
    def _save_csv_results(self, results: StressTestResults, filepath: Path) -> None:
        """Save individual results as CSV file.
        
        Args:
            results: Results to save.
            filepath: Path to save file.
        """
        if not results.individual_results:
            logger.warning("No individual results to save as CSV")
            return
        
        fieldnames = results.individual_results[0].keys()
        
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results.individual_results)
    
    def print_summary(self, results: StressTestResults) -> None:
        """Print a summary of stress test results.
        
        Args:
            results: Results to summarize.
        """
        print(f"\n{'='*60}")
        print(f"STRESS TEST SUMMARY: {results.test_name}")
        print(f"{'='*60}")
        print(f"Duration: {results.total_duration:.2f}s")
        print(f"Total Requests: {results.total_requests}")
        print(f"Successful: {results.successful_requests}")
        print(f"Failed: {results.failed_requests}")
        print(f"Success Rate: {results.success_rate:.2%}")
        print(f"Requests/Second: {results.requests_per_second:.2f}")
        print(f"\nLatency Metrics (successful requests only):")
        print(f"  Min: {results.min_latency:.3f}s")
        print(f"  Max: {results.max_latency:.3f}s")
        print(f"  Avg: {results.avg_latency:.3f}s")
        print(f"  Median: {results.median_latency:.3f}s")
        print(f"  95th percentile: {results.p95_latency:.3f}s")
        print(f"\nTotal Tokens: {results.total_tokens}")
        
        if results.errors:
            print(f"\nErrors:")
            for error, count in results.errors.items():
                print(f"  {error}: {count}")
        
        print(f"{'='*60}\n") 