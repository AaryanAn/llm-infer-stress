"""Streamlit dashboard for LLM inference stress testing."""

import logging
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional

from llm_infer.clients.openai_client import OpenAIClient
from llm_infer.clients.mock_client import MockClient
from llm_infer.clients.huggingface_client import LocalModelClient
from llm_infer.clients.ollama_client import OllamaClient
from llm_infer.core.prompt_generator import PromptGenerator, PromptType
from llm_infer.core.stress_test_runner import StressTestRunner, StressTestConfig
from llm_infer.core.cost_tracker import CostTracker, CostTier
from llm_infer.metrics.prometheus_metrics import PrometheusMetrics
from llm_infer.utils import setup_logging, validate_environment_variables

# Configure logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="LLM Stress Test Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit footer and menu
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Initialize session state
if "test_results" not in st.session_state:
    st.session_state.test_results = []

if "metrics" not in st.session_state:
    st.session_state.metrics = PrometheusMetrics()

if "prompt_generator" not in st.session_state:
    st.session_state.prompt_generator = PromptGenerator()

if "cost_tracker" not in st.session_state:
    st.session_state.cost_tracker = CostTracker(CostTier.DEVELOPMENT)


def check_environment(model_provider: str = "api") -> bool:
    """Check if required environment variables are set for API models."""
    if model_provider in ["local", "mock"]:
        st.info("🖥️ Using local models - no API keys required!")
        return True
    
    env_status = validate_environment_variables()
    
    if not env_status["all_set"]:
        with st.expander("⚠️ Missing API Keys (Click to expand)", expanded=False):
            st.warning("API models require environment variables. You can still use local models below!")
            st.write("For API models, set the following environment variables:")
            for var in env_status["missing"]:
                st.code(f"export {var}=your_api_key_here")
        return False
    
    st.success("✅ All required environment variables are set")
    return True


def create_client(model: str, model_type: str = "api"):
    """Create an LLM client based on model selection."""
    try:
        if model_type == "mock":
            return MockClient(model=model)
        elif model_type == "local_hf":
            return LocalModelClient.create_client(model)
        elif model_type == "ollama":
            return OllamaClient(model_name=model)
        elif model.startswith("gpt"):
            return OpenAIClient(model=model)
        else:
            st.error(f"Model {model} not supported yet.")
            return None
    except Exception as e:
        st.error(f"Failed to create client: {str(e)}")
        return None


def run_stress_test(client, config: StressTestConfig) -> None:
    """Run a stress test and update session state."""
    try:
        runner = StressTestRunner(client, st.session_state.prompt_generator, st.session_state.cost_tracker)
        
        # Show progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Starting stress test...")
        progress_bar.progress(10)
        
        # Run the test
        results = runner.run_stress_test(config)
        progress_bar.progress(90)
        
        # Record metrics
        st.session_state.metrics.record_batch_results(results.individual_results)
        progress_bar.progress(100)
        
        # Store results
        st.session_state.test_results.append(results)
        
        status_text.text("✅ Stress test completed!")
        
        # Display summary
        st.success(f"Test completed! {results.successful_requests}/{results.total_requests} requests successful")
        
        # Display detailed results
        display_test_results(results)
        
    except Exception as e:
        st.error(f"Error running stress test: {str(e)}")
        logger.error(f"Stress test error: {e}", exc_info=True)


