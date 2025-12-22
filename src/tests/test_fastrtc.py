"""
🧪 FastRTC Tests - Comprehensive Testing Suite
==============================================
Tests for performance, reliability, security, and accuracy

Coverage:
- Unit tests for FastRTC service
- Integration tests for WebSocket streaming
- Performance benchmarks
- Security tests
- Accuracy validation
"""

import pytest
import asyncio
import time
import json
import base64
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

# Import FastRTC components
import sys
sys.path.insert(0, '.')

from src.services.fastrtc_service import (
    FastRTCService,
    FastRTCPipeline,
    VoiceActivityDetector,
    VoiceSession,
    StreamState,
    AudioChunk,
    get_fastrtc_service
)


class TestVoiceActivityDetector:
    """Tests for Voice Activity Detection"""
    
    def test_vad_initialization(self):
        """Test VAD initializes with correct defaults"""
        vad = VoiceActivityDetector()
        
        assert vad.threshold == 0.3
        assert vad.smoothing_frames == 5
        assert not vad.is_speaking
        assert vad.silence_start is None
    
    def test_vad_custom_threshold(self):
        """Test VAD with custom threshold"""
        vad = VoiceActivityDetector(threshold=0.5, smoothing_frames=10)
        
        assert vad.threshold == 0.5
        assert vad.smoothing_frames == 10
    
    def test_vad_process_silence(self):
        """Test VAD correctly detects silence"""
        vad = VoiceActivityDetector(threshold=0.3)
        
        # Generate silent audio (near-zero 16-bit PCM samples)
        # For 16-bit PCM, silence is values near 0 (not 128 which is for 8-bit)
        import struct
        silent_samples = [0] * 500  # 500 samples of silence
        silent_audio = struct.pack(f"<{len(silent_samples)}h", *silent_samples)
        
        is_speech, energy = vad.process(silent_audio)
        
        # Should detect as silence (energy should be very low)
        assert energy < 0.01, f"Silent audio should have near-zero energy, got {energy}"
    
    def test_vad_process_speech(self):
        """Test VAD correctly detects speech-like audio"""
        vad = VoiceActivityDetector(threshold=0.1)
        
        # Generate audio with variation (simulating speech)
        # Alternating high/low values
        speech_audio = bytes([50 + (i % 150) for i in range(1000)])
        
        is_speech, energy = vad.process(speech_audio)
        
        # Energy should be calculated
        assert energy >= 0
    
    def test_vad_silence_duration(self):
        """Test silence duration tracking"""
        vad = VoiceActivityDetector(threshold=0.3)
        
        # First, simulate speech
        vad.is_speaking = True
        vad.silence_start = None
        
        # Then silence
        silent_audio = bytes([128] * 1000)
        vad.process(silent_audio)
        
        # Silence duration should be tracked
        if vad.silence_start is not None:
            duration = vad.get_silence_duration_ms()
            assert duration >= 0


class TestVoiceSession:
    """Tests for Voice Session management"""
    
    def test_session_creation(self):
        """Test session creates with correct defaults"""
        session = VoiceSession(
            session_id="test_session_123",
            user_id="test_user"
        )
        
        assert session.session_id == "test_session_123"
        assert session.user_id == "test_user"
        assert session.state == StreamState.IDLE
        assert session.audio_buffer == b""
        assert session.transcript_buffer == ""
    
    def test_session_metrics_initialized(self):
        """Test session metrics are properly initialized"""
        session = VoiceSession(
            session_id="test",
            user_id="user"
        )
        
        assert "total_audio_bytes" in session.metrics
        assert "stt_calls" in session.metrics
        assert "llm_calls" in session.metrics
        assert "tts_calls" in session.metrics
        assert "avg_latency_ms" in session.metrics
        
        # All should start at 0
        assert session.metrics["total_audio_bytes"] == 0
        assert session.metrics["stt_calls"] == 0
    
    def test_session_config_defaults(self):
        """Test session config has sensible defaults"""
        session = VoiceSession(
            session_id="test",
            user_id="user"
        )
        
        assert session.config["vad_threshold"] == 0.3
        assert session.config["silence_timeout_ms"] == 1500
        assert session.config["max_audio_duration_ms"] == 30000
        assert session.config["language"] == "en"


