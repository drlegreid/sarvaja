"""
Tests for GAP-EMBED-001: Embedding Configuration

TDD tests per RULE-004: Exploratory Testing & Executable Specification
Per: GAP-EMBED-001, GAP-EMBED-002, GAP-EMBED-003, GAP-EMBED-004

Tests cover:
1. Environment variable configuration
2. Default behavior (production = real embeddings)
3. Mock override via env var
4. Provider selection (ollama, litellm, mock)
"""

import pytest
import os
from unittest.mock import patch


# =============================================================================
# Test 1: Environment Variable Defaults
# =============================================================================

class TestEnvironmentDefaults:
    """Tests for environment variable default behavior."""

    def test_get_use_mock_defaults_to_false(self):
        """USE_MOCK_EMBEDDINGS defaults to False for production safety."""
        from governance.embedding_config import get_use_mock

        # Clear env var to test default
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            os.environ.pop("USE_MOCK_EMBEDDINGS", None)
            assert get_use_mock() is False

    def test_get_use_mock_true_when_set(self):
        """USE_MOCK_EMBEDDINGS=true enables mock mode."""
        from governance.embedding_config import get_use_mock

        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
            assert get_use_mock() is True

    def test_get_use_mock_false_when_false(self):
        """USE_MOCK_EMBEDDINGS=false disables mock mode."""
        from governance.embedding_config import get_use_mock

        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false"}):
            assert get_use_mock() is False

    def test_get_embedding_provider_defaults_to_ollama(self):
        """EMBEDDING_PROVIDER defaults to 'ollama' for real embeddings."""
        from governance.embedding_config import get_embedding_provider

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("EMBEDDING_PROVIDER", None)
            assert get_embedding_provider() == "ollama"

    def test_get_embedding_provider_litellm(self):
        """EMBEDDING_PROVIDER=litellm selects LiteLLM."""
        from governance.embedding_config import get_embedding_provider

        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "litellm"}):
            assert get_embedding_provider() == "litellm"

    def test_get_embedding_provider_mock(self):
        """EMBEDDING_PROVIDER=mock selects mock."""
        from governance.embedding_config import get_embedding_provider

        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "mock"}):
            assert get_embedding_provider() == "mock"

    def test_invalid_provider_defaults_to_ollama(self):
        """Invalid EMBEDDING_PROVIDER falls back to ollama."""
        from governance.embedding_config import get_embedding_provider

        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "invalid"}):
            assert get_embedding_provider() == "ollama"


# =============================================================================
# Test 2: Embedding Generator Factory
# =============================================================================

class TestEmbeddingGeneratorFactory:
    """Tests for create_embedding_generator factory function."""

    def test_create_mock_when_use_mock_true(self):
        """create_embedding_generator returns MockEmbeddings when use_mock=True."""
        from governance.embedding_config import create_embedding_generator
        from governance.vector_store.embeddings import MockEmbeddings

        generator = create_embedding_generator(use_mock=True)
        assert isinstance(generator, MockEmbeddings)

    def test_create_ollama_when_provider_ollama(self):
        """create_embedding_generator returns OllamaEmbeddings for ollama provider."""
        from governance.embedding_config import create_embedding_generator
        from governance.vector_store.embeddings import OllamaEmbeddings

        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false", "EMBEDDING_PROVIDER": "ollama"}):
            generator = create_embedding_generator()
            assert isinstance(generator, OllamaEmbeddings)

    def test_create_litellm_when_provider_litellm(self):
        """create_embedding_generator returns LiteLLMEmbeddings for litellm provider."""
        from governance.embedding_config import create_embedding_generator
        from governance.vector_store.embeddings import LiteLLMEmbeddings

        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false", "EMBEDDING_PROVIDER": "litellm"}):
            generator = create_embedding_generator()
            assert isinstance(generator, LiteLLMEmbeddings)

    def test_use_mock_overrides_provider(self):
        """use_mock=True overrides provider setting."""
        from governance.embedding_config import create_embedding_generator
        from governance.vector_store.embeddings import MockEmbeddings

        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "ollama"}):
            generator = create_embedding_generator(use_mock=True)
            assert isinstance(generator, MockEmbeddings)

    def test_mock_uses_dimension_parameter(self):
        """MockEmbeddings uses the dimension parameter."""
        from governance.embedding_config import create_embedding_generator

        generator = create_embedding_generator(use_mock=True, dimension=768)
        assert generator.dimension == 768

    def test_default_dimension_is_384(self):
        """Default dimension is 384."""
        from governance.embedding_config import create_embedding_generator

        generator = create_embedding_generator(use_mock=True)
        assert generator.dimension == 384


# =============================================================================
# Test 3: Host/Port Configuration
# =============================================================================