def display_test_results(results) -> None:
    """Display stress test results with charts."""
    st.subheader("Test Results")
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Success Rate", f"{results.success_rate:.1%}")
    
    with col2:
        st.metric("Avg Latency", f"{results.avg_latency:.3f}s")
    
    with col3:
        st.metric("Requests/sec", f"{results.requests_per_second:.2f}")
    
    with col4:
        st.metric("Total Tokens", f"{results.total_tokens:,}")
    
    with col5:
        cost_color = "inverse" if results.total_cost == 0 else "normal"
        st.metric("Total Cost", f"${results.total_cost:.4f}", delta=None, delta_color=cost_color)
    
    # Latency distribution chart
    if results.individual_results:
        successful_results = [r for r in results.individual_results if r["success"]]
        
        if successful_results:
            latencies = [r["latency"] for r in successful_results]
            
            fig = px.histogram(
                x=latencies,
                nbins=20,
                title="Latency Distribution (Successful Requests)",
                labels={"x": "Latency (seconds)", "y": "Count"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Request timeline
            request_times = list(range(1, len(successful_results) + 1))
            fig_timeline = px.line(
                x=request_times,
                y=latencies,
                title="Latency Over Time",
                labels={"x": "Request Number", "y": "Latency (seconds)"}
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Error breakdown
    if results.errors:
        st.subheader("Error Breakdown")
        error_df = pd.DataFrame(list(results.errors.items()), columns=["Error Type", "Count"])
        fig_errors = px.bar(error_df, x="Error Type", y="Count", title="Error Types")
        st.plotly_chart(fig_errors, use_container_width=True)
    
    # Detailed results table
    with st.expander("Detailed Results"):
        df = pd.DataFrame(results.individual_results)
        st.dataframe(df, use_container_width=True)


def main():
    """Main Streamlit application."""
    st.title("🚀 LLM Inference Stress Testing Dashboard")
    st.markdown("Benchmark and stress-test inference times across multiple LLM providers")
    
    # Sidebar configuration
    st.sidebar.header("Test Configuration")
    
    # Model provider selection
    model_provider = st.sidebar.radio(
        "Model Provider",
        options=["mock", "local", "ollama", "api"],
        format_func=lambda x: {
            "local": "🖥️ Local Models (Hugging Face)",
            "ollama": "🦙 Ollama (Easy Local Setup)",
            "mock": "🎭 Mock Client (Testing)",
            "api": "☁️ API Models (OpenAI/etc)"
        }[x],
        help="Choose between mock client, local HF models, Ollama (easiest), or API models"
    )
    
    # Check environment based on provider
    env_ok = check_environment(model_provider)
    
    # Model selection based on provider
    if model_provider == "local":
        available_models = LocalModelClient.get_available_models()
        model_options = list(available_models.keys())
        selected_model = st.sidebar.selectbox(
            "Select Local Model", 
            model_options,
            format_func=lambda x: f"{available_models[x]['name']} ({available_models[x]['size']})"
        )
        
        # Show model info
        with st.sidebar.expander("Model Info"):
            model_info = available_models[selected_model]
            st.write(f"**{model_info['name']}**")
            st.write(model_info['description'])
            st.write(f"Size: {model_info['size']}")
    
    elif model_provider == "ollama":
        # Check if Ollama is available
        if OllamaClient.is_ollama_available():
            st.sidebar.success("✅ Ollama is running")
            popular_models = OllamaClient.get_popular_models()
            model_options = list(popular_models.keys())
            selected_model = st.sidebar.selectbox(
                "Select Ollama Model",
                model_options,
                format_func=lambda x: f"{popular_models[x]['name']} ({popular_models[x]['size']})"
            )
            
            # Show model info and installation help
            with st.sidebar.expander("Model Info & Setup"):
                model_info = popular_models[selected_model]
                st.write(f"**{model_info['name']}**")
                st.write(model_info['description'])
                st.write(f"Size: {model_info['size']}")
                st.code(f"ollama pull {selected_model}", language="bash")
                st.info("💡 First run will download the model automatically")
        else:
            st.sidebar.error("❌ Ollama not running")
            selected_model = "llama2:7b"  # Default
            
            with st.sidebar.expander("🦙 How to Install Ollama"):
                st.write("**Step 1:** Install Ollama")
                st.markdown("[Download from ollama.ai](https://ollama.ai)")
                
                st.write("**Step 2:** Start Ollama")
                st.code("ollama serve", language="bash")
                
                st.write("**Step 3:** Pull a model")
                st.code("ollama pull llama2:7b", language="bash")
                
                st.info("🚀 Then refresh this page and select Ollama!")
    
    elif model_provider == "mock":
        selected_model = st.sidebar.selectbox(
            "Mock Model",
            ["mock-gpt-3.5", "mock-gpt-4", "mock-claude", "mock-fast", "mock-slow"]
        )
    
    else:  # API models
        if not env_ok:
            st.warning("API keys missing - defaulting to mock client for demonstration")
            model_provider = "mock"
            selected_model = "mock-gpt-3.5"
        else:
            model_options = [
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo-16k"
            ]
            selected_model = st.sidebar.selectbox("Select Model", model_options)
    
    # Prompt configuration
    prompt_type = st.sidebar.selectbox(
        "Prompt Type",
        options=[pt.value for pt in PromptType],
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    # Custom prompt option
    use_custom_prompt = st.sidebar.checkbox("Use Custom Prompt")
    custom_prompt = None
    if use_custom_prompt:
        custom_prompt = st.sidebar.text_area("Custom Prompt", height=100)
    
    # Test parameters
    num_requests = st.sidebar.slider("Number of Requests", 1, 100, 10)
    concurrent_requests = st.sidebar.slider("Concurrent Requests", 1, 10, 1)
    
    # Budget configuration
    st.sidebar.subheader("💰 Cost & Budget")
    budget_tier = st.sidebar.selectbox(
        "Budget Tier",
        options=[tier.value for tier in CostTier],
        format_func=lambda x: {
            "development": "🧪 Development ($5/day, $1/test)",
            "demo": "🎯 Demo ($25/day, $10/test)",
            "production": "🚀 Production ($100/day, $50/test)"
        }[x]
    )
    
    # Update cost tracker if tier changed
    selected_tier = CostTier(budget_tier)
    if st.session_state.cost_tracker.budget_config.tier != selected_tier:
        st.session_state.cost_tracker = CostTracker(selected_tier)
    
    # Show current budget status
    budget_status = st.session_state.cost_tracker._get_budget_status()
    
    with st.sidebar.expander("📊 Budget Status"):
        st.progress(budget_status["daily_percentage"] / 100)
        st.write(f"Daily: ${budget_status['daily_used']:.2f} / ${budget_status['daily_limit']:.2f}")
        st.write(f"Remaining: ${budget_status['daily_remaining']:.2f}")
    
    # Cost estimation for planned test
    if selected_model and model_provider == "api":
        estimated_cost = st.session_state.cost_tracker.estimate_test_cost(
            selected_model, num_requests, 50, 100
        )
        can_afford, reason = st.session_state.cost_tracker.can_afford_test(
            selected_model, num_requests, 50, 100
        )
        
        if can_afford:
            st.sidebar.success(f"✅ Estimated cost: ${estimated_cost:.4f}")
        else:
            st.sidebar.error(f"❌ {reason}")
    else:
        st.sidebar.info("💚 Free testing with local/mock models")
    
    # Test name
    test_name = st.sidebar.text_input("Test Name (optional)")
    
    # Output options
    save_results = st.sidebar.checkbox("Save Results", value=True)
    output_format = st.sidebar.selectbox("Output Format", ["json", "csv"])
    
    # Run test button
    if st.sidebar.button("🚀 Run Stress Test", type="primary"):
        # Map UI model provider to internal type
        if model_provider == "local":
            internal_model_type = "local_hf"
        elif model_provider == "ollama":
            internal_model_type = "ollama"
        else:
            internal_model_type = model_provider
        client = create_client(selected_model, internal_model_type)
        if client:
            # Create configuration
            config = StressTestConfig(
                num_requests=num_requests,
                concurrent_requests=concurrent_requests,
                prompt_type=PromptType(prompt_type),
                custom_prompts=[custom_prompt] if custom_prompt else None,
                save_results=save_results,
                output_format=output_format,
                test_name=test_name if test_name else None,
                budget_tier=selected_tier
            )
            
            # Run the test
            run_stress_test(client, config)
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Test", "📈 Historical Results", "💰 Cost Analysis", "🔧 Metrics"])
    
    with tab1:
        if not st.session_state.test_results:
            st.info("👆 Configure your test in the sidebar and click 'Run Stress Test' to get started!")
            
            # Show prompt examples
            st.subheader("Example Prompts")
            for pt in PromptType:
                with st.expander(f"{pt.value.replace('_', ' ').title()} Examples"):
                    examples = st.session_state.prompt_generator._get_prompts_by_type(pt)[:3]
                    for i, example in enumerate(examples, 1):
                        st.text(f"{i}. {example}")
        else:
            st.info("Test results will appear here after running a stress test.")
    
    with tab2:
        st.subheader("Historical Test Results")
        
        if st.session_state.test_results:
            # Create summary table
            summary_data = []
            for result in st.session_state.test_results:
                summary_data.append({
                    "Test Name": result.test_name,
                    "Start Time": result.start_time,
                    "Model": result.config.num_requests,  # This should be model name from config
                    "Requests": result.total_requests,
                    "Success Rate": f"{result.success_rate:.1%}",
                    "Avg Latency": f"{result.avg_latency:.3f}s",
                    "Requests/sec": f"{result.requests_per_second:.2f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Comparison charts
            if len(st.session_state.test_results) > 1:
                st.subheader("Performance Comparison")
                
                # Success rate comparison
                test_names = [r.test_name for r in st.session_state.test_results]
                success_rates = [r.success_rate for r in st.session_state.test_results]
                
                fig_comparison = go.Figure(data=[
                    go.Bar(x=test_names, y=success_rates, name="Success Rate")
                ])
                fig_comparison.update_layout(title="Success Rate Comparison", yaxis_title="Success Rate")
                st.plotly_chart(fig_comparison, use_container_width=True)
        else:
            st.info("No test results yet. Run some tests to see historical data!")
    
    with tab3:
        st.subheader("💰 Cost Analysis & Optimization")
        
        # Cost summary
        cost_summary = st.session_state.cost_tracker.get_cost_summary(days=30)
        
        if cost_summary["total_requests"] > 0:
            # Cost overview metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("30-Day Total", f"${cost_summary['total_cost']:.2f}")
            
            with col2:
                st.metric("Avg Daily Cost", f"${cost_summary['avg_daily_cost']:.2f}")
            
            with col3:
                st.metric("Total Requests", f"{cost_summary['total_requests']:,}")
            
            with col4:
                st.metric("Avg Cost/Request", f"${cost_summary['avg_cost_per_request']:.4f}")
            
            # Model cost breakdown
            if cost_summary["model_breakdown"]:
                st.subheader("Cost by Model")
                model_data = []
                for model, stats in cost_summary["model_breakdown"].items():
                    model_data.append({
                        "Model": model,
                        "Total Cost": f"${stats['cost']:.4f}",
                        "Requests": stats['requests'],
                        "Avg Cost/Request": f"${stats['cost']/stats['requests']:.4f}" if stats['requests'] > 0 else "$0.0000"
                    })
                
                model_df = pd.DataFrame(model_data)
                st.dataframe(model_df, use_container_width=True)
                
                # Cost breakdown chart
                model_names = list(cost_summary["model_breakdown"].keys())
                model_costs = [stats["cost"] for stats in cost_summary["model_breakdown"].values()]
                
                if len(model_names) > 1:
                    fig_cost_pie = px.pie(
                        values=model_costs,
                        names=model_names,
                        title="Cost Distribution by Model"
                    )
                    st.plotly_chart(fig_cost_pie, use_container_width=True)
            
            # Daily cost trend
            if len(cost_summary["daily_costs"]) > 1:
                st.subheader("Daily Cost Trend")
                daily_df = pd.DataFrame([
                    {"Date": date, "Cost": cost} 
                    for date, cost in cost_summary["daily_costs"].items()
                ])
                daily_df["Date"] = pd.to_datetime(daily_df["Date"])
                
                fig_daily = px.line(
                    daily_df, 
                    x="Date", 
                    y="Cost",
                    title="Daily API Costs",
                    labels={"Cost": "Cost ($)"}
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            
            # Cost optimization suggestions
            st.subheader("💡 Optimization Suggestions")
            suggestions = st.session_state.cost_tracker.get_optimization_suggestions()
            for suggestion in suggestions:
                st.info(f"💡 {suggestion}")
                
            # Budget status details
            st.subheader("📊 Budget Status")
            budget_status = st.session_state.cost_tracker._get_budget_status()
            
            # Daily budget progress
            st.write("**Daily Budget**")
            progress = budget_status["daily_percentage"] / 100
            st.progress(progress)
            st.write(f"${budget_status['daily_used']:.2f} / ${budget_status['daily_limit']:.2f} used ({budget_status['daily_percentage']:.1f}%)")
            
            # Current test budget
            st.write("**Current Test Session**")
            test_progress = budget_status["test_percentage"] / 100
            st.progress(test_progress)
            st.write(f"${budget_status['test_used']:.2f} / ${budget_status['test_limit']:.2f} used ({budget_status['test_percentage']:.1f}%)")
            
        else:
            st.info("No cost data yet. Run some tests with API models to see cost analysis!")
            
            # Show model pricing comparison
            st.subheader("📋 Model Pricing Reference")
            pricing_data = []
            for model, pricing in st.session_state.cost_tracker.MODEL_PRICING.items():
                if "mock" not in model.lower() and "local" not in model.lower():
                    pricing_data.append({
                        "Model": model,
                        "Input (per 1K tokens)": f"${pricing.input_cost_per_1k:.4f}",
                        "Output (per 1K tokens)": f"${pricing.output_cost_per_1k:.4f}",
                        "Est. Cost (100 requests)": f"${((50 * pricing.input_cost_per_1k + 100 * pricing.output_cost_per_1k) / 1000) * 100:.2f}"
                    })
            
            pricing_df = pd.DataFrame(pricing_data)
            st.dataframe(pricing_df, use_container_width=True)
    
    with tab4:
        st.subheader("Prometheus Metrics")
        
        # Current metrics summary
        current_stats = st.session_state.metrics.get_current_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requests", current_stats.get("total_requests", 0))
        with col2:
            st.metric("Total Failures", current_stats.get("total_failures", 0))
        with col3:
            st.metric("Active Requests", current_stats.get("active_requests", 0))
        
        # Raw metrics
        with st.expander("Raw Prometheus Metrics"):
            metrics_text = st.session_state.metrics.get_metrics()
            st.text(metrics_text)
        
        # Metrics endpoint info
        st.info("💡 Metrics are available at `/metrics` endpoint when running the application")
    
    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit • [View Documentation](cursor_instructions.md)")


if __name__ == "__main__":
    main() 