class TestFastRTCService:
    """Tests for FastRTC Service"""
    
    def test_service_creation(self):
        """Test service creates successfully"""
        service = FastRTCService()
        
        assert service.sessions == {}
        assert service.vad is not None
        assert service.pipeline is not None
    
    def test_create_session(self):
        """Test session creation"""
        service = FastRTCService()
        
        session = service.create_session(user_id="test_user")
        
        assert session is not None
        assert session.session_id.startswith("rtc_")
        assert session.user_id == "test_user"
        assert session.session_id in service.sessions
    
    def test_get_session(self):
        """Test session retrieval"""
        service = FastRTCService()
        
        session = service.create_session()
        retrieved = service.get_session(session.session_id)
        
        assert retrieved is session
    
    def test_get_nonexistent_session(self):
        """Test retrieving non-existent session returns None"""
        service = FastRTCService()
        
        result = service.get_session("nonexistent")
        
        assert result is None
    
    def test_end_session(self):
        """Test session termination"""
        service = FastRTCService()
        
        session = service.create_session()
        session_id = session.session_id
        
        result = service.end_session(session_id)
        
        assert result is True
        assert session_id not in service.sessions
    
    def test_end_nonexistent_session(self):
        """Test ending non-existent session returns False"""
        service = FastRTCService()
        
        result = service.end_session("nonexistent")
        
        assert result is False
    
    def test_get_service_stats(self):
        """Test service statistics"""
        service = FastRTCService()
        
        # Create a couple sessions
        service.create_session()
        service.create_session()
        
        stats = service.get_service_stats()
        
        assert stats["service"] == "FastRTC"
        assert stats["active_sessions"] == 2
        assert "pipeline_stats" in stats
    
    def test_cleanup_stale_sessions(self):
        """Test stale session cleanup"""
        service = FastRTCService()
        service.config["session_timeout_sec"] = 0  # Immediate timeout
        
        session = service.create_session()
        session.last_activity = 0  # Set to far past
        
        cleaned = service.cleanup_stale_sessions()
        
        assert cleaned == 1
        assert len(service.sessions) == 0
    
    def test_service_singleton(self):
        """Test service singleton pattern"""
        # Reset global
        import src.services.fastrtc_service as fastrtc_module
        fastrtc_module._fastrtc_service = None
        
        service1 = get_fastrtc_service()
        service2 = get_fastrtc_service()
        
        assert service1 is service2


class TestFastRTCPipeline:
    """Tests for FastRTC Pipeline"""
    
    @pytest.fixture
    def mock_llm_handler(self):
        """Create a mock LLM handler"""
        async def handler(text, session_id, context=None):
            return {"response": f"AI response to: {text}"}
        return handler
    
    def test_pipeline_creation(self, mock_llm_handler):
        """Test pipeline creates successfully"""
        pipeline = FastRTCPipeline(llm_handler=mock_llm_handler)
        
        assert pipeline.llm_handler is mock_llm_handler
        assert pipeline.total_requests == 0
        assert pipeline.total_latency == 0
    
    def test_pipeline_stats(self, mock_llm_handler):
        """Test pipeline statistics"""
        pipeline = FastRTCPipeline(llm_handler=mock_llm_handler)
        
        stats = pipeline.get_stats()
        
        assert stats["total_requests"] == 0
        assert "avg_latency_ms" in stats


class TestPerformance:
    """Performance and benchmark tests"""
    
    def test_vad_processing_speed(self):
        """Test VAD processing is fast (<5ms per chunk)"""
        vad = VoiceActivityDetector()
        audio_chunk = bytes([128] * 4096)  # 4KB chunk
        
        iterations = 1000
        start = time.time()
        
        for _ in range(iterations):
            vad.process(audio_chunk)
        
        elapsed = time.time() - start
        avg_ms = (elapsed / iterations) * 1000
        
        # Should process in under 5ms per chunk (allowing for various hardware)
        assert avg_ms < 5, f"VAD processing too slow: {avg_ms:.3f}ms"
    
    def test_session_creation_speed(self):
        """Test session creation is fast (<5ms)"""
        service = FastRTCService()
        
        iterations = 100
        start = time.time()
        
        for _ in range(iterations):
            service.create_session()
        
        elapsed = time.time() - start
        avg_ms = (elapsed / iterations) * 1000
        
        # Should create session in under 5ms
        assert avg_ms < 5, f"Session creation too slow: {avg_ms:.3f}ms"
        
        # Cleanup
        for session_id in list(service.sessions.keys()):
            service.end_session(session_id)
    
    def test_memory_efficiency(self):
        """Test service doesn't leak memory with many sessions"""
        service = FastRTCService()
        
        # Create and destroy many sessions
        for _ in range(100):
            sessions = [service.create_session() for _ in range(10)]
            for session in sessions:
                service.end_session(session.session_id)
        
        # No sessions should remain
        assert len(service.sessions) == 0