class TestHostPortConfig:
    """Tests for host/port configuration."""

    def test_get_ollama_config_defaults(self):
        """Ollama defaults to localhost:11434."""
        from governance.embedding_config import get_ollama_config

        with patch.dict(os.environ, {}, clear=True):
            host, port = get_ollama_config()
            assert host == "localhost"
            assert port == 11434

    def test_get_ollama_config_from_env(self):
        """Ollama config from environment variables."""
        from governance.embedding_config import get_ollama_config

        with patch.dict(os.environ, {"OLLAMA_HOST": "ollama.local", "OLLAMA_PORT": "11435"}):
            host, port = get_ollama_config()
            assert host == "ollama.local"
            assert port == 11435

    def test_get_litellm_config_defaults(self):
        """LiteLLM defaults to localhost:4000."""
        from governance.embedding_config import get_litellm_config

        with patch.dict(os.environ, {}, clear=True):
            host, port = get_litellm_config()
            assert host == "localhost"
            assert port == 4000

    def test_get_litellm_config_from_env(self):
        """LiteLLM config from environment variables."""
        from governance.embedding_config import get_litellm_config

        with patch.dict(os.environ, {"LITELLM_HOST": "litellm.local", "LITELLM_PORT": "4001"}):
            host, port = get_litellm_config()
            assert host == "litellm.local"
            assert port == 4001


# =============================================================================
# Test 4: Config Summary for Diagnostics
# =============================================================================

class TestConfigSummary:
    """Tests for configuration summary."""

    def test_get_embedding_config_summary_returns_dict(self):
        """get_embedding_config_summary returns a dictionary."""
        from governance.embedding_config import get_embedding_config_summary

        summary = get_embedding_config_summary()
        assert isinstance(summary, dict)

    def test_config_summary_has_required_keys(self):
        """Config summary includes all required keys."""
        from governance.embedding_config import get_embedding_config_summary

        summary = get_embedding_config_summary()
        assert "use_mock" in summary
        assert "provider" in summary
        assert "ollama_config" in summary
        assert "litellm_config" in summary
        assert "env_vars" in summary


# =============================================================================
# Test 5: Integration with Embedding Pipeline
# =============================================================================

class TestEmbeddingPipelineIntegration:
    """Tests for integration with embedding_pipeline.py."""

    def test_pipeline_uses_env_config_by_default(self):
        """EmbeddingPipeline uses environment config by default."""
        from governance.embedding_pipeline import EmbeddingPipeline
        from governance.vector_store.embeddings import MockEmbeddings, OllamaEmbeddings

        # With mock env var set
        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
            pipeline = EmbeddingPipeline()
            assert isinstance(pipeline.generator, MockEmbeddings)

    def test_create_embedding_pipeline_uses_env_config(self):
        """create_embedding_pipeline uses environment config."""
        from governance.embedding_pipeline import create_embedding_pipeline
        from governance.vector_store.embeddings import MockEmbeddings

        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
            pipeline = create_embedding_pipeline()
            assert isinstance(pipeline.generator, MockEmbeddings)

    def test_create_embedding_pipeline_override_works(self):
        """create_embedding_pipeline use_mock parameter overrides env."""
        from governance.embedding_pipeline import create_embedding_pipeline
        from governance.vector_store.embeddings import MockEmbeddings

        # Even with env set to false, use_mock=True should work
        with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false"}):
            pipeline = create_embedding_pipeline(use_mock=True)
            assert isinstance(pipeline.generator, MockEmbeddings)


# =============================================================================
# Test 6: Production Safety
# =============================================================================

class TestProductionSafety:
    """Tests ensuring production defaults are safe (real embeddings)."""

    def test_no_env_vars_means_real_embeddings(self):
        """Without env vars, real embeddings are used (OllamaEmbeddings)."""
        from governance.embedding_config import create_embedding_generator
        from governance.vector_store.embeddings import OllamaEmbeddings

        # Simulate clean environment
        with patch.dict(os.environ, {}, clear=True):
            # Ensure our target vars are not set
            for var in ["USE_MOCK_EMBEDDINGS", "EMBEDDING_PROVIDER"]:
                os.environ.pop(var, None)

            generator = create_embedding_generator()
            assert isinstance(generator, OllamaEmbeddings)

    def test_pipeline_default_not_mock(self):
        """EmbeddingPipeline default is not MockEmbeddings in production."""
        from governance.embedding_pipeline import create_embedding_pipeline
        from governance.vector_store.embeddings import MockEmbeddings, OllamaEmbeddings

        # Simulate production (no mock env var)
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("USE_MOCK_EMBEDDINGS", None)
            os.environ.pop("EMBEDDING_PROVIDER", None)

            # When use_mock is None (default), should use env config
            pipeline = create_embedding_pipeline(use_mock=None)
            # Should be Ollama (real) not Mock
            assert isinstance(pipeline.generator, OllamaEmbeddings)
