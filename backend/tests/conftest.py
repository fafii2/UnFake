"""
Pytest fixtures shared across all test modules.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from config import settings


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Tests never call paid providers or mutate the developer's archive."""
    monkeypatch.setattr(settings, 'ARCHIVE_PATH', tmp_path / 'archive.sqlite3')
    monkeypatch.setattr(settings, 'SEARCH_API_KEY', None)
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', None)
    monkeypatch.setattr(settings, 'EMBEDDING_PROVIDER', 'none')
    monkeypatch.setattr(settings, 'CALIBRATION_PATH', tmp_path / 'calibration.json')


@pytest.fixture
def client():
    """Synchronous test client using httpx."""
    from fastapi.testclient import TestClient
    return TestClient(app)
