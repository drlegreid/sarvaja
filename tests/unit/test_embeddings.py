"""
Unit tests for Embedding Generators.

Per DOC-SIZE-01-v1: Tests for governance/vector_store/embeddings.py module.
Tests: EmbeddingGenerator (base), MockEmbeddings, OllamaEmbeddings, LiteLLMEmbeddings.
"""

import pytest
from unittest.mock import patch, MagicMock

from governance.vector_store.embeddings import (
    EmbeddingGenerator,
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
)


# ── EmbeddingGenerator (base) ─────────────────────────────


class TestEmbeddingGenerator:
    def test_generate_not_implemented(self):
        gen = EmbeddingGenerator()
        with pytest.raises(NotImplementedError):
            gen.generate("test")

    def test_model_name_not_implemented(self):
        gen = EmbeddingGenerator()
        with pytest.raises(NotImplementedError):
            _ = gen.model_name

    def test_dimension_not_implemented(self):
        gen = EmbeddingGenerator()
        with pytest.raises(NotImplementedError):
            _ = gen.dimension

    def test_generate_batch_delegates(self):
        gen = MockEmbeddings(dimension=4)
        results = gen.generate_batch(["hello", "world"])
        assert len(results) == 2
        assert len(results[0]) == 4
        assert len(results[1]) == 4


# ── MockEmbeddings ────────────────────────────────────────


class TestMockEmbeddings:
    def test_default_dimension(self):
        mock = MockEmbeddings()
        assert mock.dimension == 384

    def test_custom_dimension(self):
        mock = MockEmbeddings(dimension=128)
        assert mock.dimension == 128

    def test_model_name(self):
        mock = MockEmbeddings()
        assert mock.model_name == "mock-embeddings"

    def test_generate_returns_correct_length(self):
        mock = MockEmbeddings(dimension=64)
        embedding = mock.generate("hello world")
        assert len(embedding) == 64

    def test_generate_deterministic(self):
        mock = MockEmbeddings(dimension=32)
        e1 = mock.generate("same text")
        e2 = mock.generate("same text")
        assert e1 == e2

    def test_generate_different_for_different_text(self):
        mock = MockEmbeddings(dimension=32)
        e1 = mock.generate("text one")
        e2 = mock.generate("text two")
        assert e1 != e2

    def test_values_in_range(self):
        mock = MockEmbeddings(dimension=100)
        embedding = mock.generate("test")
        for val in embedding:
            assert -1.0 <= val <= 1.0

    def test_generate_batch(self):
        mock = MockEmbeddings(dimension=16)
        results = mock.generate_batch(["a", "b", "c"])
        assert len(results) == 3
        assert all(len(e) == 16 for e in results)

    def test_empty_text(self):
        mock = MockEmbeddings(dimension=8)
        embedding = mock.generate("")
        assert len(embedding) == 8


# ── OllamaEmbeddings ──────────────────────────────────────


class TestOllamaEmbeddings:
    def test_defaults(self):
        embed = OllamaEmbeddings()
        assert embed.host == "localhost"
        assert embed.port == 11434
        assert embed.model == "nomic-embed-text"
        assert embed.dimension == 768

    def test_custom(self):
        embed = OllamaEmbeddings(host="gpu-server", port=11435, model="all-minilm")
        assert embed.host == "gpu-server"
        assert embed.port == 11435
        assert embed.model == "all-minilm"

    def test_model_name(self):
        embed = OllamaEmbeddings(model="nomic-embed-text")
        assert embed.model_name == "ollama/nomic-embed-text"

    def test_generate_calls_api(self):
        embed = OllamaEmbeddings(host="test", port=9999)
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response) as mock_post:
            result = embed.generate("hello")

        mock_post.assert_called_once_with(
            "http://test:9999/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": "hello"},
            timeout=30,
        )
        assert result == [0.1, 0.2, 0.3]


# ── LiteLLMEmbeddings ─────────────────────────────────────


class TestLiteLLMEmbeddings:
    def test_defaults(self):
        embed = LiteLLMEmbeddings()
        assert embed.host == "localhost"
        assert embed.port == 4000
        assert embed.model == "text-embedding-3-small"
        assert embed.dimension == 1536

    def test_custom(self):
        embed = LiteLLMEmbeddings(host="proxy", port=5000, model="custom-model")
        assert embed.host == "proxy"
        assert embed.model == "custom-model"

    def test_model_name(self):
        embed = LiteLLMEmbeddings(model="text-embedding-3-small")
        assert embed.model_name == "litellm/text-embedding-3-small"

    def test_generate_calls_api(self):
        embed = LiteLLMEmbeddings(host="test", port=4000)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.5, 0.6]}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.post", return_value=mock_response) as mock_post:
            result = embed.generate("test text")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test:4000/embeddings"
        assert call_args[1]["json"]["model"] == "text-embedding-3-small"
        assert call_args[1]["json"]["input"] == "test text"
        assert result == [0.5, 0.6]
