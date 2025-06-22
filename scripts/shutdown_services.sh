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

# Storage cleanup option
echo ""
echo "=================================================="
echo "💾 Storage Cleanup (Optional)"
echo "=================================================="

# Function to get directory size
get_size() {
    if [ -d "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

OLLAMA_SIZE=$(get_size ~/.ollama)
HF_SIZE=$(get_size ~/.cache/huggingface)

echo "📊 Current Storage Usage:"
echo "🦙 Ollama Models:      $OLLAMA_SIZE"
echo "🤗 Hugging Face Cache: $HF_SIZE"
echo ""

read -p "🧹 Clean up model storage to free space? [y/N]: " cleanup_storage

if [[ $cleanup_storage =~ ^[Yy]$ ]]; then
    echo ""
    echo "🛠️  Storage Cleanup Options:"
    echo "1️⃣  Keep models (just shutdown services)"
    echo "2️⃣  Remove Ollama models (~$OLLAMA_SIZE)"
    echo "3️⃣  Remove HuggingFace cache (~$HF_SIZE)" 
    echo "4️⃣  Remove ALL models (frees ~7GB+)"
    echo ""
    
    read -p "Choose option [1-4]: " cleanup_option
    
    case $cleanup_option in
        2)
            echo "🗑️  Removing Ollama models..."
            ollama list --format json 2>/dev/null | jq -r '.[].name' | xargs -I {} ollama rm {} 2>/dev/null || echo "Manual cleanup required"
            rm -rf ~/.ollama/models/* 2>/dev/null
            echo "✅ Ollama models removed"
            ;;
        3)
            echo "🗑️  Removing HuggingFace cache..."
            rm -rf ~/.cache/huggingface/*
            echo "✅ HuggingFace cache cleared"
            ;;
        4)
            echo "🗑️  Removing ALL models..."
            ollama list --format json 2>/dev/null | jq -r '.[].name' | xargs -I {} ollama rm {} 2>/dev/null
            rm -rf ~/.ollama/models/* 2>/dev/null
            rm -rf ~/.cache/huggingface/*
            rm -rf ./results/*
            echo "✅ All models and caches cleared"
            ;;
        *)
            echo "ℹ️  Keeping all models"
            ;;
    esac
    
    echo ""
    echo "📊 New Storage Usage:"
    echo "🦙 Ollama Models:      $(get_size ~/.ollama)"
    echo "🤗 Hugging Face Cache: $(get_size ~/.cache/huggingface)"
fi

echo ""
echo "=================================================="
echo "🎉 Shutdown Complete!"
echo "💡 To restart later: ./start_services.sh"
echo "💽 Models will auto-download when needed"
echo "==================================================" 