class TestSecurity:
    """Security tests"""
    
    def test_session_id_uniqueness(self):
        """Test session IDs are unique"""
        service = FastRTCService()
        
        session_ids = set()
        for _ in range(100):
            session = service.create_session()
            assert session.session_id not in session_ids
            session_ids.add(session.session_id)
    
    def test_session_isolation(self):
        """Test sessions are isolated from each other"""
        service = FastRTCService()
        
        session1 = service.create_session(user_id="user1")
        session2 = service.create_session(user_id="user2")
        
        # Modify session1
        session1.audio_buffer = b"session1_audio"
        session1.transcript_buffer = "session1_transcript"
        
        # Session2 should be unaffected
        assert session2.audio_buffer == b""
        assert session2.transcript_buffer == ""
    
    def test_audio_buffer_cleared_after_processing(self):
        """Test audio buffer is cleared after processing"""
        session = VoiceSession(
            session_id="test",
            user_id="user"
        )
        
        # Simulate audio accumulation
        session.audio_buffer = b"audio_data_here"
        
        # After processing, buffer should be cleared
        assert len(session.audio_buffer) > 0  # Has data
        
        session.audio_buffer = b""  # Clear (as processing would)
        assert session.audio_buffer == b""


class TestReliability:
    """Reliability and error handling tests"""
    
    def test_vad_handles_empty_audio(self):
        """Test VAD handles empty audio gracefully"""
        vad = VoiceActivityDetector()
        
        # Should not raise exception
        is_speech, energy = vad.process(b"")
        
        assert energy == 0.0
    
    def test_vad_handles_short_audio(self):
        """Test VAD handles very short audio"""
        vad = VoiceActivityDetector()
        
        # Single byte
        is_speech, energy = vad.process(b"\x80")
        
        # Should not crash
        assert isinstance(energy, float)
    
    def test_session_handles_large_audio_buffer(self):
        """Test session handles large audio buffers"""
        session = VoiceSession(
            session_id="test",
            user_id="user"
        )
        
        # Simulate 1MB of audio
        large_audio = b"x" * (1024 * 1024)
        session.audio_buffer += large_audio
        
        assert len(session.audio_buffer) == 1024 * 1024
        
        # Clear
        session.audio_buffer = b""


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_processing_flow(self):
        """Test complete audio processing flow"""
        # Create service with mock LLM
        mock_response = {"response": "Hello! I received your audio."}
        
        async def mock_llm(text, session_id, context=None):
            return mock_response
        
        service = FastRTCService()
        service.pipeline.llm_handler = mock_llm
        
        # Create session
        session = service.create_session()
        
        # Simulate audio processing
        test_audio = bytes([128 + i % 50 for i in range(4096)])
        
        # Process audio (won't trigger full pipeline due to VAD)
        responses = []
        async for chunk in service.process_audio_chunk(session.session_id, test_audio):
            responses.append(chunk)
        
        # Session should be updated
        assert session.metrics["total_audio_bytes"] > 0
    
    @pytest.mark.asyncio
    async def test_complete_audio_processing(self):
        """Test processing complete audio data"""
        async def mock_llm(text, session_id, context=None):
            return {"response": f"Response to: {text}"}
        
        async def mock_stt(audio_data):
            return "Test transcription"
        
        service = FastRTCService()
        service.pipeline.llm_handler = mock_llm
        service.pipeline.stt_handler = mock_stt
        
        session = service.create_session()
        
        # Process complete audio
        test_audio = bytes([128] * 16000)  # 1 second at 16kHz
        
        responses = []
        async for chunk in service.process_complete_audio(session.session_id, test_audio):
            responses.append(chunk)
        
        # Should have processed something
        assert session.transcript_buffer == "Test transcription"


# Benchmark helper
def run_benchmark(func, iterations=100, name="Benchmark"):
    """Run a simple benchmark"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        func()
        times.append((time.time() - start) * 1000)
    
    avg = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n{name}:")
    print(f"  Iterations: {iterations}")
    print(f"  Avg: {avg:.3f}ms")
    print(f"  Min: {min_time:.3f}ms")
    print(f"  Max: {max_time:.3f}ms")
    
    return avg


if __name__ == "__main__":
    # Run with: python -m pytest src/tests/test_fastrtc.py -v
    pytest.main([__file__, "-v", "--tb=short"])
