"""
Voice Processing with OpenAI Whisper - ACCURATE & RELIABLE
"""

import io
import wave
import logging
import tempfile
from pathlib import Path
from typing import Optional
import time

logger = logging.getLogger(__name__)


class WhisperProcessor:
    """Speech-to-text using OpenAI Whisper."""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper model.
        
        Args:
            model_name: Model size - tiny, base, small, medium, large
                       base = best balance of speed & accuracy
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            import whisper
            
            logger.info(f"📥 Loading Whisper model: {self.model_name}")
            
            # Model will auto-download on first use
            self.model = whisper.load_model(self.model_name)
            
            logger.info(f"✅ Whisper model loaded: {self.model_name}")
            
        except ImportError:
            logger.error("❌ whisper not installed. Run: pip install openai-whisper")
            self.model = None
        except Exception as e:
            logger.error(f"❌ Error loading Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_bytes: Audio file bytes (WAV, MP3, WebM, etc.)
        
        Returns:
            Transcribed text
        """
        if self.model is None:
            return "Error: Whisper model not loaded"
        
        try:
            start_time = time.time()
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name
            
            logger.info(f"🎤 Transcribing audio: {len(audio_bytes)} bytes")
            
            # Transcribe using Whisper
            result = self.model.transcribe(tmp_path, fp16=False)
            
            # Extract text
            transcript = result.get("text", "").strip()
            
            # Cleanup
            Path(tmp_path).unlink(missing_ok=True)
            
            duration = time.time() - start_time
            logger.info(f"✅ Transcribed in {duration:.2f}s: {transcript[:100]}...")
            
            return transcript
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return f"Error: {str(e)}"


# Global instance
whisper_processor = WhisperProcessor(model_name="base")


def transcribe_audio(audio_bytes: bytes) -> dict:
    """
    Transcribe audio using Whisper.
    
    Args:
        audio_bytes: Audio file bytes
    
    Returns:
        Dictionary with transcript and metadata
    """
    start_time = time.time()
    
    transcript = whisper_processor.transcribe(audio_bytes)
    duration = time.time() - start_time
    
    return {
        "transcript": transcript,
        "duration": duration,
        "model": whisper_processor.model_name,
        "engine": "openai-whisper"
    }
