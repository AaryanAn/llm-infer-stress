#!/bin/bash

echo "🚀 Starting LLM Stress Testing Development Environment"
echo "====================================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root directory."
    echo "   cd /path/to/llm-infer-stress"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv-llm-infer" ]; then
    echo "❌ Error: Virtual environment not found at .venv-llm-infer"
    echo "   Please create it first: python3 -m venv .venv-llm-infer"
    exit 1
fi

echo "🔧 Step 1: Starting Ollama service..."
./start_services.sh

echo ""
echo "🔧 Step 2: Checking virtual environment..."
if [ -f ".venv-llm-infer/bin/activate" ]; then
    echo "✅ Virtual environment found"
else
    echo "❌ Virtual environment activation script not found"
    exit 1
fi

echo ""
echo "🔧 Step 3: Creating development startup script..."

# Create a temporary script that will run in the user's shell
cat > temp_dev_start.sh << 'EOF'
#!/bin/bash

echo "🐍 Activating virtual environment..."
source .venv-llm-infer/bin/activate

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""

echo "📱 Starting Streamlit dashboard with auto-reload..."
echo "🌐 Dashboard will open at: http://localhost:8501"
echo "🔄 Auto-reload enabled - changes will refresh automatically"
echo ""
echo "🛑 To stop: Press Ctrl+C, then run ./shutdown_services.sh"
echo ""

# Start Streamlit with development settings
exec streamlit run app.py --server.runOnSave true --server.headless false
EOF

chmod +x temp_dev_start.sh

echo ""
echo "=================================================="
echo "🎉 Ready to start development!"
echo "=================================================="
echo ""
echo "🚀 Run this command to start the dashboard:"
echo "   ./temp_dev_start.sh"
echo ""
echo "Or manually:"
echo "   source .venv-llm-infer/bin/activate"
echo "   streamlit run app.py --server.runOnSave true"
echo ""
echo "📋 What's running:"
echo "   ✅ Ollama service (background)"
echo "   🔜 Streamlit dashboard (after running command above)"
echo ""
echo "💡 The dashboard will open automatically in your browser"
echo "🔄 Code changes will auto-reload"
echo "🛑 When done: Ctrl+C then ./shutdown_services.sh" 