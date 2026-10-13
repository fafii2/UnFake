"""
Pytest fixtures shared across all test modules.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def client():
    """Synchronous test client using httpx."""
    from fastapi.testclient import TestClient
    return TestClient(app)
