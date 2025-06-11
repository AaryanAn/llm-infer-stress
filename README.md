# LLM Inference Stress Testing Platform

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Last Commit](https://img.shields.io/github/last-commit/yourusername/llm-infer-stress)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)

**A comprehensive, production-ready platform for benchmarking and stress-testing Large Language Model (LLM) inference systems.** This tool helps organizations evaluate LLM performance, reliability, and cost-effectiveness across different providers, deployment scenarios, and usage patterns. With support for both cloud APIs (OpenAI) and local models (Llama, DeepSeek, Hugging Face), plus zero-cost mock testing, it provides enterprise-grade metrics collection, real-time monitoring, and professional reporting capabilities.

## 🎯 Key Use Cases

• **LLM Provider Evaluation** - Compare performance and costs across OpenAI, local models, and other providers  
• **Infrastructure Capacity Planning** - Determine throughput requirements and scaling needs for production deployments  
• **Performance Regression Testing** - Validate that model updates and changes maintain expected response times and quality  
• **Cost Optimization Analysis** - Analyze token usage patterns and optimize API spending with detailed cost breakdowns  
• **Zero-Cost Development** - Prototype and demonstrate LLM applications using mock clients before API investment  

## 📚 Table of Contents

- [MVP Status](#-mvp-status)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Web Dashboard](#web-dashboard-recommended)
  - [Command Line Interface](#command-line-interface)
- [Project Structure](#project-structure)
- [Metrics](#metrics)
- [Example Results](#example-results)
- [Service Management](#service-management)
- [Storage Management](#storage-management)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🚧 MVP Status

This is a **Minimum Viable Product (MVP)** designed to demonstrate core LLM stress testing capabilities. While fully functional and production-ready for testing scenarios, it focuses on essential features rather than comprehensive enterprise deployment. Perfect for evaluation, prototyping, and small-to-medium scale testing workloads.

**Current Status:** ✅ Core functionality complete, 🔄 Local model integration, 📋 Additional providers planned

## 🛠 Tech Stack

**Core Framework**
- **Python 3.9+** - Primary development language
- **Streamlit** - Interactive web dashboard and real-time visualization
- **FastAPI** - High-performance API endpoints (planned)

**LLM Integration**
- **OpenAI API** - Cloud-based model access with retry logic and rate limiting
- **Transformers** - Hugging Face local model support (DeepSeek, Llama)
- **Ollama** - Local model serving and management

**Monitoring & Metrics**
- **Prometheus** - Enterprise-grade metrics collection and time-series data
- **Plotly** - Interactive charts and real-time performance visualization
- **JSON/CSV Export** - Flexible data export for external analysis

**Infrastructure**
- **asyncio** - Concurrent request handling and stress testing
- **Ray** - Distributed computing support (planned)
- **Docker** - Containerized deployment options (planned)

## ⚡ Quick Start

**Option 1: One-Command Demo (Recommended)**
```bash
git clone <repository-url> && cd llm-infer-stress
./start_dev.sh
# Opens http://localhost:8501 with full dashboard
```

**Option 2: Zero-Cost Mock Testing**
```bash
python test_mock.py
# Runs complete stress test simulation without API costs
```

**Option 3: CLI Benchmark**
```bash
export OPENAI_API_KEY="your_key_here"
python benchmark.py --requests 10 --concurrent 2
# Runs actual LLM stress test with results
```

## Features

- **Multi-Provider Support**: Currently supports OpenAI (with Anthropic and Google Gemini planned)
- **Stress Testing**: Configurable concurrent request testing
- **Multiple Prompt Types**: Short Q&A, long-form text, and code generation prompts
- **Metrics Collection**: Prometheus-compatible metrics with latency histograms
- **Interactive Dashboard**: Streamlit-based web interface
- **CLI Support**: Command-line interface for automation
- **Result Export**: JSON and CSV export options

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd llm-infer-stress
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv .venv-llm-infer
source .venv-llm-infer/bin/activate  # On Windows: .venv-llm-infer\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Configuration

Set up your API keys as environment variables:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"  # Optional, for future use
export GOOGLE_API_KEY="your_google_api_key_here"        # Optional, for future use
```

## Usage

### Web Dashboard (Recommended)

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard provides:
- Interactive test configuration
- Real-time progress tracking
- Visual results with charts
- Historical test comparison
- Prometheus metrics viewer

### Command Line Interface

Run stress tests from the command line:

```bash
# Basic test with 10 requests
python benchmark.py

# Advanced test configuration
python benchmark.py \
  --model gpt-4 \
  --requests 50 \
  --concurrent 5 \
  --prompt-type code_generation \
  --output json \
  --test-name "GPT-4 Code Generation Test"

# Custom prompt test
python benchmark.py \
  --custom-prompt "Explain quantum computing in simple terms" \
  --requests 20 \
  --concurrent 3
```

#### CLI Options

```
--provider          LLM provider (openai, anthropic, google) [default: openai]
--model            Model name [default: gpt-3.5-turbo]
--requests         Number of requests [default: 10]
--concurrent       Concurrent requests [default: 1]
--prompt-type      Prompt type (short_qa, long_form, code_generation) [default: short_qa]
--custom-prompt    Use custom prompt text
--output          Output format (json, csv) [default: json]
--output-dir      Results directory [default: results]
--test-name       Custom test name
--no-save         Don't save results to file
--log-level       Logging level [default: INFO]
--metrics         Display Prometheus metrics
```

## Project Structure

```
llm-infer-stress/
├── llm_infer/                    # Main package
│   ├── __init__.py
│   ├── clients/                  # LLM provider clients
│   │   ├── __init__.py
│   │   └── openai_client.py      # OpenAI API client
│   ├── core/                     # Core functionality
│   │   ├── __init__.py
│   │   ├── prompt_generator.py   # Prompt generation
│   │   └── stress_test_runner.py # Test execution engine
│   ├── metrics/                  # Metrics collection
│   │   ├── __init__.py
│   │   └── prometheus_metrics.py # Prometheus exporter
│   └── utils.py                  # Utility functions
├── app.py                        # Streamlit dashboard
├── benchmark.py                  # CLI interface
├── requirements.txt              # Dependencies
├── cursor_instructions.md        # Project specification
└── README.md                     # This file
```

## Metrics

The tool collects Prometheus-compatible metrics:

- `llm_requests_total` - Total requests with labels: model, prompt_type, status
- `llm_latency_seconds` - Request latency histogram with labels: model, prompt_type
- `llm_failure_count` - Failed requests with labels: model, prompt_type, error_type
- `llm_tokens_total` - Total tokens processed with labels: model, prompt_type
- `llm_active_requests` - Current active requests with labels: model

## Example Results

### CLI Output
```
============================================================
STRESS TEST SUMMARY: stress_test_20241201_143022
============================================================
Duration: 25.43s
Total Requests: 20
Successful: 19
Failed: 1
Success Rate: 95.00%
Requests/Second: 0.79

Latency Metrics (successful requests only):
  Min: 0.847s
  Max: 3.241s
  Avg: 1.523s
  Median: 1.445s
  95th percentile: 2.891s

Total Tokens: 2,847

Errors:
  Rate limit exceeded: 1
============================================================
```

### Saved Results
Results are automatically saved to the `results/` directory in JSON or CSV format:

```json
{
  "test_name": "gpt-4-code-test",
  "start_time": "2024-01-15T14:30:22",
  "success_rate": 0.95,
  "avg_latency": 1.523,
  "requests_per_second": 0.79,
  "individual_results": [...]
}
```

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```
   Error: OpenAI API key must be provided or set in OPENAI_API_KEY environment variable
   ```
   Solution: Set the required environment variables as shown in Configuration.

2. **Rate Limiting**
   ```
   Rate limit exceeded: You've exceeded your API quota
   ```
   Solution: Reduce concurrent requests or wait before retrying.

3. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'llm_infer'
   ```
   Solution: Ensure you're running from the project root and the virtual environment is activated.

## Service Management

### 🚀 **Starting Services**
```bash
# Easy startup (starts Ollama service)
./start_services.sh

# Manual startup
brew services start ollama
streamlit run app.py
```

### 🛑 **Shutting Down Services** (Important!)
Before turning off your computer or when done testing:

```bash
# Clean shutdown of all services
./shutdown_services.sh
```

This will:
- Stop all Streamlit processes
- Stop Ollama service  
- Kill any remaining background processes
- Free up system resources

**Why this matters:**
- Ollama can use 6GB+ of RAM for models
- Multiple Streamlit processes consume resources
- Clean shutdown prevents corrupted model states
- Ensures proper system shutdown

### 🔄 **Service Status Check**
```bash
# Check what's running
ps aux | grep -E "(streamlit|ollama)" | grep -v grep

# Check Ollama specifically
brew services list | grep ollama
```

## Storage Management

### 📊 **Storage Usage Analysis**
This project can use significant storage space:

```bash
# Check current usage
du -sh ~/.ollama ~/.cache/huggingface
```

**Typical Storage Usage:**
- **Ollama Models**: 1-10GB per model (DeepSeek: ~3.8GB, Llama: ~2GB)
- **Hugging Face Cache**: 500MB-5GB (GPT-2: ~500MB, larger models: 1-5GB)
- **Test Results**: 1-100MB (JSON files with test results)
- **Total**: Can easily reach 10-20GB+

### 🧹 **Storage Cleanup**
```bash
# Interactive cleanup tool
./cleanup_storage.sh
```

**Manual Cleanup Options:**

```bash
# Remove specific Ollama models
ollama list                    # See what's installed
ollama rm deepseek-coder:6.7b # Remove specific model

# Clear all Ollama models (frees ~5GB)
ollama list --format json | jq -r '.[].name' | xargs -I {} ollama rm {}

# Clear Hugging Face cache (frees ~2GB)
rm -rf ~/.cache/huggingface/*

# Clear test results
rm -rf ./results/*

# Clear logs  
rm -rf ./logs/*
```

**💡 Smart Storage Tips:**
- Models auto-download when needed
- Keep only your most-used models
- Clean up test results regularly
- Use the cleanup script before long trips/storage space issues

## Development

### 🚀 **Development Quick Start**

#### Option 1: One-Command Startup (Recommended)
```bash
# Navigate to project and run everything at once
cd /path/to/llm-infer-stress
./start_dev.sh
```
**That's it!** This script:
- ✅ Starts Ollama service
- ✅ Activates virtual environment
- ✅ Starts Streamlit with auto-reload
- ✅ Opens browser at http://localhost:8501

#### Option 2: Step-by-Step Control
```bash
# 1. Start background services only
./start_services.sh

# 2. Then choose one:
./temp_dev_start.sh                          # Auto-generated helper script
# OR manually:
source .venv-llm-infer/bin/activate
streamlit run app.py --server.runOnSave true
```

#### Option 3: Manual Commands (For Advanced Users)
```bash
# Individual control of each service
brew services start ollama
source .venv-llm-infer/bin/activate  
streamlit run app.py --server.runOnSave true --server.headless false
```

**💡 Daily Workflow:** Just run `./start_dev.sh` for effortless development!

### 📋 **Development Patterns**

**For daily development:**
- Use `./start_services.sh` to start fresh
- Use `streamlit run app.py --server.runOnSave true` for auto-reload
- Test components with `python test_mock.py`
- Use `./shutdown_services.sh` when done (includes storage cleanup)

**For component testing:**
```bash
python test_mock.py          # Test mock client
python test_local_models.py  # Test HuggingFace models
python benchmark.py          # Test CLI interface
```

**See [DEV_WORKFLOW.md](DEV_WORKFLOW.md) for complete development guide.**

### Adding New Providers

To add support for new LLM providers:

1. Create a new client in `llm_infer/clients/` (e.g., `anthropic_client.py`)
2. Implement the `run_prompt(prompt: str) -> dict` method
3. Add the client to `__init__.py` and update imports
4. Update CLI and dashboard to support the new provider

### Running Tests

```bash
# Basic functionality test
python benchmark.py --requests 3 --log-level DEBUG

# Dashboard test
streamlit run app.py
```

## License

This project is provided as-is for educational and testing purposes.

## Contributing

1. Follow PEP8 style guidelines
2. Add type hints to all functions
3. Include docstrings for public methods
4. Test changes with multiple models and request patterns 