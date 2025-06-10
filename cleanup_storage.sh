#!/bin/bash

echo "🧹 LLM Inference Storage Cleanup Tool"
echo "====================================="

# Function to get directory size in human readable format
get_size() {
    if [ -d "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# Current storage analysis
echo "📊 Current Storage Usage:"
echo "------------------------"

OLLAMA_SIZE=$(get_size ~/.ollama)
HF_SIZE=$(get_size ~/.cache/huggingface)
PROJECT_RESULTS=$(get_size ./results)
PROJECT_LOGS=$(get_size ./logs)

echo "🦙 Ollama Models:      $OLLAMA_SIZE"
echo "🤗 Hugging Face Cache: $HF_SIZE"
echo "📋 Project Results:    $PROJECT_RESULTS"
echo "📝 Project Logs:       $PROJECT_LOGS"
echo ""

# Calculate total
TOTAL=$(du -sh ~/.ollama ~/.cache/huggingface ./results ./logs 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo "~7-10GB")
echo "💾 Total LLM Storage: ~${TOTAL}"
echo ""

# Cleanup options
echo "🛠️  Cleanup Options:"
echo "==================="
echo ""

read -p "1️⃣  Remove ALL Ollama models? (frees ~${OLLAMA_SIZE}) [y/N]: " remove_ollama
if [[ $remove_ollama =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing Ollama models..."
    ollama list --format json 2>/dev/null | jq -r '.[].name' | xargs -I {} ollama rm {} 2>/dev/null || echo "Manual cleanup required"
    # Also remove the model directory
    rm -rf ~/.ollama/models/* 2>/dev/null
    echo "✅ Ollama models removed"
fi

echo ""
read -p "2️⃣  Remove Hugging Face cache? (frees ~${HF_SIZE}) [y/N]: " remove_hf
if [[ $remove_hf =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing Hugging Face cache..."
    rm -rf ~/.cache/huggingface/*
    echo "✅ Hugging Face cache cleared"
fi

echo ""
read -p "3️⃣  Remove project test results? (frees ~${PROJECT_RESULTS}) [y/N]: " remove_results
if [[ $remove_results =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing test results..."
    rm -rf ./results/*
    echo "✅ Test results cleared"
fi

echo ""
read -p "4️⃣  Remove project logs? (frees ~${PROJECT_LOGS}) [y/N]: " remove_logs
if [[ $remove_logs =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing logs..."
    rm -rf ./logs/*
    echo "✅ Logs cleared"
fi

echo ""
echo "🧹 Cleanup Complete!"
echo "==================="

# Show new storage usage
echo "📊 New Storage Usage:"
echo "--------------------"
echo "🦙 Ollama Models:      $(get_size ~/.ollama)"
echo "🤗 Hugging Face Cache: $(get_size ~/.cache/huggingface)"
echo "📋 Project Results:    $(get_size ./results)"
echo "📝 Project Logs:       $(get_size ./logs)"

echo ""
echo "💡 To re-download models later:"
echo "  • Ollama: ollama pull <model-name>"
echo "  • HuggingFace: Models auto-download on first use"
echo ""
echo "⚡ Your system is now optimized!" 