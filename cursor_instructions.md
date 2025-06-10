# Cursor Project Instructions: LLM Inference Stress Testing MVP

## Project Overview

This project benchmarks and stress-tests inference times and error behaviors across multiple large language models (LLMs), including OpenAI, Anthropic, and Google Gemini. It compares model responsiveness, reliability, and throughput under load, with observability using Prometheus and Grafana.

## Tech Stack

- Language: Python 3.11+
- Frontend: Streamlit
- Metrics: Prometheus-compatible endpoints
- Virtual Environment: .venv or llmvenv
- Dependencies: requirements.txt
- Optional Dashboard: Grafana

## Project Structure

llm-infer-stress/
├── .cursor/
│   └── config.json
├── llm_infer/
│   ├── __init__.py
│   ├── clients/
│   │   ├── openai_client.py
│   │   ├── anthropic_client.py
│   │   └── gemini_client.py
│   ├── metrics/
│   │   └── prometheus_metrics.py
│   ├── core/
│   │   ├── stress_test_runner.py
│   │   └── prompt_generator.py
│   └── utils.py
├── app.py
├── requirements.txt
├── README.md
└── cursor_instructions.md

## MVP Features

### 1. LLM Clients
- Each client must:
  - Load API key from environment variables
  - Implement a run_prompt(prompt: str) -> dict method
  - Handle retries, timeouts, and errors

### 2. Prompt Generator
- Generate prompts for:
  - Short Q&A
  - Long-form text
  - Code generation
- Configurable via CLI or Streamlit UI

### 3. Stress Test Runner
- Execute N requests sequentially or concurrently
- Collect:
  - Latency stats (min, max, avg)
  - Error counts
  - Throughput
- Save results to JSON or CSV

### 4. Prometheus Exporter
- Expose /metrics endpoint with:
  - llm_latency_seconds
  - llm_requests_total
  - llm_failure_count
- Labels should include:
  - model
  - prompt_type
  - status (success|fail)

### 5. Streamlit Dashboard (Optional)
- Interface to:
  - Select model
  - Choose or input prompts
  - Run benchmark and view metrics
  - Export results

## Code Style and Guidelines

- PEP8 formatting
- Type hints on all functions
- Google-style docstrings
- Minimal global variables
- Use logging, not print
- Never hardcode secrets

## Environment Setup

python3 -m venv llmvenv
source llmvenv/bin/activate
pip install -r requirements.txt

Required environment variables:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY

## Cursor Behavior Instructions

- Do not write code in any language other than Python
- Enforce modularity and separation of concerns
- Avoid premature abstraction
- Default to using real APIs unless mock behavior is explicitly requested
- Focus on metrics and real throughput — not simulated time.sleep loops

## Immediate Next Tasks

1. Implement openai_client.py with run_prompt method
2. Add 3 static prompt types in prompt_generator.py
3. Create stress_test_runner.py with config and results logging
4. Add /metrics Prometheus exporter using prometheus_client
5. Scaffold Streamlit UI for interacting with the benchmark
