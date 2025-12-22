"""
🔌 FastRTC WebSocket Handler
============================
Real-time bidirectional audio streaming over WebSocket
Enables <2 second voice-to-voice AI responses

Features:
- WebSocket streaming (low latency)
- Binary audio transfer
- JSON control messages
- Session management
- Auto-reconnection support
- Health monitoring
"""

import asyncio
import json
import logging
import time
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from starlette.websockets import WebSocketState
import base64

from src.services.fastrtc_service import (
    get_fastrtc_service, 
    FastRTCService,
    VoiceSession,
    StreamState
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rtc", tags=["fastrtc"])


class WebSocketManager:
    """Manages WebSocket connections for FastRTC"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_sessions: Dict[str, str] = {}  # ws_id -> session_id
        
    async def connect(self, websocket: WebSocket, client_id: str) -> str:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"🔌 WebSocket connected: {client_id}")
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.connection_sessions:
            session_id = self.connection_sessions.pop(client_id)
            logger.info(f"🔌 WebSocket disconnected: {client_id} (session: {session_id})")
        else:
            logger.info(f"🔌 WebSocket disconnected: {client_id}")
    
    async def send_json(self, client_id: str, data: dict):
        """Send JSON message to client"""
        if client_id in self.active_connections:
            ws = self.active_connections[client_id]
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_json(data)
    
    async def send_bytes(self, client_id: str, data: bytes):
        """Send binary data to client"""
        if client_id in self.active_connections:
            ws = self.active_connections[client_id]
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_bytes(data)
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON to all connected clients"""
        for client_id in list(self.active_connections.keys()):
            await self.send_json(client_id, data)


# Global WebSocket manager
ws_manager = WebSocketManager()


@router.websocket("/stream")
async def websocket_voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming
    
    Protocol:
    - Client sends: Binary audio chunks or JSON control messages
    - Server sends: Binary audio responses or JSON status updates
    
    Control Messages:
    - {"type": "start_session", "user_id": "..."}
    - {"type": "end_session"}
    - {"type": "config", "vad_threshold": 0.3, ...}
    
    Status Messages:
    - {"type": "session_started", "session_id": "..."}
    - {"type": "state_change", "state": "listening|processing|speaking"}
    - {"type": "transcript", "text": "..."}
    - {"type": "response", "text": "..."}
    - {"type": "error", "message": "..."}
    """
    client_id = f"ws_{int(time.time()*1000)}"
    session: Optional[VoiceSession] = None
    fastrtc: FastRTCService = get_fastrtc_service()
    
    try:
        await ws_manager.connect(websocket, client_id)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "message": "FastRTC WebSocket connected. Send 'start_session' to begin."
        })
        
        while True:
            # Receive message (can be text or binary)
            message = await websocket.receive()
            
            if "text" in message:
                # JSON control message
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type", "")
                    
                    if msg_type == "start_session":
                        # Create new voice session
                        user_id = data.get("user_id", "anonymous")
                        session = fastrtc.create_session(user_id)
                        ws_manager.connection_sessions[client_id] = session.session_id
                        
                        await websocket.send_json({
                            "type": "session_started",
                            "session_id": session.session_id,
                            "config": session.config
                        })
                        
                    elif msg_type == "end_session":
                        if session:
                            stats = session.metrics
                            fastrtc.end_session(session.session_id)
                            
                            await websocket.send_json({
                                "type": "session_ended",
                                "stats": stats
                            })
                            session = None
                            
                    elif msg_type == "config":
                        if session:
                            # Update session config
                            for key, value in data.items():
                                if key in session.config:
                                    session.config[key] = value
                                    
                            await websocket.send_json({
                                "type": "config_updated",
                                "config": session.config
                            })
                            
                    elif msg_type == "audio_base64":
                        # Handle base64 encoded audio (for browsers that don't support binary)
                        if session and "data" in data:
                            audio_bytes = base64.b64decode(data["data"])
                            await _process_audio(
                                websocket, 
                                fastrtc, 
                                session, 
                                audio_bytes
                            )
                            
                    elif msg_type == "ping":
                        await websocket.send_json({"type": "pong", "time": time.time()})
                        
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON message"
                    })
                    
            elif "bytes" in message:
                # Binary audio data
                if session:
                    await _process_audio(
                        websocket,
                        fastrtc,
                        session,
                        message["bytes"]
                    )
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No active session. Send 'start_session' first."
                    })
                    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        # Cleanup
        if session:
            fastrtc.end_session(session.session_id)
        ws_manager.disconnect(client_id)


async def _process_audio(
    websocket: WebSocket,
    fastrtc: FastRTCService,
    session: VoiceSession,
    audio_bytes: bytes
):
    """Process incoming audio and stream response"""
    try:
        # Notify state change
        if session.state != StreamState.LISTENING:
            await websocket.send_json({
                "type": "state_change",
                "state": "listening"
            })
        
        # Process audio chunk and get response stream
        async for response_chunk in fastrtc.process_audio_chunk(
            session.session_id,
            audio_bytes
        ):
            # Check if this is the start of speech
            if session.state == StreamState.PROCESSING:
                await websocket.send_json({
                    "type": "state_change",
                    "state": "processing"
                })
                
                # Send transcript if available
                if session.transcript_buffer:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": session.transcript_buffer
                    })
            
            if session.state == StreamState.SPEAKING:
                await websocket.send_json({
                    "type": "state_change",
                    "state": "speaking"
                })
            
            # Send audio response
            await websocket.send_bytes(response_chunk)
        
        # Back to idle
        if session.state != StreamState.LISTENING:
            await websocket.send_json({
                "type": "state_change",
                "state": "idle"
            })
            
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


@router.websocket("/stream/full")
async def websocket_full_audio(websocket: WebSocket):
    """
    WebSocket endpoint for full audio processing
    Client sends complete audio recording, server responds with complete audio
    Simpler protocol for non-streaming use cases
    """
    client_id = f"ws_full_{int(time.time()*1000)}"
    fastrtc: FastRTCService = get_fastrtc_service()
    
    try:
        await ws_manager.connect(websocket, client_id)
        session = fastrtc.create_session()
        
        await websocket.send_json({
            "type": "ready",
            "session_id": session.session_id,
            "message": "Send audio data to process"
        })
        
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                audio_bytes = message["bytes"]
                
                # Acknowledge receipt
                await websocket.send_json({
                    "type": "processing",
                    "audio_size": len(audio_bytes)
                })
                
                # Process and collect all response audio
                response_chunks = []
                async for chunk in fastrtc.process_complete_audio(
                    session.session_id,
                    audio_bytes
                ):
                    response_chunks.append(chunk)
                
                # Send complete response
                if response_chunks:
                    full_response = b"".join(response_chunks)
                    
                    await websocket.send_json({
                        "type": "response_ready",
                        "transcript": session.transcript_buffer,
                        "audio_size": len(full_response),
                        "metrics": session.metrics
                    })
                    
                    await websocket.send_bytes(full_response)
                    
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "end":
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    finally:
        ws_manager.disconnect(client_id)


# REST API endpoints for FastRTC

@router.post("/session")
async def create_session(user_id: str = "anonymous"):
    """Create a new FastRTC session via REST API"""
    fastrtc = get_fastrtc_service()
    session = fastrtc.create_session(user_id)
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "config": session.config,
        "websocket_url": f"/api/v1/rtc/stream"
    }


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a FastRTC session"""
    fastrtc = get_fastrtc_service()
    
    session = fastrtc.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    
    stats = session.metrics
    fastrtc.end_session(session_id)
    
    return {
        "message": "Session ended",
        "session_id": session_id,
        "stats": stats
    }


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    fastrtc = get_fastrtc_service()
    session = fastrtc.get_session(session_id)
    
    if not session:
        return {"error": "Session not found"}
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "state": session.state.value,
        "config": session.config,
        "metrics": session.metrics,
        "duration_sec": time.time() - session.created_at
    }


