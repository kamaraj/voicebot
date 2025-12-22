# 🎙️ Voice Chat Integration Guide

## Open-Source Tools (Pipecat Compatible)

This guide shows how to integrate the voice chat interface with open-source tools compatible with Pipecat.

---

## 🔊 Pipeline Flow

```
Audio Input → STT → RAG → LLM → TTS → Audio Output
    🎤      →  📝  →  📚 →  🤖 → 🔊 →     🔈
```

---

## 1. 🎤 Speech-to-Text (STT)

### **Option A: Whisper (Local - Recommended)**

```bash
# Install Whisper
pip install openai-whisper

# Or faster-whisper (recommended)
pip install faster-whisper
```

**Python Code:**
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(audio_file):
    segments, info = model.transcribe(audio_file, beam_size=5)
    text = " ".join([segment.text for segment in segments])
    return text
```

### **Option B: Vosk (Offline)**

```bash
pip install vosk
```

### **Option C: Deepgram (Cloud - Pipecat Default)**

```bash
pip install deepgram-sdk
```

---

## 2. 📚 RAG (Retrieval Augmented Generation)

### **Local Vector Database**

```bash
# Install FAISS for vector search
pip install faiss-cpu sentence-transformers
```

**Python Code:**
```python
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create vector database
def create_vector_db(documents):
    embeddings = model.encode(documents)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

# Search
def search_similar(query, index, documents, k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, k)
    return [documents[i] for i in indices[0]]
```

---

## 3. 🤖 LLM (Already Configured)

You're already using **Llama 3.1 8B via Ollama** - perfect for Pipecat!

---

## 4. 🔊 Text-to-Speech (TTS)

### **Option A: Piper TTS (Local - Recommended)**

```bash
pip install piper-tts
```

**Usage:**
```python
from piper import PiperVoice

voice = PiperVoice.load("en_US-lessac-medium")

def speak(text):
    audio = voice.synthesize(text)
    # Play audio
    return audio
```

### **Option B: Coqui TTS**

```bash
pip install TTS
```

**Usage:**
```python
from TTS.api import TTS

tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")

def speak(text, output_path="output.wav"):
    tts.tts_to_file(text=text, file_path=output_path)
```

### **Option C: Bark (High Quality)**

```bash
pip install bark
```

---

## 🚀 Complete Integration Example

### **API Endpoint for Voice Pipeline**

Add this to `src/api/main.py`:

```python
from fastapi import File, UploadFile
import tempfile

@app.post("/api/v1/voice/process")
async def process_voice(audio: UploadFile = File(...)):
    """Complete voice processing pipeline."""
    
    # 1. Save uploaded audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    # 2. STT: Audio → Text
    transcript = transcribe_audio(tmp_path)
    
    # 3. RAG: Retrieve relevant context
    context = search_similar(transcript, vector_index, knowledge_base)
    
    # 4. LLM: Generate response
    response = await agent.process_message(
        user_message=transcript,
        context={"rag_context": context}
    )
    
    # 5. TTS: Text → Audio
    audio_response = text_to_speech(response["response"])
    
    return {
        "transcript": transcript,
        "response": response["response"],
        "audio_url": "/path/to/audio.wav",
        "context_used": context
    }
```

---

## 📦 Updated Requirements

Add to `requirements.txt`:

```
# Voice Processing (Pipecat Compatible)
faster-whisper==0.10.0
piper-tts==1.2.0
TTS==0.22.0

# RAG
faiss-cpu==1.7.4
sentence-transformers==2.2.2

# Audio Processing
pydub==0.25.1
soundfile==0.12.1
```

---

## 🎛️ Frontend Integration

The voice chat page (`/voice`) already includes:

✅ **Microphone access**  
✅ **3-second silence detection**  
✅ **10-second progress bar**  
✅ **Pipeline visualization** (STT → RAG → LLM → TTS)  
✅ **Audio playback**  
✅ **Transcript display**  

---

## 🔧 Quick Setup

### 1. Install Voice Dependencies

```powershell
cd c:\kamaraj\Prototype\VoiceBot
venv\Scripts\activate
pip install faster-whisper piper-tts faiss-cpu sentence-transformers pydub
```

### 2. Test Voice Interface

Visit: **http://localhost:9011/voice**

---

## 🎯 Pipecat Architecture

This matches the Pipecat framework architecture:

```
┌─────────────────────────────────────────────┐
│  Browser (WebRTC/MediaRecorder)             │
│  ↓                                           │
│  Voice Input (3s silence detection)         │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  Backend Pipeline                           │
│                                              │
│  1. STT (Whisper) → Text                    │
│  2. RAG (FAISS) → Context                   │
│  3. LLM (Llama) → Response                  │
│  4. TTS (Piper) → Audio                     │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│  Browser (Audio Playback)                   │
└─────────────────────────────────────────────┘
```

---

## 📝 Notes

- **STT**: Uses browser's built-in for demo, replace with Whisper
- **TTS**: Uses browser's built-in for demo, replace with Piper/Coqui
- **RAG**: Ready to integrate - just add your knowledge base
- **LLM**: Already working with Llama 3.1 8B!

---

## 🎊 Features Implemented

✅ Single-page full-width layout  
✅ Voice recording with waveform visualization  
✅ 3-second silence auto-submit  
✅ 10-second progress bar  
✅ Pipeline status indicators (STT → RAG → LLM → TTS)  
✅ Transcript display  
✅ Error handling  
✅ Responsive design  
✅ Pipecat-compatible architecture  

**Ready to integrate real STT/TTS!** 🚀
