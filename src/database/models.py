"""
Database Models for Persistent Storage
SQLAlchemy models for conversation history, API keys, and audit logs
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class Conversation(Base):
    """Conversation model for persistent storage"""
    __tablename__ = "conversations"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    user_id = Column(String(100), index=True)
    
    # Metadata
    message_index = Column(Integer, nullable=False)  # Order within conversation
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    duration_ms = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_user_conversations', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Conversation {self.conversation_id}:{self.role}>"


class APIKey(Base):
    """API key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)  # Key description
    user_id = Column(String(100), index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)  # Optional expiration
    revoked_at = Column(DateTime)  # When key was revoked
    
    def __repr__(self):
        return f"<APIKey {self.name}>"


class AuditLog(Base):
    """Audit log for security and compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Request info
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_id = Column(String(100), index=True)
    api_key_id = Column(String(50))
    
    # Client info
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    
    # Response info
    status_code = Column(Integer)
    duration_ms = Column(Float)
    
    # Security events
    event_type = Column(String(50), index=True)  # 'auth_success', 'rate_limit', etc.
    severity = Column(String(20))  # 'info', 'warning', 'error', 'critical'
    details = Column(Text)  # JSON string with additional details
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'created_at'),
        Index('idx_audit_event_time', 'event_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.event_type}:{self.endpoint}>"


class CacheEntry(Base):
    """Optional: Persistent cache (for Redis-less deployments)"""
    __tablename__ = "cache_entries"
    
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)  # JSON serialized
    
    # TTL
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Stats
    hit_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<CacheEntry {self.key}>"
