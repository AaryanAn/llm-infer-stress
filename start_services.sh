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
echo "💡 To test your models:"
echo "   1. Open http://localhost:8501 in your browser"
echo "   2. Select 'Ollama' as provider"
echo "   3. Choose your model and run stress tests"
echo ""
echo "🛑 To shut down everything later, run:"
echo "   ./shutdown_services.sh" 