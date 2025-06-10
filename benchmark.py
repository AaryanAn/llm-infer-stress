#!/usr/bin/env python3
"""Command-line interface for LLM inference stress testing."""

import argparse
import logging
import sys
from typing import Optional

from llm_infer.clients.openai_client import OpenAIClient
from llm_infer.core.prompt_generator import PromptGenerator, PromptType
from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
from llm_infer.metrics.prometheus_metrics import PrometheusMetrics
from llm_infer.utils import setup_logging, validate_environment_variables


def create_client(provider: str, model: str) -> Optional[OpenAIClient]:
    """Create an LLM client based on provider and model.
    
    Args:
        provider: LLM provider (openai, anthropic, google).
        model: Model name.
        
    Returns:
        Client instance or None if unsupported.
    """
    if provider.lower() == "openai":
        return OpenAIClient(model=model)
    else:
        print(f"Error: Provider '{provider}' not yet supported. Only 'openai' is currently available.")
        return None


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="LLM Inference Stress Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python benchmark.py --requests 20 --concurrent 3 --prompt-type short_qa
  python benchmark.py --model gpt-4 --requests 50 --prompt-type code_generation --output json
  python benchmark.py --custom-prompt "Explain quantum computing" --requests 10
        """
    )
    
    # Model configuration
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "anthropic", "google"],
        help="LLM provider (default: openai)"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="Model name (default: gpt-3.5-turbo)"
    )
    
    # Test configuration
    parser.add_argument(
        "--requests",
        type=int,
        default=10,
        help="Number of requests to send (default: 10)"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Number of concurrent requests (default: 1)"
    )
    
    parser.add_argument(
        "--prompt-type",
        choices=["short_qa", "long_form", "code_generation"],
        default="short_qa",
        help="Type of prompts to use (default: short_qa)"
    )
    
    parser.add_argument(
        "--custom-prompt",
        help="Use a custom prompt instead of predefined ones"
    )
    
    # Output configuration
    parser.add_argument(
        "--output",
        choices=["json", "csv"],
        default="json",
        help="Output format for results (default: json)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory to save results (default: results)"
    )
    
    parser.add_argument(
        "--test-name",
        help="Name for this test run"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="File to write logs to (default: stdout only)"
    )
    
    # Metrics configuration
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Display Prometheus metrics after test"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)
    logger = logging.getLogger(__name__)
    
    # Validate environment
    env_status = validate_environment_variables()
    if not env_status["all_set"]:
        print("Error: Missing required environment variables!")
        print("Please set the following environment variables:")
        for var in env_status["missing"]:
            print(f"  export {var}=your_api_key_here")
        sys.exit(1)
    
    logger.info(f"Starting stress test with {args.requests} requests, {args.concurrent} concurrent")
    
    try:
        # Create client
        client = create_client(args.provider, args.model)
        if not client:
            sys.exit(1)
        
        # Create prompt generator
        prompt_generator = PromptGenerator()
        
        # Create configuration
        config = StressTestConfig(
            num_requests=args.requests,
            concurrent_requests=args.concurrent,
            prompt_type=PromptType(args.prompt_type),
            custom_prompts=[args.custom_prompt] if args.custom_prompt else None,
            save_results=not args.no_save,
            output_format=args.output,
            output_dir=args.output_dir,
            test_name=args.test_name
        )
        
        # Initialize metrics if requested
        metrics = None
        if args.metrics:
            metrics = PrometheusMetrics()
        
        # Create and run stress test
        runner = StressTestRunner(client, prompt_generator)
        results = runner.run_stress_test(config)
        
        # Record metrics
        if metrics:
            metrics.record_batch_results(results.individual_results)
        
        # Print summary
        runner.print_summary(results)
        
        # Display metrics if requested
        if args.metrics:
            print("\nPrometheus Metrics:")
            print("=" * 60)
            print(metrics.get_metrics())
        
        # Exit with appropriate code
        if results.failed_requests > 0:
            logger.warning(f"Test completed with {results.failed_requests} failures")
            sys.exit(1)
        else:
            logger.info("Test completed successfully")
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
