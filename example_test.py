#!/usr/bin/env python3
"""Example script demonstrating LLM stress testing functionality."""

import os
from llm_infer.clients.openai_client import OpenAIClient
from llm_infer.core.prompt_generator import PromptGenerator, PromptType
from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
from llm_infer.metrics.prometheus_metrics import PrometheusMetrics
from llm_infer.utils import setup_logging, validate_environment_variables


def main():
    """Run example stress tests."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Validate environment variables
    env_status = validate_environment_variables()
    if not env_status["all_set"]:
        print("Missing required environment variables. Please set:")
        for var in env_status["missing"]:
            print(f"  export {var}=your_api_key_here")
        return
    
    print("🚀 LLM Stress Testing Example")
    print("=" * 50)
    
    try:
        # Initialize components
        client = OpenAIClient(model="gpt-3.5-turbo")
        prompt_generator = PromptGenerator()
        metrics = PrometheusMetrics()
        
        # Test 1: Quick test with short Q&A prompts
        print("\n📝 Test 1: Short Q&A prompts (5 requests)")
        config1 = StressTestConfig(
            num_requests=5,
            concurrent_requests=1,
            prompt_type=PromptType.SHORT_QA,
            test_name="example_short_qa",
            save_results=False  # Don't save for this example
        )
        
        runner = StressTestRunner(client, prompt_generator)
        results1 = runner.run_stress_test(config1)
        
        print(f"✅ Success rate: {results1.success_rate:.1%}")
        print(f"⏱️  Average latency: {results1.avg_latency:.2f}s")
        
        # Record metrics
        metrics.record_batch_results(results1.individual_results)
        
        # Test 2: Concurrent test with code generation
        print("\n💻 Test 2: Code generation prompts (3 concurrent)")
        config2 = StressTestConfig(
            num_requests=6,
            concurrent_requests=3,
            prompt_type=PromptType.CODE_GENERATION,
            test_name="example_code_gen",
            save_results=False
        )
        
        results2 = runner.run_stress_test(config2)
        
        print(f"✅ Success rate: {results2.success_rate:.1%}")
        print(f"⏱️  Average latency: {results2.avg_latency:.2f}s")
        print(f"🚀 Throughput: {results2.requests_per_second:.2f} req/s")
        
        # Record metrics
        metrics.record_batch_results(results2.individual_results)
        
        # Test 3: Custom prompt test
        print("\n🎯 Test 3: Custom prompt")
        config3 = StressTestConfig(
            num_requests=3,
            concurrent_requests=1,
            custom_prompts=["Explain the concept of machine learning in one paragraph."],
            test_name="example_custom",
            save_results=False
        )
        
        results3 = runner.run_stress_test(config3)
        
        print(f"✅ Success rate: {results3.success_rate:.1%}")
        print(f"⏱️  Average latency: {results3.avg_latency:.2f}s")
        print(f"📊 Total tokens: {results3.total_tokens}")
        
        # Record metrics
        metrics.record_batch_results(results3.individual_results)
        
        # Show final metrics summary
        print("\n📊 Final Metrics Summary")
        print("=" * 30)
        stats = metrics.get_current_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total failures: {stats['total_failures']}")
        
        # Show some sample metrics
        print("\n🔧 Sample Prometheus Metrics:")
        print("-" * 30)
        metrics_text = metrics.get_metrics()
        # Show just the first few lines
        for line in metrics_text.split('\n')[:15]:
            if line and not line.startswith('#'):
                print(line)
        
        print("\n✅ Example completed successfully!")
        print("💡 Try running: streamlit run app.py")
        print("💡 Or: python benchmark.py --help")
        
    except Exception as e:
        print(f"❌ Error running example: {e}")
        print("💡 Make sure you have set OPENAI_API_KEY environment variable")


if __name__ == "__main__":
    main() 