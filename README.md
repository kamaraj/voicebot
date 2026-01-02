# 🎙️ VoiceBot - AI-Powered Customer Support

> **Production-ready voice AI platform with RAG, semantic caching, and multi-provider LLM support**

[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?style=for-the-badge&logo=vercel)](https://voicebot-kamaraj-v1.vercel.app)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

---

## 🌐 Live Demo

| Interface | URL |
|-----------|-----|
| **Chat UI** | https://voicebot-kamaraj-v1.vercel.app/chat |
| **Voice Chat** | https://voicebot-kamaraj-v1.vercel.app/voice |
| **Knowledge Base** | https://voicebot-kamaraj-v1.vercel.app/help |
| **API Docs** | https://voicebot-kamaraj-v1.vercel.app/docs |

---

## ✨ Features

### 🤖 **AI & LLM**
- **Multi-Provider Support**: Ollama, Groq, Google Gemini, OpenAI
- **RAG (Retrieval-Augmented Generation)**: ChromaDB + semantic search
- **Semantic Caching**: Consistent answers for similar questions
- **Concise Responses**: Strict document-only answers, no hallucination

### 🎤 **Voice**
- **Speech-to-Text**: Browser-native + Whisper backend
- **Text-to-Speech**: Browser-native synthesis
- **Real-time Streaming**: FastRTC WebSocket support

### 🛡️ **Safety & Quality**
- **Guardrails**: PII detection, toxicity filtering, injection prevention
- **Response Validation**: Ensures accurate, document-based answers
- **Async Processing**: Non-blocking guardrails checks

### 📊 **Observability**
- **Structured Logging**: JSON logs with request tracing
- **Metrics**: Prometheus-compatible metrics endpoint
- **Token Tracking**: Usage and cost estimation

---

## 🚀 Quick Start

### **Local Development**

```powershell
# 1. Clone the repository
git clone https://github.com/kamaraj/voicebot.git
cd voicebot

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 9011 --reload
```

**Open**: http://localhost:9011/chat

### **One-Command Start**

```powershell
.\start_local.bat
```

---

## 🔗 URLs

### **Vercel (Production)**

| Page | URL |
|------|-----|
| Main Chat | https://voicebot-kamaraj-v1.vercel.app/chat |
| Voice Chat | https://voicebot-kamaraj-v1.vercel.app/voice |
| Help/Knowledge Base | https://voicebot-kamaraj-v1.vercel.app/help |
| About | https://voicebot-kamaraj-v1.vercel.app/about |
| Documents List | https://voicebot-kamaraj-v1.vercel.app/documents |
| API Docs | https://voicebot-kamaraj-v1.vercel.app/docs |
| Health Check | https://voicebot-kamaraj-v1.vercel.app/health |

### **Local (Development)**

| Page | URL |
|------|-----|
| Main Chat | http://localhost:9011/chat |
| Voice Chat | http://localhost:9011/voice |
| Help/Knowledge Base | http://localhost:9011/help |
| About | http://localhost:9011/about |
| Documents List | http://localhost:9011/documents |
| Upload Documents | http://localhost:9011/static/upload_documents.html |
| FastRTC Voice | http://localhost:9011/fastrtc |
| API Docs | http://localhost:9011/docs |
| Metrics | http://localhost:9011/metrics |

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/conversation` | POST | Chat with the bot |
| `/api/v1/documents/list` | GET | List FAQ documents |
| `/api/v1/documents/stats` | GET | RAG statistics |
| `/api/v1/documents/upload` | POST | Upload documents (local only) |
| `/api/v1/llm/providers` | GET | List LLM providers |
| `/api/v1/llm/current` | GET | Current LLM info |
| `/api/v1/llm/switch` | POST | Switch LLM provider |
| `/api/v1/token-stats` | GET | Token usage stats |
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

### **Example: Chat API**

```bash
curl -X POST https://voicebot-kamaraj-v1.vercel.app/api/v1/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your discipline policy?"}'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        VoiceBot                              │
├─────────────────────────────────────────────────────────────┤
│  Frontend (UI)                                               │
│  ├── Chat Interface (Text + Voice)                          │
│  ├── Help Page (Knowledge Base)                             │
│  └── Document Upload (Local only)                           │
├─────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                         │
│  ├── /api/v1/conversation (Chat)                            │
│  ├── /api/v1/documents/* (RAG)                              │
│  └── /api/v1/llm/* (Provider Management)                    │
├─────────────────────────────────────────────────────────────┤
│  Core Services                                               │
│  ├── FastVoiceAgent (Optimized processing)                  │
│  ├── Semantic Cache (Consistent answers)                    │
│  ├── RAG Retriever (Document search)                        │
│  ├── Guardrails (Safety checks)                             │
│  └── Memory (Conversation context)                          │
├─────────────────────────────────────────────────────────────┤
│  LLM Providers                                               │
│  ├── Ollama (Local)       │  Groq (Cloud - Fast)           │
│  ├── Google Gemini        │  OpenAI                         │
│  └── Auto-detection based on API keys                       │
├─────────────────────────────────────────────────────────────┤
│  Storage                                                     │
│  ├── ChromaDB (Vector DB - Local)                           │
│  ├── JSON Embeddings (Vercel - Lightweight)                 │
│  └── SQLite (Conversation history)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Feature Comparison

| Feature | Local | Vercel |
|---------|-------|--------|
| **Chat UI** | ✅ | ✅ |
| **Voice Chat** | ✅ | ✅ |
| **RAG** | ✅ ChromaDB | ✅ Lightweight |
| **Vector DB** | ✅ ChromaDB | ⚠️ TF-IDF |
| **Document Upload** | ✅ | ❌ |
| **Semantic Cache** | ✅ | ❌ |
| **LLM Switching** | ✅ | ❌ |
| **Full Embeddings** | ✅ | ⚠️ Pre-computed |

---

## 🛠️ Configuration

### **Environment Variables**

```bash
# LLM Providers (set one or more)
GROQ_API_KEY=your_groq_key          # Fast cloud inference
GOOGLE_API_KEY=your_google_key      # Gemini API
OPENAI_API_KEY=your_openai_key      # OpenAI GPT

# Optional
LANGCHAIN_API_KEY=your_langsmith_key  # Tracing
```

### **LLM Provider Priority**

1. **Groq** (if `GROQ_API_KEY` set) - Ultra-fast, recommended
2. **Gemini** (if `GOOGLE_API_KEY` set) - Fast, cheap
3. **OpenAI** (if `OPENAI_API_KEY` set) - Powerful
4. **Ollama** (default) - Local, free

---

## 📁 Project Structure

```
VoiceBot/
├── api/                      # Vercel serverless functions
│   ├── index.py              # Main API handler
│   ├── lightweight_rag.py    # Vercel RAG implementation
│   └── faq_embeddings.json   # Pre-computed embeddings
│
├── src/                      # Core application
│   ├── agents/               # AI agents
│   │   ├── fast_voice_agent.py  # Optimized agent
│   │   └── voice_agent.py    # Standard agent
│   ├── cache/                # Caching
│   │   └── semantic_cache.py # Semantic response cache
│   ├── llm/                  # LLM providers
│   ├── rag/                  # RAG retriever
│   ├── guardrails/           # Safety checks
│   └── api/                  # FastAPI app
│
├── static/                   # Frontend assets
│   ├── index.html            # Chat UI
│   ├── voice_chat.html       # Voice interface
│   └── help.html             # Knowledge base
│
├── docs/                     # Documentation
│   └── childcare_faqs/       # FAQ documents (10 topics)
│
├── scripts/                  # Utility scripts
│   ├── generate_faq_embeddings.py
│   └── test_canonical_responses.py
│
├── data/                     # Data storage
│   ├── chroma/               # Vector DB
│   └── semantic_cache.json   # Cached responses
│
└── vercel.json               # Vercel configuration
```

---

## 📚 FAQ Topics (Knowledge Base)

| Topic | Questions |
|-------|-----------|
| 1. System Usage | How to use the portal, login, etc. |
| 2. Admission | Enrollment, registration, waitlist |
| 3. Fees & Payment | Tuition, payment methods, discounts |
| 4. Timing & Schedule | Hours, holidays, drop-off/pick-up |
| 5. Security | Safety procedures, authorized pick-up |
| 6. Food & Nutrition | Meals, allergies, dietary needs |
| 7. Health & Illness | Sick policy, medications, immunizations |
| 8. Daily Activities | Curriculum, schedule, learning areas |
| 9. Staff | Qualifications, ratios, training |
| 10. Policies | Discipline, behavior, guidelines |

---

## 🧪 Testing

```powershell
# Run all tests
pytest tests/ -v

# Test specific module
pytest tests/unit/test_agent.py -v

# Test canonical responses
python scripts/test_canonical_responses.py
```

---

## 🚢 Deployment

### **Vercel (Recommended)**

```powershell
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### **Docker (Optional)**

```bash
docker build -t voicebot .
docker run -p 9011:9011 voicebot
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| **Response Time (Cached)** | < 1ms |
| **Response Time (RAG + LLM)** | 2-4s |
| **Max Tokens** | 256 (concise) |
| **Temperature** | 0.3 (consistent) |
| **Cache Hit Rate** | ~70% |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **LangChain** - LLM orchestration
- **ChromaDB** - Vector database
- **Groq** - Ultra-fast inference
- **Vercel** - Serverless deployment

---

**Built with ❤️ for AI-powered customer support**
