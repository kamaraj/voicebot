# 🎯 VoiceBot AI - Local Setup Quick Reference

## ⚡ INSTANT START

```powershell
cd c:\kamaraj\Prototype\VoiceBot
.\start_local.bat
```

**Done!** Open http://localhost:8000/docs

---

## 🧪 TEST IT

```powershell
# In a NEW PowerShell window:
venv\Scripts\activate
python scripts\test_local_setup.py
```

---

## 📞 EXAMPLE USAGE

### PowerShell (Quick Test)
```powershell
$body = @{message = "What time is it?"} | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/v1/conversation -Method POST -ContentType "application/json" -Body $body
```

### Python (In your code)
```python
import asyncio
from src.agents.voice_agent import VoiceAgent

async def main():
    agent = VoiceAgent()
    response = await agent.process_message("Hello!", "test_conv")
    print(response['response'])

asyncio.run(main())
```

---

## ✅ WHAT YOU HAVE

| Component | Status | Storage |
|-----------|--------|---------|
| AI Agent (Llama 3.1 8B) | ✅ Local | Ollama |
| Guardrails (PII, Safety) | ✅ Local | Python |
| Database | ✅ Local | SQLite file |
| Metrics & KPIs | ✅ Local | In-memory |
| Logging | ✅ Local | Console + file |
| Testing | ✅ Local | pytest |
| Evaluations | ✅ Local | JSON files |

**Zero cloud dependencies!**

---

## 🛠️ DAILY COMMANDS

```powershell
# Start server
.\start_local.bat

# Run tests
pytest tests/ -v

# Run evaluations
python scripts\run_evals.py

# Interactive Python
ipython
```

---

## 🐛 TROUBLESHOOTING

**Issue**: Ollama not responding
```powershell
# Solution:
ollama serve
```

**Issue**: Module not found
```powershell
# Solution:
venv\Scripts\activate
pip install -r requirements.txt
```

**Issue**: Port in use
```powershell
# Solution: Use different port
python -m uvicorn src.api.main:app --reload --port 8001
```

---

## 📁 WHERE IS EVERYTHING?

```
VoiceBot/
├── start_local.bat          ← START HERE!
├── .env.local              ← Your config
├── src/
│   ├── agents/             ← AI logic
│   ├── guardrails/         ← Safety
│   ├── api/                ← API server
│   └── observability/      ← Metrics, logs
├── tests/                  ← Test suites
├── scripts/
│   ├── test_local_setup.py ← Verify setup
│   └── run_evals.py        ← Run evals
└── data/
    ├── voicebot.db         ← SQLite DB (auto-created)
    ├── eval_datasets/      ← Eval results
    └── test_kpis.json      ← KPI reports
```

---

## 🎓 LEARNING PATH

**Day 1**: Get it running
```powershell
.\start_local.bat
python scripts\test_local_setup.py
```

**Day 2**: Read code
- Start with: `src/agents/voice_agent.py`
- Then: `src/guardrails/engine.py`

**Day 3**: Customize
- Add your own tools
- Modify prompts
- Test changes

**Week 2**: Add features
- Voice (STT/TTS)
- Phone calls (Twilio)
- Frontend UI

---

## 💡 PRO TIPS

1. **Keep Ollama running** - Better performance
2. **Use --reload flag** - Auto-restart on changes
3. **Check terminal logs** - Structured JSON output
4. **Run tests often** - Catch issues early
5. **Use IPython** - Interactive testing

---

## 🎯 WHAT WORKS NOW

✅ Complete AI agent with multi-step reasoning  
✅ LLM integration (Llama 3.1 8B via Ollama)  
✅ Safety guardrails (PII, toxicity, injection)  
✅ Comprehensive logging & metrics  
✅ Evaluation framework  
✅ Test suites (unit, integration, E2E)  
✅ KPI dashboard  
✅ Synthetic personas  
✅ Production-ready API  
✅ Complete documentation  

---

## 🚀 NEXT STEPS

1. **Run it**: `.\start_local.bat`
2. **Test it**: `python scripts\test_local_setup.py`
3. **Explore it**: http://localhost:8000/docs
4. **Customize it**: Edit `src/agents/voice_agent.py`
5. **Build it**: Add voice, phone, frontend

---

## 📚 DOCS

- `README.md` - Overview
- `LOCAL_SETUP.md` - Detailed local guide
- `IMPLEMENTATION_SUMMARY.md` - What's included
- `ROADMAP.md` - Path to production
- `docs/architecture.md` - System design
- `docs/evals.md` - Testing guide

---

## 🎉 YOU'RE READY!

Everything is configured for **100% local development**.

**Just run**: `.\start_local.bat`

Then build the next Vapi.ai! 🚀

---

**Questions?** Check the docs or run:
```powershell
python scripts\test_local_setup.py
```
