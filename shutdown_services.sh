#!/bin/bash

echo "🛑 Shutting down LLM Inference Stress Testing Services..."
echo "=================================================="

# Stop all Streamlit processes
echo "📱 Stopping Streamlit processes..."
pkill -f "streamlit run"
if [ $? -eq 0 ]; then
    echo "✅ Streamlit processes stopped"
else
    echo "ℹ️  No Streamlit processes found"
fi

# Stop Ollama service (if running as brew service)
echo "🦙 Stopping Ollama service..."
brew services stop ollama 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Ollama brew service stopped"
else
    echo "ℹ️  Ollama brew service was not running"
fi

# Kill any remaining Ollama processes
echo "🔪 Killing any remaining Ollama processes..."
pkill -f "ollama"
if [ $? -eq 0 ]; then
    echo "✅ Ollama processes killed"
else
    echo "ℹ️  No Ollama processes found"
fi

# Optional: Free up GPU memory (if you were using GPU)
echo "🧹 Clearing any cached models from memory..."
# This is more relevant for CUDA, but good practice
python3 -c "import gc; gc.collect()" 2>/dev/null

echo "=================================================="
echo "🎉 All LLM services have been shut down!"
echo "💾 Model files are still cached locally for faster startup next time"
echo "🔋 Your system is now free to shut down safely"

# Check if any processes are still running
echo ""
echo "🔍 Checking for any remaining processes..."
REMAINING=$(ps aux | grep -E "(streamlit|ollama)" | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo "✅ Clean shutdown - no processes remaining"
else
    echo "⚠️  Warning: $REMAINING processes may still be running:"
    ps aux | grep -E "(streamlit|ollama)" | grep -v grep
fi 