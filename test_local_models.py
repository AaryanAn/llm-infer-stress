#!/usr/bin/env python3
"""Test script for local model clients."""

import logging
from llm_infer.clients.huggingface_client import LocalModelClient
from llm_infer.clients.mock_client import MockClient
from llm_infer.clients.ollama_client import OllamaClient
from llm_infer.utils import setup_logging

setup_logging(level="INFO")
logger = logging.getLogger(__name__)

def test_mock_client():
    """Test the mock client."""
    print("\n" + "="*50)
    print("Testing Mock Client")
    print("="*50)
    
    try:
        client = MockClient(model="mock-test")
        
        test_prompt = "What is artificial intelligence?"
        print(f"Prompt: {test_prompt}")
        
        result = client.run_prompt(test_prompt)
        
        print(f"Success: {result['success']}")
        print(f"Latency: {result['latency']:.3f}s")
        print(f"Response: {result['response'][:100]}...")
        print(f"Tokens: {result['total_tokens']}")
        
        return True
        
    except Exception as e:
        print(f"Mock client test failed: {e}")
        return False

def test_local_model():
    """Test a local Hugging Face model."""
    print("\n" + "="*50)
    print("Testing Local Hugging Face Model")
    print("="*50)
    
    try:
        # Use a small, fast model for testing
        print("Loading DialoGPT-small model...")
        client = LocalModelClient.create_client("microsoft/DialoGPT-small", max_length=100)
        
        test_prompt = "Hello, how are you?"
        print(f"Prompt: {test_prompt}")
        
        result = client.run_prompt(test_prompt)
        
        print(f"Success: {result['success']}")
        print(f"Latency: {result['latency']:.3f}s")
        print(f"Response: {result['response']}")
        print(f"Tokens: {result['total_tokens']}")
        print(f"Device: {result['metadata']['device']}")
        
        return True
        
    except Exception as e:
        print(f"Local model test failed: {e}")
        return False

def test_ollama_client():
    """Test Ollama client if available."""
    print("\n" + "="*50)
    print("Testing Ollama Client")
    print("="*50)
    
    if not OllamaClient.is_ollama_available():
        print("❌ Ollama is not running or not installed")
        print("To install and run Ollama:")
        print("1. Visit https://ollama.ai")
        print("2. Download and install Ollama")
        print("3. Run: ollama serve")
        print("4. Pull a model: ollama pull llama2:7b")
        return False
    
    try:
        print("✅ Ollama is running")
        client = OllamaClient(model_name="llama2:7b")
        
        test_prompt = "What is machine learning?"
        print(f"Prompt: {test_prompt}")
        
        result = client.run_prompt(test_prompt)
        
        print(f"Success: {result['success']}")
        print(f"Latency: {result['latency']:.3f}s")
        print(f"Response: {result['response'][:200]}...")
        print(f"Tokens: {result['total_tokens']}")
        
        return True
        
    except Exception as e:
        print(f"Ollama client test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Local Model Clients")
    print("This script tests the different local model options available.")
    
    results = {}
    
    # Test mock client (should always work)
    results['mock'] = test_mock_client()
    
    # Test local Hugging Face model
    results['local'] = test_local_model()
    
    # Test Ollama client
    results['ollama'] = test_ollama_client()
    
    print("\n" + "="*50)
    print("Test Results Summary")
    print("="*50)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name.upper()} client: {status}")
    
    if any(results.values()):
        print("\n🎉 At least one client is working! You can use the dashboard now.")
        print("Run: streamlit run app.py")
    else:
        print("\n⚠️ No clients are working. Check the error messages above.")

if __name__ == "__main__":
    main() 