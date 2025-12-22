# 🏠 Local-Only Setup Guide

## ✅ What You Need (Minimal Setup)

**Only 2 Requirements:**
1. **Python 3.11+** (you already have this)
2. **Ollama with Llama 3.1 8B** (you already have this running!)

**No Docker, No Cloud, No Database Server required!**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Activate Virtual Environment
```powershell
cd c:\kamaraj\Prototype\VoiceBot

# Create virtual environment (first time only)
python -m venv venv

# Activate
venv\Scripts\activate
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure for Local Use
```powershell
# Copy local config
copy .env.local .env
```

The `.env.local` file is pre-configured for local-only use:
- ✅ SQLite database (no PostgreSQL needed)
- ✅ In-memory Redis alternative
- ✅ Ollama on localhost
- ✅ All cloud services disabled

### Step 4: Create Data Directories
```powershell
mkdir data\eval_datasets
mkdir data\synthetic_data
mkdir logs
```

### Step 5: Run the API Server
```powershell
python -m uvicorn src.api.main:app --reload --port 8000
```

**That's it!** 🎉

---

## 🧪 Test It's Working

### Open a new PowerShell window and test:

```powershell
# 1. Health check
Invoke-WebRequest -Uri http://localhost:8000/health

# 2. Send a test message
$body = @{
    message = "Hello, what can you do?"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/conversation `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# 3. Test guardrails
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/guardrails/check?text=My email is test@example.com"
```

---

## 📊 View the API

**Open in your browser:**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## 🧪 Run Tests

```powershell
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests
pytest tests/ -v --cov=src

# Run evaluations
python scripts/run_evals.py
```

---

## 📁 Local Data Storage

Everything is stored locally in SQLite:

```
data/
├── voicebot.db          # SQLite database (created automatically)
├── eval_datasets/       # Evaluation results
└── synthetic_data/      # Generated test data

logs/
└── voicebot.log        # Application logs
```

---

## 🔧 What's Running Locally

```
┌─────────────────────────────────────┐
│  Your Computer                      │
│                                     │
│  ┌──────────────┐                  │
│  │ Ollama       │ Port 11434       │
│  │ Llama 3.1 8B │                  │
│  └──────────────┘                  │
│         ↓                           │
│  ┌──────────────┐                  │
│  │ FastAPI      │ Port 8000        │
│  │ VoiceBot API │                  │
│  └──────────────┘                  │
│         ↓                           │
│  ┌──────────────┐                  │
│  │ SQLite DB    │ data/voicebot.db │
│  └──────────────┘                  │
│                                     │
└─────────────────────────────────────┘
```

**No external services needed!**

---

## 🎯 Usage Examples

### Python Code

```python
import asyncio
from src.agents.voice_agent import VoiceAgent

async def main():
    # Initialize agent
    agent = VoiceAgent()
    
    # Send a message
    response = await agent.process_message(
        user_message="What time is it?",
        conversation_id="local_test"
    )
    
    print(f"Response: {response['response']}")
    print(f"Tools used: {response.get('tool_results', {})}")

# Run it
asyncio.run(main())
```

### PowerShell API Calls

```powershell
# Simple conversation
$body = @{
    message = "Schedule an appointment for tomorrow at 2pm"
    conversation_id = "test_123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/api/v1/conversation `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Depth 10
```

---

## 🛠️ Development Workflow

### 1. Make Code Changes
Edit any file in `src/`

### 2. Auto-Reload
The server automatically reloads when you save changes (thanks to `--reload` flag)

### 3. Test Your Changes
```powershell
# Quick test
pytest tests/unit/test_guardrails.py -v

# Full test suite
pytest tests/ -v
```

### 4. Check Logs
All logs appear in your terminal with structured JSON output

---

## 📊 View Metrics (Local)

Instead of Prometheus/Grafana, use the built-in KPI dashboard:

```python
# Add to your code or run interactively
from src.observability.kpi_dashboard import kpi_dashboard

# Generate text report
report = kpi_dashboard.generate_report()
print(report)

# Export to JSON
kpi_dashboard.export_json("data/kpis.json")
```

---

## 🔍 View Traces (Local)

Traces are logged to console in structured format:

```python
# All traces appear in terminal output
# Look for log entries with:
# - trace_id
# - conversation_id
# - llm_call_started/completed
# - agent_step_started/completed
```

To see detailed traces:
```powershell
# Run with DEBUG logging
$env:LOG_LEVEL="DEBUG"
python -m uvicorn src.api.main:app --reload
```

---

## 🎓 Interactive Development

### Use IPython for testing:

```powershell
# Activate venv first
venv\Scripts\activate

# Start IPython
ipython
```

```python
# In IPython
from src.agents.voice_agent import VoiceAgent
from src.guardrails.engine import guardrails_engine
from src.evals.framework import EvaluationFramework

# Test guardrails
result = guardrails_engine.check_input("My email is test@example.com")
print(result)

# Test agent
agent = VoiceAgent()
response = await agent.process_message("Hello", "test")
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused to Ollama"

**Check if Ollama is running:**
```powershell
# Test Ollama
curl http://localhost:11434/api/tags
```

**If not running:**
```powershell
ollama serve
```

### Issue: "Module not found"

**Ensure venv is activated:**
```powershell
# You should see (venv) in your prompt
venv\Scripts\activate

# Reinstall if needed
pip install -r requirements.txt
```

### Issue: "Database locked"

**SQLite is in use. Just restart the server.**

### Issue: Port 8000 already in use

```powershell
# Use a different port
python -m uvicorn src.api.main:app --reload --port 8001
```

---

## 📈 Performance on Local Machine

Expected performance (varies by CPU):

| Metric | Local (CPU) | With GPU |
|--------|-------------|----------|
| LLM Response Time | 1-3 seconds | 200-500ms |
| Full Conversation | 2-5 seconds | 500ms-1s |
| Concurrent Requests | 1-3 | 10+ |

**Tips for better performance:**
1. Close other heavy applications
2. Use smaller models if needed (`ollama pull llama3.1:8b-instruct-q4_0`)
3. Reduce max_tokens in config

---

## 🎯 What Works Locally

✅ **Working out of the box:**
- Full agentic AI with LangGraph
- Llama 3.1 8B local LLM
- All guardrails (PII, toxicity, injection)
- Structured logging
- Metrics collection
- KPI tracking
- All evaluations
- Synthetic personas
- Complete test suite
- SQLite database

❌ **Not needed locally:**
- Docker / Docker Compose
- PostgreSQL server
- Redis server
- Cloud services
- Prometheus/Grafana (use built-in KPI dashboard instead)

---

## 🔄 Upgrading to Full Stack Later

When you're ready, you can easily upgrade:

1. **Add PostgreSQL**: Change `DATABASE_URL` in `.env`
2. **Add Redis**: Change `REDIS_URL` in `.env`
3. **Add Monitoring**: Run `docker-compose up prometheus grafana`
4. **Deploy**: Use the Dockerfile

**But for development, local is perfect!** ✨

---

## 📝 Daily Workflow

```powershell
# Morning: Start development
cd c:\kamaraj\Prototype\VoiceBot
venv\Scripts\activate
python -m uvicorn src.api.main:app --reload

# Code, test, iterate...

# When done: Stop server (Ctrl+C)
```

---

## 🎉 You're All Set!

Everything runs locally on your machine:
- ✅ No cloud dependencies
- ✅ No Docker required
- ✅ No database server needed
- ✅ Just Python + Ollama
- ✅ Fast iteration
- ✅ Full features

**Start building! 🚀**

---

## 💡 Quick Commands Reference

| Task | Command |
|------|---------|
| Start server | `python -m uvicorn src.api.main:app --reload` |
| Run tests | `pytest tests/ -v` |
| Run evals | `python scripts/run_evals.py` |
| Interactive shell | `ipython` |
| View API docs | http://localhost:8000/docs |
| Check health | http://localhost:8000/health |

---

**Happy Local Development! 🏠**
