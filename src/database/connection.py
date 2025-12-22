"""
Database Connection and Session Management
Thread-safe SQLAlchemy connection with connection pooling
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool
from contextlib import contextmanager
from typing import Generator
import structlog
from pathlib import Path

from src.config.settings import settings
from src.database.models import Base

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Thread-safe database manager with connection pooling.
    
    Features:
    - Connection pooling for performance
    - Automatic schema creation
    - Session management
    - SQLite optimizations
    """
    
    def __init__(self, database_url: str = None):
        """Initialize database manager"""
        self.database_url = database_url or settings.database_url
        
        # Create data directory if needed
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Configure engine
        if "sqlite" in self.database_url:
            # SQLite-specific configuration
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},  # Allow multi-threading
                poolclass=StaticPool,  # Single connection pool for SQLite
                echo=False  # Set to True for SQL debugging
            )
            
            # Enable WAL mode for better concurrency
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        else:
            # PostgreSQL/MySQL configuration
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections
                echo=False
            )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        )
        
        # Create tables
        self._create_tables()
        
        logger.info("database_initialized", 
                   url=self._mask_url(self.database_url),
                   dialect=self.engine.dialect.name)
    
    def _create_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("database_tables_created")
        except Exception as e:
            logger.error("failed_to_create_tables", error=str(e))
            raise
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of database URL for logging"""
        if "@" in url:
            # Mask password
            parts = url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split("://")[-1]
                user = user_pass.split(":")[0]
                return url.replace(user_pass, f"{user}:****")
        return url
    
    @contextmanager
    def get_session(self) -> Generator:
        """
        Get database session with automatic cleanup.
        
        Usage:
            with db_manager.get_session() as session:
                session.query(Model).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            session.close()
    
    def get_db(self):
        """
        Get database session for dependency injection.
        
        Usage:
            @app.get("/")
            def endpoint(db: Session = Depends(db_manager.get_db)):
                ...
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def close(self):
        """Close all connections"""
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("database_closed")
    
    def reset(self):
        """Drop and recreate all tables (DANGER: for testing only!)"""
        logger.warning("database_reset_initiated")
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        logger.warning("database_reset_complete")


# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get or create database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_db():
    """FastAPI dependency for database sessions"""
    db_manager = get_database_manager()
    return db_manager.get_db()
