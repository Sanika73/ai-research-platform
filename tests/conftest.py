"""
Test configuration and fixtures for AI Research Platform
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('services.research_client.OpenAI') as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Initialize test database
    from models.database import init_db
    init_db(db_path)
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_research_request():
    """Sample research request data"""
    return {
        "query": "AI app for construction workers",
        "model": "o3-deep-research",
        "research_type": "custom",
        "enrich_prompt": True
    }


@pytest.fixture
def sample_research_result():
    """Sample research result data"""
    return {
        "status": "completed",
        "output": "# AI App for Construction Workers\n\nThis is a sample research result...",
        "citations": 5,
        "word_count": 1500,
        "processing_time": 120.5
    }
