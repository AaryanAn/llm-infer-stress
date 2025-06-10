#!/bin/bash

echo "🚀 Starting LLM Inference Stress Testing Services..."
echo "=================================================="

# Start Ollama service
echo "🦙 Starting Ollama service..."
brew services start ollama
if [ $? -eq 0 ]; then
    echo "✅ Ollama service started"
    # Wait for Ollama to be ready
    echo "⏳ Waiting for Ollama to be ready..."
    sleep 3
    
    # Test if Ollama is responding
    if curl -s http://localhost:11434 > /dev/null; then
        echo "✅ Ollama is responding on localhost:11434"
    else
        echo "⚠️  Ollama may need more time to start"
    fi
else
    echo "❌ Failed to start Ollama service"
fi

# List available models
echo ""
echo "📋 Available Ollama models:"
ollama list 2>/dev/null || echo "❌ Ollama not ready yet"

# Start Streamlit dashboard
echo ""
echo "📱 Starting Streamlit dashboard..."
echo "🌐 Dashboard will be available at: http://localhost:8501"
echo "📊 To start the dashboard, run:"
echo "   streamlit run app.py"

echo "=================================================="
echo "🎉 Services are ready!"
echo ""
echo "🚀 Next Steps:"
echo "1. Activate virtual environment:"
echo "   source .venv-llm-infer/bin/activate"
echo ""
echo "2. Start Streamlit dashboard:"
echo "   streamlit run app.py --server.runOnSave true"
echo ""
echo "3. Open browser: http://localhost:8501"
echo ""
echo "💡 Or use the automated development script:"
echo "   ./dev_start.sh"
echo ""
echo "🛑 To shut down everything later, run:"
echo "   ./shutdown_services.sh" 