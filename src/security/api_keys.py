"""
API Key Authentication & Management
Production-grade API key authentication with usage tracking
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import secrets
import hashlib
import structlog

from src.database import get_database_manager, APIKey

logger = structlog.get_logger(__name__)

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """
    API key management and validation.
    
    Features:
    - Secure key generation
    - Hashed storage
    - Usage tracking
    - Rate limit configuration
    - Expiration support
    """
    
    def __init__(self):
        self.db_manager = get_database_manager()
        logger.info("api_key_manager_initialized")
    
    def generate_key(
        self,
        name: str,
        user_id: str,
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 10000,
        expires_in_days: Optional[int] = None
    ) -> str:
        """
        Generate a new API key.
        
        Args:
            name: Key description
            user_id: User identifier
            rate_limit_per_minute: Requests per minute limit
            rate_limit_per_day: Requests per day limit
            expires_in_days: Optional expiration in days
        
        Returns:
            API key string (store this! won't be shown again)
        """
        # Generate secure random key
        raw_key = secrets.token_urlsafe(32)  # 256 bits of entropy
        
        # Hash for storage (don't store raw key!)
        key_hash = self._hash_key(raw_key)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Store in database
        try:
            with self.db_manager.get_session() as session:
                api_key = APIKey(
                    key=key_hash,
                    name=name,
                    user_id=user_id,
                    is_active=True,
                    rate_limit_per_minute=rate_limit_per_minute,
                    rate_limit_per_day=rate_limit_per_day,
                    expires_at=expires_at
                )
                session.add(api_key)
                session.flush()
                
                key_id = api_key.id
                
            logger.info("api_key_created",
                       key_id=key_id,
                       name=name,
                       user_id=user_id)
            
            return raw_key  # Return only once!
            
        except Exception as e:
            logger.error("failed_to_create_api_key", error=str(e))
            raise
    
    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Validate API key and return key object.
        
        Args:
            raw_key: Raw API key from request
        
        Returns:
            APIKey object if valid, None if invalid
        """
        if not raw_key:
            return None
        
        key_hash = self._hash_key(raw_key)
        
        try:
            with self.db_manager.get_session() as session:
                api_key = session.query(APIKey)\
                    .filter(APIKey.key == key_hash)\
                    .first()
                
                if not api_key:
                    logger.warning("invalid_api_key_attempt",
                                 key_preview=raw_key[:8] + "...")
                    return None
                
                # Check if active
                if not api_key.is_active:
                    logger.warning("inactive_api_key_used",
                                 key_id=api_key.id,
                                 name=api_key.name)
                    return None
                
                # Check if expired
                if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
                    logger.warning("expired_api_key_used",
                                 key_id=api_key.id,
                                 name=api_key.name,
                                 expired_at=api_key.expires_at)
                    return None
                
                # Check if revoked
                if api_key.revoked_at:
                    logger.warning("revoked_api_key_used",
                                 key_id=api_key.id,
                                 name=api_key.name)
                    return None
                
                # Update usage
                api_key.total_requests += 1
                api_key.last_used_at = datetime.utcnow()
                session.commit()
                
                logger.debug("api_key_validated",
                           key_id=api_key.id,
                           user_id=api_key.user_id)
                
                return api_key
                
        except Exception as e:
            logger.error("api_key_validation_error", error=str(e))
            return None
    
    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: Key ID to revoke
        
        Returns:
            True if revoked, False if not found
        """
        try:
            with self.db_manager.get_session() as session:
                api_key = session.query(APIKey)\
                    .filter(APIKey.id == key_id)\
                    .first()
                
                if not api_key:
                    return False
                
                api_key.is_active = False
                api_key.revoked_at = datetime.utcnow()
                session.commit()
                
                logger.info("api_key_revoked",
                           key_id=key_id,
                           name=api_key.name)
                
                return True
                
        except Exception as e:
            logger.error("failed_to_revoke_key", error=str(e))
            return False
    
    def list_keys(self, user_id: Optional[str] = None) -> list:
        """List API keys (optionally filtered by user)"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(APIKey)
                
                if user_id:
                    query = query.filter(APIKey.user_id == user_id)
                
                keys = query.all()
                
                return [{
                    'id': k.id,
                    'name': k.name,
                    'user_id': k.user_id,
                    'is_active': k.is_active,
                    'created_at': k.created_at.isoformat(),
                    'last_used_at': k.last_used_at.isoformat() if k.last_used_at else None,
                    'total_requests': k.total_requests,
                    'rate_limit_per_minute': k.rate_limit_per_minute,
                    'expires_at': k.expires_at.isoformat() if k.expires_at else None
                } for k in keys]
                
        except Exception as e:
            logger.error("failed_to_list_keys", error=str(e))
            return []
    
    def _hash_key(self, raw_key: str) -> str:
        """Hash API key for storage (SHA-256)"""
        return hashlib.sha256(raw_key.encode()).hexdigest()


# Global manager instance
_api_key_manager = None

def get_api_key_manager() -> APIKeyManager:
    """Get or create API key manager singleton"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


# FastAPI dependency for authentication
async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> APIKey:
    """
    Verify API key from request header.
    
    Usage:
        @app.get("/protected")
        async def protected_route(
            api_key: APIKey = Depends(verify_api_key)
        ):
            # api_key is validated APIKey object
            ...
    """
    manager = get_api_key_manager()
    
    # Validate key
    validated_key = manager.validate_key(api_key) if api_key else None
    
    if not validated_key:
        logger.warning("authentication_failed",
                      key_provided=bool(api_key))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return validated_key


# Optional: Dependency for optional authentication
async def optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[APIKey]:
    """
    Optional API key validation (doesn't require auth).
    
    Usage:
        @app.get("/optional-auth")
        async def route(
            api_key: Optional[APIKey] = Depends(optional_api_key)
        ):
            if api_key:
                # Authenticated user
                ...
            else:
                # Anonymous user
                ...
    """
    if not api_key:
        return None
    
    manager = get_api_key_manager()
    return manager.validate_key(api_key)
