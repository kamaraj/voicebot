"""
Pytest configuration and fixtures
Shared test utilities and setup
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import Base, get_database_manager
from src.api.main import app
from src.memory.cache import ResponseCache
from src.persistence.conversation_db import PersistentConversationMemory


@pytest.fixture(scope="session")
def test_db_path():
    """Create temporary database for tests"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield f"sqlite:///{db_path}"
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_session(test_db_path):
    """Create a fresh database session for each test"""
    # Create engine
    engine = create_engine(
        test_db_path,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_cache():
    """Create a fresh cache for each test"""
    cache = ResponseCache(ttl_minutes=60, max_size=100)
    yield cache
    cache.clear()


@pytest.fixture(scope="function")
def test_memory():
    """Create a fresh conversation memory for each test"""
    memory = PersistentConversationMemory(
        max_messages=10,
        max_conversations=100,
        use_database=False  # Use in-memory for tests
    )
    yield memory


@pytest.fixture(scope="module")
def test_client():
    """Create FastAPI test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_conversation():
    """Sample conversation data for testing"""
    return {
        "conversation_id": "test_conv_123",
        "messages": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm doing well, thanks!"}
        ]
    }


@pytest.fixture
def sample_api_key_data():
    """Sample API key data for testing"""
    return {
        "name": "Test Key",
        "user_id": "test_user",
        "rate_limit_per_minute": 60,
        "rate_limit_per_day": 10000
    }
