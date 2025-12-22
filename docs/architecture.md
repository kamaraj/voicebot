# System Architecture

## Overview

The VoiceBot Agentic AI Platform is a production-ready voice AI system built with industry best practices for observability, safety, and reliability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  Phone (Twilio) │ Web (WebRTC) │ Mobile App                     │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (FastAPI)                      │
│  • Authentication  • Rate Limiting  • Request Routing           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     VOICE PROCESSING LAYER                      │
│  ┌──────────────┐           ┌──────────────┐                   │
│  │  STT Engine  │  ◄────►   │  TTS Engine  │                   │
│  │  (Deepgram)  │           │ (ElevenLabs) │                   │
│  └──────────────┘           └──────────────┘                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GUARDRAILS LAYER                           │
│  ┌───────────┐  ┌──────────┐  ┌─────────────┐                 │
│  │    PII    │  │ Toxicity │  │   Prompt    │                 │
│  │ Detection │  │ Filtering│  │  Injection  │                 │
│  └───────────┘  └──────────┘  └─────────────┘                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC AI ENGINE                           │
│  ┌─────────────────────────────────────────────────┐            │
│  │              LangGraph Workflow                 │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │            │
│  │  │ Intent   │→ │ Planning │→ │ Tool Calling │ │            │
│  │  │ Analysis │  │ & Action │  │ & Response   │ │            │
│  │  └──────────┘  └──────────┘  └──────────────┘ │            │
│  └─────────────────────────────────────────────────┘            │
│  ┌─────────────────┐                                            │
│  │ Llama 3.1 8B    │  (Local via Ollama)                        │
│  │ LLM Engine      │                                            │
│  └─────────────────┘                                            │
└────────────┬────────────────────────────────────────────────────┘
             │
      ┌──────┴──────┬───────────────┬───────────────┐
      ▼             ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────┐
│ Calendar │  │ Knowledge│  │   CRM       │  │ External │
│   API    │  │   Base   │  │Integration  │  │   APIs   │
│  (Tools) │  │  (RAG)   │  │   (Tools)   │  │ (Weather)│
└──────────┘  └──────────┘  └─────────────┘  └──────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                          │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  Tracing   │  │  Metrics │  │  Logging │  │     KPI     │  │
│  │ (LangSmith)│  │(Prometheus)│ │(Structlog)│ │  Dashboard  │  │
│  └────────────┘  └──────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌────────────┐           ┌──────────┐                          │
│  │ PostgreSQL │           │  Redis   │                          │
│  │ (Persistent)│          │  (Cache) │                          │
│  └────────────┘           └──────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### 1. API Gateway
- **Technology**: FastAPI
- **Responsibilities**: 
  - Request routing
  - Authentication & authorization
  - Rate limiting
  - Request/response logging
  - CORS handling

### 2. Voice Processing
- **STT (Speech-to-Text)**: Deepgram for real-time transcription
- **TTS (Text-to-Speech)**: ElevenLabs for natural voice synthesis
- **Audio Pipeline**: Pipecat for bidirectional audio streaming

### 3. Guardrails
- **PII Detection**: Microsoft Presidio for detecting/redacting sensitive info
- **Toxicity Filtering**: Pattern-based and ML-based content filtering
- **Prompt Injection Prevention**: Security against jailbreak attempts
- **Content Length Limits**: Enforced input/output constraints

### 4. Agentic AI Engine
- **LLM**: Llama 3.1 8B (local via Ollama)
- **Orchestration**: LangGraph for multi-step workflows
- **Capabilities**:
  - Intent recognition
  - Multi-step reasoning
  - Tool/function calling
  - Context management
  - RAG for knowledge retrieval

### 5. Tools & Integrations
- **Internal Tools**: Time, scheduling, search
- **External APIs**: Weather, CRM, Calendar
- **RAG**: Vector database for knowledge base

### 6. Observability
- **Tracing**: LangSmith for distributed tracing
- **Metrics**: Prometheus for time-series metrics
- **Logging**: Structlog for structured JSON logs
- **Dashboards**: Grafana for visualization
- **KPIs**: Custom dashboard for business metrics

### 7. Data Layer
- **PostgreSQL**: Conversations, users, analytics
- **Redis**: Session caching, rate limiting

## Key Design Decisions

### 1. Local LLM (Llama 3.1 8B)
**Why**: 
- Cost savings (no API fees)
- Data privacy (on-premise)
- Low latency
- Full control

**Trade-offs**:
- Requires GPU/hardware
- Smaller context window than GPT-4
- Less capable than larger models

### 2. LangGraph for Orchestration
**Why**:
- Explicit workflow definition
- Debuggable state machines
- Tool calling support
- Memory management

### 3. Comprehensive Guardrails
**Why**:
- GDPR/privacy compliance
- Safety & toxicity prevention
- Security against attacks
- Trust & reliability

### 4. Multi-layer Observability
**Why**:
- Production debugging
- Performance optimization
- Quality monitoring
- Cost tracking
- Business insights

## Data Flow

### Conversation Request Flow

```
1. User speaks → Phone/Web client
2. Audio → STT (Deepgram) → Text
3. Text → Input Guardrails
4. Text (sanitized) → Agentic AI Engine
   4a. Intent Recognition
   4b. Planning & Action Selection
   4c. Tool Execution (if needed)
   4d. Response Generation
5. Response → Output Guardrails
6. Response (validated) → TTS (ElevenLabs)
7. Audio → Client

Throughout:
- Tracing captures each step
- Metrics recorded
- Logs generated
- KPIs updated
```

## Scalability Considerations

### Horizontal Scaling
- API servers: Load balanced, stateless
- Database: Read replicas
- Redis: Cluster mode

### Vertical Scaling
- LLM: GPU acceleration
- Batch processing: Queue-based

### Caching Strategy
- Redis for session data
- HTTP caching for static content
- LLM response caching for common queries

## Security

### Authentication
- JWT tokens
- API keys
- OAuth 2.0 support

### Authorization
- Role-based access control (RBAC)
- Rate limiting per user/org

### Data Protection
- Encryption at rest (database)
- Encryption in transit (TLS)
- PII redaction
- Audit logging

## Monitoring & Alerts

### Health Checks
- `/health` endpoint
- Component status
- Dependency checks

### Alerts
- Latency > threshold
- Error rate > threshold
- Guardrail violations
- Cost anomalies

### Dashboards
- Real-time metrics (Grafana)
- Business KPIs
- System health
- Cost tracking
