# 🏠 LOCAL-ONLY Development Guide

## You're All Set for Local Development!

Everything is configured to run **100% locally** on your machine. No Docker, no cloud, no external databases.

---

## ⚡ **ONE-COMMAND START**

```powershell
.\start_local.bat
```

That's it! This will:
1. ✅ Create virtual environment (if needed)
2. ✅ Install dependencies
3. ✅ Configure for local use
4. ✅ Create data directories
5. ✅ Start the API server

**Open in browser**: http://localhost:8000/docs

---

## 🧪 **Verify Everything Works**

In a new PowerShell window:

```powershell
# Activate venv
venv\Scripts\activate

# Run test script
python scripts\test_local_setup.py
```

This will test:
- ✅ AI Agent (with Llama 3.1 8B)
- ✅ Guardrails (PII, toxicity, injection)
- ✅ KPI Dashboard
- ✅ All core functionality

---

## 🎯 **What's Running**

```
Your PC
├── Ollama (Port 11434) ← Llama 3.1 8B
├── FastAPI (Port 8000) ← VoiceBot API
└── SQLite ← data/voicebot.db
```

**No external services!**

---

## 📊 **Project Structure**

```
VoiceBot/
├── start_local.bat          ← ONE-COMMAND START!
├── .env.local               ← Local configuration
├── LOCAL_SETUP.md           ← Full local setup guide
│
├── src/                     ← Your code
│   ├── agents/              ← AI agent (LangGraph + Llama)
│   ├── guardrails/          ← Safety (PII, toxicity)
│   ├── observability/       ← Logging, metrics, KPIs
│   ├── evals/               ← Testing framework
│   └── api/                 ← FastAPI server
│
├── tests/                   ← Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── test_local_setup.py  ← Verify setup
│   └── run_evals.py         ← Run evaluations
│
└── data/                    ← Local storage
    ├── voicebot.db          ← SQLite database
    ├── eval_datasets/       ← Eval results
    └── synthetic_data/      ← Test data
```

---

## 🚀 **Quick Usage**

### Python API

```python
import asyncio
from src.agents.voice_agent import VoiceAgent

async def main():
    agent = VoiceAgent()
    
    response = await agent.process_message(
        user_message="What time is it?",
        conversation_id="test123"
    )
    
    print(response['response'])

asyncio.run(main())
```

### PowerShell API

```powershell
$body = @{
    message = "Hello!"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/api/v1/conversation `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## ✅ **Everything Included (Local)**

| Feature | Status | Details |
|---------|--------|---------|
| **AI Agent** | ✅ | LangGraph + Llama 3.1 8B |
| **Guardrails** | ✅ | PII, toxicity, injection |
| **Tracing** | ✅ | Console logs |
| **Metrics** | ✅ | In-memory tracking |
| **KPIs** | ✅ | Text dashboard |
| **Evals** | ✅ | Full test framework |
| **Personas** | ✅ | Synthetic users |
| **Testing** | ✅ | Unit, integration, E2E |
| **Database** | ✅ | SQLite (local file) |
| **Logging** | ✅ | Structured JSON |

**All working locally, no cloud needed!**

---

## 📚 **Documentation**

- **Quick Start**: `LOCAL_SETUP.md` (detailed guide)
- **Architecture**: `docs/architecture.md`
- **Testing**: `docs/evals.md`
- **Roadmap**: `ROADMAP.md`

---

## 🎓 **Learning Path**

### Day 1: Get Familiar
```powershell
# 1. Start server
.\start_local.bat

# 2. Test it works
python scripts\test_local_setup.py

# 3. Explore API docs
# Visit: http://localhost:8000/docs
```

### Day 2: Understand Components
```powershell
# Read the code
# Start with: src/agents/voice_agent.py
```

### Day 3: Customize
```python
# Add your own tools
# Edit: src/agents/voice_agent.py
# Add custom functions to tools dictionary
```

### Week 2: Add Features
- Integrate voice (STT/TTS)
- Add phone calling (Twilio)
- Build frontend

---

## 💡 **Tips for Local Development**

1. **Keep Ollama running** in background
2. **Use `--reload`** flag for auto-restart on code changes
3. **Check logs** in terminal for debugging
4. **Run tests** before committing changes
5. **Use IPython** for interactive testing

---

## 🐛 **Common Issues**

### "Ollama connection failed"
```powershell
# Start Ollama
ollama serve

# Test it
curl http://localhost:11434/api/tags
```

### "Module not found"
```powershell
# Activate venv
venv\Scripts\activate

# Reinstall
pip install -r requirements.txt
```

### "Port 8000 in use"
```powershell
# Use different port
python -m uvicorn src.api.main:app --reload --port 8001
```

---

## 🎉 **You Have Everything!**

✅ **Production-ready code** - All industry standards  
✅ **Local development** - No cloud dependencies  
✅ **One-command start** - `start_local.bat`  
✅ **Complete documentation** - Everything explained  
✅ **Test framework** - Verify quality  
✅ **Extensible** - Easy to customize  

**Start building your voice AI product!** 🚀

---

## 📞 **Quick Commands**

| Action | Command |
|--------|---------|
| Start everything | `.\start_local.bat` |
| Test setup | `python scripts\test_local_setup.py` |
| Run tests | `pytest tests/ -v` |
| Run evals | `python scripts\run_evals.py` |
| API docs | http://localhost:8000/docs |

---

**Happy local development! 🏠✨**
