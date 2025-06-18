# 🚀 Development Workflow Guide

## Quick Start for Development

### **Daily Development Routine:**

```bash
# 1. Navigate to project
cd /path/to/llm-infer-stress

# 2. Activate virtual environment
source .venv-llm-infer/bin/activate

# 3. Start all services (recommended)
./start_services.sh

# 4. Start development dashboard
streamlit run app.py --server.port 8501 --server.runOnSave true
```

### **When to Use Each Script:**

#### **🟢 Use `./start_services.sh` when:**
- Starting fresh development session
- Need Ollama models for testing
- Want to see available models
- First time setup

#### **🟡 Manual start when:**
- Debugging specific components
- Testing individual scripts
- Ollama already running
- Quick code testing

#### **🔴 Use `./shutdown_services.sh` when:**
- Done for the day
- Switching projects
- Need to free up RAM/storage
- Before system shutdown

## Development Patterns

### **Frontend Development (Streamlit):**
```bash
# Auto-reload on file changes
streamlit run app.py --server.runOnSave true

# Different port for testing
streamlit run app.py --server.port 8502
```

### **Backend Development (LLM Clients):**
```bash
# Test specific clients
python -c "from llm_infer.clients.ollama_client import OllamaClient; print('Ollama OK')"

# Test with mock data
python test_mock.py

# Test local models
python test_local_models.py
```

### **Adding New Models:**
1. **Ollama Models:**
   ```bash
   ollama pull new-model-name:tag
   # Then add to ollama_client.py popular_models dict
   ```

2. **Hugging Face Models:**
   ```python
   # Add to huggingface_client.py SUPPORTED_MODELS dict
   ```

## Debugging

### **Common Issues & Solutions:**

#### **"Ollama not responding"**
```bash
# Check if running
brew services list | grep ollama

# Restart if needed
brew services restart ollama
```

#### **"Model not found"**
```bash
# Check available models
ollama list

# Pull missing model
ollama pull model-name
```

#### **"Streamlit port in use"**
```bash
# Kill existing processes
./shutdown_services.sh

# Or use different port
streamlit run app.py --server.port 8502
```

#### **"Memory issues"**
```bash
# Quick cleanup
./shutdown_services.sh
# Choose storage cleanup option
```

## File Structure for Development

```
llm-infer-stress/
├── app.py                 # 🎯 Main dashboard - start here
├── start_services.sh      # 🚀 Start everything
├── shutdown_services.sh   # 🛑 Stop & cleanup
├── 
├── llm_infer/            # 🔧 Core library
│   ├── clients/          # Add new LLM providers here
│   ├── core/            # Stress testing logic
│   └── metrics/         # Prometheus metrics
├── 
├── test_*.py            # 🧪 Test individual components
├── benchmark.py         # 📊 CLI interface
└── results/            # 📋 Test outputs
```

## Development Workflow Examples

### **Adding a New Feature:**
```bash
# 1. Start development environment
./start_services.sh
streamlit run app.py --server.runOnSave true

# 2. Make code changes
# 3. Test automatically reloads in browser
# 4. Test with: python test_your_feature.py
# 5. Commit changes: git add . && git commit -m "feature"
```

### **Testing Performance:**
```bash
# Quick test with mock client
python demo_local_stress_test.py

# Real test with Ollama
python benchmark.py --provider ollama --model deepseek-coder:6.7b

# Full dashboard test
streamlit run app.py
# Select Ollama → DeepSeek → Run test
```

### **Before Committing:**
```bash
# Test everything works
python test_mock.py
python test_local_models.py

# Clean up and shutdown
./shutdown_services.sh

# Commit
git add .
git commit -m "descriptive message"
git push
```

## Pro Tips

1. **Always use the virtual environment:** `source .venv-llm-infer/bin/activate`
2. **Use auto-reload during development:** `--server.runOnSave true`
3. **Test with mock client first** before using real models
4. **Monitor storage usage** - models can be 5GB+
5. **Shutdown cleanly** to free resources
6. **Check logs** in terminal if something breaks

## Quick Commands Cheat Sheet

| Task | Command |
|------|---------|
| **Start Development** | `./start_services.sh && streamlit run app.py` |
| **Stop Everything** | `./shutdown_services.sh` |
| **Test Components** | `python test_mock.py` |
| **Check Storage** | `du -sh ~/.ollama ~/.cache/huggingface` |
| **Add Ollama Model** | `ollama pull model-name` |
| **Debug Port Issues** | `lsof -i :8501` |
| **Check Running Services** | `ps aux \| grep -E "(streamlit\|ollama)"` | 