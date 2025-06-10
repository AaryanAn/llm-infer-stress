#!/usr/bin/env python3
"""Demonstration script showing local model stress testing."""

import time
from llm_infer.clients.mock_client import MockClient
from llm_infer.clients.huggingface_client import LocalModelClient
from llm_infer.core.prompt_generator import PromptGenerator, PromptType
from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
from llm_infer.utils import setup_logging

setup_logging(level="INFO")

def demo_mock_stress_test():
    """Demonstrate stress testing with mock client."""
    print("🎭 Demo: Mock Client Stress Test")
    print("="*50)
    
    # Create mock client
    client = MockClient(model="mock-demo", error_rate=0.2)
    
    # Create prompt generator
    prompt_generator = PromptGenerator()
    
    # Create test runner
    runner = StressTestRunner(client, prompt_generator)
    
    # Configure test
    config = StressTestConfig(
        num_requests=5,
        concurrent_requests=2,
        prompt_type=PromptType.SHORT_QA,
        test_name="mock_demo",
        save_results=True
    )
    
    print(f"Running {config.num_requests} requests with {config.concurrent_requests} concurrent...")
    start_time = time.time()
    
    # Run the test
    results = runner.run_stress_test(config)
    
    elapsed = time.time() - start_time
    
    # Display results
    print(f"\n✅ Test completed in {elapsed:.2f} seconds!")
    print(f"Success rate: {results.success_rate:.1%}")
    print(f"Average latency: {results.avg_latency:.3f}s")
    print(f"Total tokens: {results.total_tokens:,}")
    print(f"Requests per second: {results.requests_per_second:.2f}")
    
    if results.errors:
        print(f"Errors encountered: {dict(results.errors)}")
    
    return results

def demo_local_model_stress_test():
    """Demonstrate stress testing with local Hugging Face model."""
    print("\n🖥️ Demo: Local Model Stress Test")
    print("="*50)
    
    try:
        # Create local model client (small model for demo)
        print("Loading DialoGPT-small model...")
        client = LocalModelClient.create_client("microsoft/DialoGPT-small", max_length=50)
        
        # Create prompt generator
        prompt_generator = PromptGenerator()
        
        # Create test runner
        runner = StressTestRunner(client, prompt_generator)
        
        # Configure test (smaller test for demo)
        config = StressTestConfig(
            num_requests=3,
            concurrent_requests=1,  # Sequential for local models
            prompt_type=PromptType.SHORT_QA,
            test_name="local_demo",
            save_results=True
        )
        
        print(f"Running {config.num_requests} requests sequentially...")
        start_time = time.time()
        
        # Run the test
        results = runner.run_stress_test(config)
        
        elapsed = time.time() - start_time
        
        # Display results
        print(f"\n✅ Test completed in {elapsed:.2f} seconds!")
        print(f"Success rate: {results.success_rate:.1%}")
        print(f"Average latency: {results.avg_latency:.3f}s")
        print(f"Total tokens: {results.total_tokens:,}")
        print(f"Requests per second: {results.requests_per_second:.2f}")
        
        if results.errors:
            print(f"Errors encountered: {dict(results.errors)}")
        
        return results
        
    except Exception as e:
        print(f"❌ Local model test failed: {e}")
        return None

def compare_results(mock_results, local_results):
    """Compare results between mock and local model."""
    print("\n📊 Performance Comparison")
    print("="*50)
    
    if not local_results:
        print("Cannot compare - local model test failed")
        return
    
    print(f"{'Metric':<20} {'Mock Client':<15} {'Local Model':<15}")
    print("-" * 50)
    print(f"{'Success Rate':<20} {f'{mock_results.success_rate:.1%}':<15} {f'{local_results.success_rate:.1%}':<15}")
    print(f"{'Avg Latency':<20} {f'{mock_results.avg_latency:.3f}s':<15} {f'{local_results.avg_latency:.3f}s':<15}")
    print(f"{'Requests/sec':<20} {f'{mock_results.requests_per_second:.2f}':<15} {f'{local_results.requests_per_second:.2f}':<15}")
    print(f"{'Total Tokens':<20} {f'{mock_results.total_tokens}':<15} {f'{local_results.total_tokens}':<15}")

def main():
    """Run the demonstration."""
    print("🚀 LLM Stress Testing Demo - Local Models")
    print("This demonstration shows the stress testing system working with local models")
    print("No API keys required!\n")
    
    # Demo mock client
    mock_results = demo_mock_stress_test()
    
    # Demo local model
    local_results = demo_local_model_stress_test()
    
    # Compare results
    compare_results(mock_results, local_results)
    
    print("\n🎉 Demo completed!")
    print("\nTo try the interactive dashboard:")
    print("streamlit run app.py")
    print("\nThen select '🎭 Mock Client (Testing)' or '🖥️ Local Models (Hugging Face)'")

if __name__ == "__main__":
    main() 