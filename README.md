# LLM Inference Stress Testing MVP

A comprehensive benchmarking tool for stress-testing large language model (LLM) inference across multiple providers. This tool measures response times, error rates, throughput, and provides Prometheus-compatible metrics.

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

## Development

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