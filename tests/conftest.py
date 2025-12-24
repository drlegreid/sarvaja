"""
Pytest configuration and fixtures for Sim.ai PoC tests.
"""
import os
import pytest
import httpx
from typing import Generator

# Service endpoints
LITELLM_URL = os.getenv("LITELLM_URL", "http://localhost:4000")
CHROMADB_URL = os.getenv("CHROMADB_URL", "http://localhost:8001")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
AGENTS_URL = os.getenv("AGENTS_URL", "http://localhost:7777")
OPIK_URL = os.getenv("OPIK_URL", "http://localhost:5173")
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
LITELLM_API_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-dev-key")


@pytest.fixture(scope="session")
def http_client() -> Generator[httpx.Client, None, None]:
    """Shared HTTP client for all tests."""
    client = httpx.Client(timeout=30.0)
    yield client
    client.close()


@pytest.fixture
def litellm_client(http_client: httpx.Client):
    """LiteLLM API client."""
    return {"client": http_client, "base_url": LITELLM_URL, "api_key": LITELLM_API_KEY}


@pytest.fixture
def chromadb_client(http_client: httpx.Client):
    """ChromaDB API client."""
    return {"client": http_client, "base_url": CHROMADB_URL}


@pytest.fixture
def agents_client(http_client: httpx.Client):
    """Agents API client."""
    return {"client": http_client, "base_url": AGENTS_URL}


@pytest.fixture
def opik_client(http_client: httpx.Client):
    """Opik API client."""
    return {"client": http_client, "base_url": OPIK_URL}


@pytest.fixture
def typedb_config():
    """TypeDB connection config."""
    return {"host": TYPEDB_HOST, "port": TYPEDB_PORT}


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: Integration tests requiring running services")
    config.addinivalue_line("markers", "unit: Unit tests that don't require services")
    config.addinivalue_line("markers", "slow: Slow tests (model inference)")
