"""
Tests for embedding configuration module.

Per GAP-EMBED-001: Environment-based embedding provider configuration.
Covers env var parsing, provider selection, and factory functions.

Created: 2026-01-30
"""

import os
import pytest

from governance.embedding_config import (
    get_use_mock,
    get_embedding_provider,
    get_ollama_config,
    get_litellm_config,
    create_embedding_generator,
    get_embedding_config_summary,
)
from governance.vector_store.embeddings import (
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
)


class TestGetUseMock:
    """Test USE_MOCK_EMBEDDINGS env var parsing."""

    def test_default_false(self, monkeypatch):
        """Default is False (production safety)."""
        monkeypatch.delenv("USE_MOCK_EMBEDDINGS", raising=False)
        assert get_use_mock() is False

    def test_true(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "true")
        assert get_use_mock() is True

    def test_true_uppercase(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "TRUE")
        assert get_use_mock() is True

    def test_false_explicit(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "false")
        assert get_use_mock() is False

    def test_invalid_treated_as_false(self, monkeypatch):
        monkeypatch.setenv("USE_MOCK_EMBEDDINGS", "yes")
        assert get_use_mock() is False


class TestGetEmbeddingProvider:
    """Test EMBEDDING_PROVIDER env var parsing."""

    def test_default_ollama(self, monkeypatch):
        monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
        assert get_embedding_provider() == "ollama"

    def test_ollama(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
        assert get_embedding_provider() == "ollama"

    def test_litellm(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "litellm")
        assert get_embedding_provider() == "litellm"

    def test_mock(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "mock")
        assert get_embedding_provider() == "mock"

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "OLLAMA")
        assert get_embedding_provider() == "ollama"

    def test_invalid_defaults_to_ollama(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "invalid")
        assert get_embedding_provider() == "ollama"


class TestGetOllamaConfig:
    """Test Ollama configuration from environment."""

    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_PORT", raising=False)
        host, port = get_ollama_config()
        assert host == "localhost"
        assert port == 11434

    def test_custom(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_HOST", "ollama.local")
        monkeypatch.setenv("OLLAMA_PORT", "8080")
        host, port = get_ollama_config()
        assert host == "ollama.local"
        assert port == 8080


class TestGetLiteLLMConfig:
    """Test LiteLLM configuration from environment."""

    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("LITELLM_HOST", raising=False)
        monkeypatch.delenv("LITELLM_PORT", raising=False)
        host, port = get_litellm_config()
        assert host == "localhost"
        assert port == 4000

    def test_custom(self, monkeypatch):
        monkeypatch.setenv("LITELLM_HOST", "litellm.local")
        monkeypatch.setenv("LITELLM_PORT", "5000")
        host, port = get_litellm_config()
        assert host == "litellm.local"
        assert port == 5000


class TestCreateEmbeddingGenerator:
    """Test embedding generator factory."""

    def test_mock_explicit(self):
        gen = create_embedding_generator(use_mock=True)
        assert isinstance(gen, MockEmbeddings)

    def test_mock_provider(self):
        gen = create_embedding_generator(use_mock=False, provider="mock")
        assert isinstance(gen, MockEmbeddings)

    def test_ollama_provider(self):
        gen = create_embedding_generator(use_mock=False, provider="ollama")
        assert isinstance(gen, OllamaEmbeddings)

    def test_litellm_provider(self):
        gen = create_embedding_generator(use_mock=False, provider="litellm")
        assert isinstance(gen, LiteLLMEmbeddings)

    def test_mock_dimension(self):
        gen = create_embedding_generator(use_mock=True, dimension=768)
        assert isinstance(gen, MockEmbeddings)

    def test_env_override_mock(self, monkeypatch):
        """use_mock=True overrides env provider."""
        monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
        gen = create_embedding_generator(use_mock=True)
        assert isinstance(gen, MockEmbeddings)


class TestGetEmbeddingConfigSummary:
    """Test configuration summary for diagnostics."""

    def test_has_required_keys(self):
        summary = get_embedding_config_summary()
        assert "use_mock" in summary
        assert "provider" in summary
        assert "ollama_config" in summary
        assert "litellm_config" in summary
        assert "env_vars" in summary

    def test_provider_is_string(self):
        summary = get_embedding_config_summary()
        assert isinstance(summary["provider"], str)

    def test_configs_are_tuples(self):
        summary = get_embedding_config_summary()
        assert isinstance(summary["ollama_config"], tuple)
        assert isinstance(summary["litellm_config"], tuple)
