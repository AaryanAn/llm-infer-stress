#!/usr/bin/env python3
"""Test script using mock client to demonstrate functionality without API costs."""

from llm_infer.clients.mock_client import MockClient
from llm_infer.core.prompt_generator import PromptGenerator, PromptType
from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
from llm_infer.metrics.prometheus_metrics import PrometheusMetrics
from llm_infer.utils import setup_logging
from llm_infer.clients.huggingface_client import LocalModelClient


def main():
    """Run demonstration with mock client."""
    # Setup logging
    setup_logging(level="INFO")
    
    print("🚀 LLM Stress Testing - Mock Demo")
    print("=" * 50)
    print("Testing all functionality without API costs!\n")
    
    # Initialize components with mock client
    client = MockClient(model="mock-gpt-3.5-turbo", error_rate=0.2)  # 20% error rate for demo
    prompt_generator = PromptGenerator()
    metrics = PrometheusMetrics()
    
    # Test 1: Short Q&A
    print("📝 Test 1: Short Q&A (5 requests)")
    config1 = StressTestConfig(
        num_requests=5,
        concurrent_requests=1,
        prompt_type=PromptType.SHORT_QA,
        test_name="mock_short_qa",
        save_results=True
    )
    
    runner = StressTestRunner(client, prompt_generator)
    results1 = runner.run_stress_test(config1)
    runner.print_summary(results1)
    
    # Record metrics
    metrics.record_batch_results(results1.individual_results)
    
    # Test 2: Concurrent code generation
    print("\n💻 Test 2: Code Generation (6 requests, 3 concurrent)")
    config2 = StressTestConfig(
        num_requests=6,
        concurrent_requests=3,
        prompt_type=PromptType.CODE_GENERATION,
        test_name="mock_code_gen",
        save_results=True
    )
    
    results2 = runner.run_stress_test(config2)
    runner.print_summary(results2)
    
    # Record metrics
    metrics.record_batch_results(results2.individual_results)
    
    # Test 3: Custom prompt
    print("\n🎯 Test 3: Custom Long-form Prompt")
    config3 = StressTestConfig(
        num_requests=3,
        concurrent_requests=2,
        custom_prompts=[
            "Write a comprehensive analysis of renewable energy technologies, covering solar, wind, and hydroelectric power, including their advantages, disadvantages, and future prospects in addressing global climate change."
        ],
        test_name="mock_custom_long",
        save_results=True
    )
    
    results3 = runner.run_stress_test(config3)
    runner.print_summary(results3)
    
    # Record metrics
    metrics.record_batch_results(results3.individual_results)
    
    # Show final metrics
    print("\n📊 Final Prometheus Metrics Sample:")
    print("=" * 40)
    metrics_text = metrics.get_metrics()
    for line in metrics_text.split('\n')[:20]:
        if line and not line.startswith('#'):
            print(line)
    
    print(f"\n✅ Mock demonstration completed successfully!")
    print(f"📁 Results saved in the 'results/' directory")
    print(f"🌐 Try the dashboard: streamlit run app.py")
    print(f"💡 To use real APIs, fix your OpenAI billing and run: python benchmark.py")

    # Test any supported model
    client = LocalModelClient.create_client("distilgpt2")
    result = client.run_prompt("What is machine learning?")
    print(f"Response: {result['response']}")
    print(f"Latency: {result['latency']:.3f}s")


if __name__ == "__main__":
    main() 