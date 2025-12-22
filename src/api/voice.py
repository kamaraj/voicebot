"""
Voice API endpoints using OpenAI Whisper
Accurate, reliable, offline speech-to-text
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


class TranscriptionResponse(BaseModel):
    transcript: str
    duration: float
    model: str
    engine: str


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio using OpenAI Whisper.
    
    **ACCURATE & RELIABLE:**
    - Engine: OpenAI Whisper
    - Accuracy: State-of-the-art
    - Offline: No internet required
    - Formats: WAV, MP3, WebM, M4A, etc.
    
    **Usage:**
    ```javascript
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    const response = await fetch('/api/v1/voice/transcribe', {
        method: 'POST',
        body: formData
    });
    
    const data = await response.json();
    console.log('Transcript:', data.transcript);
    ```
    """
    try:
        # Read audio file
        audio_bytes = await audio.read()
        
        logger.info(f"📥 Received audio: {len(audio_bytes)} bytes, type: {audio.content_type}")
        
        # Transcribe using pywhispercpp
        from src.services.voice_processing import transcribe_audio as process_audio
        
        result = process_audio(audio_bytes)
        
        logger.info(f"✅ Transcription complete: {result['transcript'][:100]}...")
        
        return TranscriptionResponse(**result)
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        raise HTTPException(
            status_code=500,
            detail="pywhispercpp not installed. Run: pip install pywhispercpp"
        )
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get("/models")
async def get_available_models():
    """Get information about available voice models."""
    return {
        "stt": {
            "engine": "openai-whisper",
            "description": "OpenAI Whisper - State-of-the-art speech recognition",
            "models": ["tiny", "base", "small", "medium", "large"],
            "current": "base",
            "accuracy": "State-of-the-art",
            "offline": True,
            "formats": ["WAV", "MP3", "WebM", "M4A", "FLAC"]
        },
        "status": "ready"
    }


@router.get("/health")
async def voice_health():
    """Check if voice processing is working."""
    try:
        from src.services.voice_processing import whisper_processor
        
        if whisper_processor.model is None:
            return {
                "status": "error",
                "message": "Whisper.cpp model not loaded",
                "solution": "Run: pip install pywhispercpp"
            }
        
        return {
            "status": "ready",
            "engine": "pywhispercpp",
            "model": whisper_processor.model_name,
            "message": "Voice processing ready!"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