@router.get("/stats")
async def get_fastrtc_stats():
    """Get FastRTC service statistics"""
    fastrtc = get_fastrtc_service()
    return fastrtc.get_service_stats()


@router.get("/health")
async def fastrtc_health():
    """FastRTC health check"""
    fastrtc = get_fastrtc_service()
    
    return {
        "status": "healthy",
        "service": "FastRTC",
        "active_sessions": len(fastrtc.sessions),
        "websocket_connections": len(ws_manager.active_connections),
        "uptime": "running"
    }


@router.post("/process")
async def process_audio_http(
    audio_base64: str,
    session_id: Optional[str] = None
):
    """
    Process audio via HTTP (non-WebSocket fallback)
    Accepts base64 encoded audio, returns text response
    """
    fastrtc = get_fastrtc_service()
    
    try:
        # Decode audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Get or create session
        if session_id:
            session = fastrtc.get_session(session_id)
        else:
            session = fastrtc.create_session()
        
        if not session:
            session = fastrtc.create_session()
        
        # Process audio (collect all response chunks)
        response_chunks = []
        async for chunk in fastrtc.process_complete_audio(
            session.session_id,
            audio_bytes
        ):
            response_chunks.append(chunk)
        
        # Return response
        response_audio = b"".join(response_chunks) if response_chunks else b""
        
        return {
            "session_id": session.session_id,
            "transcript": session.transcript_buffer,
            "audio_response_base64": base64.b64encode(response_audio).decode() if response_audio else None,
            "metrics": session.metrics
        }
        
    except Exception as e:
        logger.error(f"HTTP process error: {e}")
        return {"error": str(e)}
