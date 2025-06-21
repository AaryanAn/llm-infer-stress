#!/usr/bin/env python3
"""
Consolidated test script for LLM Inference Stress Testing.
Replaces multiple test files with a single comprehensive test.
"""

import sys
import time
from typing import Dict, Any

def test_mock_client():
    """Test the mock client functionality."""
    try:
        from llm_infer.clients.mock_client import MockClient
        
        print("Testing Mock Client...")
        client = MockClient(model="test-model", error_rate=0.1)
        
        result = client.run_prompt("What is artificial intelligence?")
        
        if result and "response" in result:
            print(f"✅ Mock client test passed")
            print(f"   Response length: {len(result['response'])} characters")
            print(f"   Latency: {result.get('latency', 0):.3f}s")
            return True
        else:
            print("❌ Mock client test failed")
            return False
            
    except Exception as e:
        print(f"❌ Mock client test error: {e}")
        return False


def test_stress_runner():
    """Test the stress test runner."""
    try:
        from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
        from llm_infer.core.prompt_generator import PromptGenerator, PromptType
        from llm_infer.core.cost_tracker import CostTracker, CostTier
        from llm_infer.clients.mock_client import MockClient
        
        print("\nTesting Stress Test Runner with Cost Tracking...")
        
        client = MockClient(model="mock-gpt-3.5", error_rate=0.0)
        prompt_generator = PromptGenerator()
        cost_tracker = CostTracker(CostTier.DEVELOPMENT)
        runner = StressTestRunner(client, prompt_generator, cost_tracker)
        
        config = StressTestConfig(
            num_requests=3,
            concurrent_requests=1,
            prompt_type=PromptType.SHORT_QA,
            save_results=False,
            budget_tier=CostTier.DEVELOPMENT
        )
        
        results = runner.run_stress_test(config)
        
        if results and results.total_requests == 3:
            print(f"✅ Stress runner test passed")
            print(f"   Total requests: {results.total_requests}")
            print(f"   Success rate: {results.success_rate:.1%}")
            print(f"   Total cost: ${results.total_cost:.4f}")
            print(f"   Avg cost per request: ${results.avg_cost_per_request:.4f}")
            return True
        else:
            print("❌ Stress runner test failed")
            return False
            
    except Exception as e:
        print(f"❌ Stress runner test error: {e}")
        return False


def test_prometheus_metrics():
    """Test Prometheus metrics functionality."""
    try:
        from llm_infer.metrics.prometheus_metrics import PrometheusMetrics
        
        print("\nTesting Prometheus Metrics...")
        
        metrics = PrometheusMetrics()
        
        # Record some test metrics
        metrics.record_request("test-model", "qa", 0.5, True, None, 100)
        metrics.record_request("test-model", "qa", 1.0, False, "timeout", 0)
        
        # Try to generate metrics output
        output = metrics.get_metrics()
        
        if output and "llm_requests_total" in output:
            print(f"✅ Prometheus metrics test passed")
            print(f"   Metrics output length: {len(output)} characters")
            return True
        else:
            print("❌ Prometheus metrics test failed")
            return False
            
    except Exception as e:
        print(f"❌ Prometheus metrics test error: {e}")
        return False


def test_prompt_generator():
    """Test prompt generator functionality."""
    try:
        from llm_infer.core.prompt_generator import PromptGenerator, PromptType
        
        print("\nTesting Prompt Generator...")
        
        generator = PromptGenerator()
        
        # Test each prompt type
        qa_prompts = generator.get_multiple_prompts(PromptType.SHORT_QA, count=2)
        longform_prompts = generator.get_multiple_prompts(PromptType.LONG_FORM, count=2)
        code_prompts = generator.get_multiple_prompts(PromptType.CODE_GENERATION, count=2)
        
        if (len(qa_prompts) == 2 and 
            len(longform_prompts) == 2 and 
            len(code_prompts) == 2):
            print(f"✅ Prompt generator test passed")
            print(f"   Generated {len(qa_prompts)} QA prompts")
            print(f"   Generated {len(longform_prompts)} longform prompts")
            print(f"   Generated {len(code_prompts)} code prompts")
            return True
        else:
            print("❌ Prompt generator test failed")
            return False
            
    except Exception as e:
        print(f"❌ Prompt generator test error: {e}")
        return False


def test_cost_tracker():
    """Test cost tracking functionality."""
    try:
        from llm_infer.core.cost_tracker import CostTracker, CostTier
        
        print("\nTesting Cost Tracker...")
        
        tracker = CostTracker(CostTier.DEMO)
        
        # Test cost calculation
        cost = tracker.calculate_request_cost("gpt-3.5-turbo", 100, 50)
        expected_cost = (100/1000 * 0.0015) + (50/1000 * 0.002)  # $0.00025
        
        if abs(cost.total_cost - expected_cost) < 0.0001:
            print(f"✅ Cost calculation test passed")
            print(f"   GPT-3.5 cost: ${cost.total_cost:.6f} for 100+50 tokens")
            
            # Test budget checking
            can_afford, reason = tracker.can_afford_test("gpt-4", 1000, 100, 100)
            print(f"   Budget check (GPT-4, 1000 requests): {can_afford}")
            print(f"   Reason: {reason}")
            
            # Test optimization suggestions
            suggestions = tracker.get_optimization_suggestions()
            print(f"   Optimization suggestions: {len(suggestions)} available")
            
            return True
        else:
            print("❌ Cost calculation test failed")
            return False
            
    except Exception as e:
        print(f"❌ Cost tracker test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running LLM Inference Stress Testing Suite")
    print("=" * 50)
    
    tests = [
        test_mock_client,
        test_stress_runner,
        test_prometheus_metrics,
        test_prompt_generator,
        test_cost_tracker
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 