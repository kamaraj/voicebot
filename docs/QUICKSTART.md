# Quick Start Guide

## Prerequisites

1. **Python 3.11+**
   ```bash
   python --version
   ```

2. **Ollama with Llama 3.1 8B**
   ```bash
   # Install Ollama
   # Visit: https://ollama.ai/download
   
   # Pull Llama 3.1
   ollama pull llama3.1:8b
   
   # Verify it's running
   ollama list
   ```

3. **Optional: Docker** (for full stack)
   ```bash
   docker --version
   docker-compose --version
   ```

## Installation

### 1. Clone & Setup

```bash
# Navigate to project
cd c:\kamaraj\Prototype\VoiceBot

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env with your settings
# At minimum, set:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: llama3.1:8b)
```

### 3. Create Required Directories

```bash
mkdir data\eval_datasets
mkdir data\synthetic_data
mkdir logs
```

## Running the Application

### Option 1: Development Mode (Recommended for Testing)

```bash
# Start the API server
python -m uvicorn src.api.main:app --reload --port 8000
```

Visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Option 2: Docker (Full Stack)

```bash
# Start all services (API, DB, Redis, Monitoring)
docker-compose up -d

# View logs
docker-compose logs -f voicebot-api

# Stop services
docker-compose down
```

Services:
- API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Phoenix: http://localhost:6006

## Testing the System

### 1. Quick Health Check

```bash
# Using curl (Windows)
curl http://localhost:8000/health

# Using PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health
```

### 2. Send a Test Message

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/conversation ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Hello, what can you do?\"}"
```

Or use the **API docs** at http://localhost:8000/docs

### 3. Test Guardrails

```bash
curl -X POST "http://localhost:8000/api/v1/guardrails/check?text=My email is john@example.com"
```Should detect PII!

### 4. Run Automated Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ --cov=src --cov-report=html
```

### 5. Run Evaluations

```bash
# Full evaluation suite
python scripts/run_evals.py

# Results saved to data/eval_datasets/
```

## Example Usage

### Python SDK

```python
import asyncio
from src.agents.voice_agent import VoiceAgent

async def main():
    agent = VoiceAgent()
    
    response = await agent.process_message(
        user_message="What time is it?",
        conversation_id="demo_001",
        user_id="user_123"
    )
    
    print(f"Response: {response['response']}")
    print(f"Tool Results: {response['tool_results']}")

asyncio.run(main())
```

### API Request (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/conversation",
    json={
        "message": "Can you schedule an appointment for tomorrow at 2pm?",
        "conversation_id": "demo_002",
        "user_id": "user_123"
    }
)

print(response.json())
```

### cURL Examples

```bash
# Basic conversation
curl -X POST http://localhost:8000/api/v1/conversation ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"Hello\"}"

# With context
curl -X POST http://localhost:8000/api/v1/conversation ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"What's my name?\", \"context\": {\"user_name\": \"Alice\"}}"

# Get agent capabilities
curl http://localhost:8000/api/v1/agent/capabilities
```

## Monitoring & Observability

### 1. View Logs

```bash
# Console (structured JSON)
# Logs appear in terminal where you ran the server

# Or check log files (if configured)
cat logs/voicebot.log
```

### 2. Prometheus Metrics

Visit http://localhost:9090 and query:
- `voicebot_requests_total` - Total requests
- `voicebot_llm_latency_seconds` - LLM response times
- `voicebot_guardrail_violations_total` - Safety violations

### 3. Grafana Dashboards

1. Visit http://localhost:3000
2. Login: admin/admin
3. Import dashboard (coming soon)

### 4. LangSmith Tracing

If you have a LangSmith API key:

```bash
# Set in .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_PROJECT=voicebot-dev
```

View traces at: https://smith.langchain.com

## Common Issues

### Issue: Ollama Connection Error

```
Error: Connection refused to localhost:11434
```

**Solution**:
```bash
# Make sure Ollama is running
ollama serve

# Or check if it's running
curl http://localhost:11434/api/tags
```

### Issue: Module Not Found

```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**:
```bash
# Ensure virtual environment is activated
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database Connection Error

**Solution**: If running locally without Docker:
```bash
# Update .env to use SQLite instead
# DATABASE_URL=sqlite:///./data/voicebot.db
```

## Next Steps

1. **Customize the Agent**
   - Edit `src/agents/voice_agent.py`
   - Add your own tools/functions
   - Modify prompts

2. **Add Voice Integration**
   - Get Deepgram API key for STT
   - Get ElevenLabs API key for TTS
   - Integrate Twilio for phone calls

3. **Extend Guardrails**
   - Add custom validation rules
   - Integrate ML-based toxicity models
   - Add domain-specific checks

4. **Deploy to Production**
   - See `docs/deployment.md`
   - Configure environment for scale
   - Set up monitoring alerts

5. **Improve the Model**
   - Fine-tune Llama on your data
   - Implement RAG for knowledge base
   - Add conversation memory

## Getting Help

- **Documentation**: See `docs/` folder
- **API Docs**: http://localhost:8000/docs
- **Issues**: Create an issue in the repo

## Quick Reference

| Command | Purpose |
|---------|---------|
| `ollama pull llama3.1:8b` | Download LLM model |
| `pip install -r requirements.txt` | Install dependencies |
| `python -m uvicorn src.api.main:app --reload` | Start API server |
| `pytest tests/ -v` | Run tests |
| `python scripts/run_evals.py` | Run evaluations |
| `docker-compose up -d` | Start full stack |

## Architecture Overview

```
User Input → Guardrails → Agent (Llama 3.1) → Tools → Response
                ↓                ↓                ↓
             Logging        Tracing          Metrics
```

Happy Building! 🚀
