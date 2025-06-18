#!/bin/bash

echo "🚀 LLM Stress Testing - Complete Development Startup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: app.py not found${NC}"
    echo "Please run this script from the project root directory:"
    echo "cd /path/to/llm-infer-stress"
    exit 1
fi

# Check virtual environment
if [ ! -d ".venv-llm-infer" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv .venv-llm-infer
    echo "Installing dependencies..."
    .venv-llm-infer/bin/pip install -r requirements.txt
fi

echo -e "${BLUE}🔧 Step 1: Starting Ollama service...${NC}"
brew services start ollama > /dev/null 2>&1

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
sleep 3

if curl -s http://localhost:11434 > /dev/null; then
    echo -e "${GREEN}✅ Ollama is ready${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama may need more time, continuing anyway...${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Step 2: Activating virtual environment...${NC}"
source .venv-llm-infer/bin/activate

echo -e "${GREEN}✅ Virtual environment activated${NC}"

echo ""
echo -e "${BLUE}🔧 Step 3: Starting Streamlit dashboard...${NC}"
echo -e "${GREEN}🌐 Dashboard URL: http://localhost:8501${NC}"
echo -e "${GREEN}🔄 Auto-reload: Enabled${NC}"
echo ""
echo -e "${YELLOW}💡 Available models:${NC}"
ollama list 2>/dev/null | head -5 || echo "   Run 'ollama pull model-name' to add models"

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Starting dashboard in 3 seconds...${NC}"
echo "🛑 To stop: Press Ctrl+C, then run ./shutdown_services.sh"
echo "=================================================="

sleep 3

# Start Streamlit with all the best development settings
exec streamlit run app.py \
    --server.runOnSave true \
    --server.headless false \
    --browser.serverAddress localhost \
    --browser.gatherUsageStats false \
    --server.port 8501 