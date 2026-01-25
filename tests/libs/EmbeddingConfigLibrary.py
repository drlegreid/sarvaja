"""
Robot Framework Library for Embedding Configuration Tests.

Per GAP-EMBED-001: Embedding Configuration.
Migrated from tests/test_embedding_config.py
"""
import os
from unittest.mock import patch
from robot.api.deco import keyword


class EmbeddingConfigLibrary:
    """Library for testing embedding configuration."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Environment Variable Defaults Tests
    # =============================================================================

    @keyword("Get Use Mock Defaults To False")
    def get_use_mock_defaults_to_false(self):
        """USE_MOCK_EMBEDDINGS defaults to False for production safety."""
        try:
            from governance.embedding_config import get_use_mock
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("USE_MOCK_EMBEDDINGS", None)
                return {"default_false": get_use_mock() is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Use Mock True When Set")
    def get_use_mock_true_when_set(self):
        """USE_MOCK_EMBEDDINGS=true enables mock mode."""
        try:
            from governance.embedding_config import get_use_mock
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
                return {"is_true": get_use_mock() is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Use Mock False When False")
    def get_use_mock_false_when_false(self):
        """USE_MOCK_EMBEDDINGS=false disables mock mode."""
        try:
            from governance.embedding_config import get_use_mock
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false"}):
                return {"is_false": get_use_mock() is False}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Embedding Provider Defaults To Ollama")
    def get_embedding_provider_defaults_to_ollama(self):
        """EMBEDDING_PROVIDER defaults to 'ollama' for real embeddings."""
        try:
            from governance.embedding_config import get_embedding_provider
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("EMBEDDING_PROVIDER", None)
                return {"is_ollama": get_embedding_provider() == "ollama"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Embedding Provider Litellm")
    def get_embedding_provider_litellm(self):
        """EMBEDDING_PROVIDER=litellm selects LiteLLM."""
        try:
            from governance.embedding_config import get_embedding_provider
            with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "litellm"}):
                return {"is_litellm": get_embedding_provider() == "litellm"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Embedding Provider Mock")
    def get_embedding_provider_mock(self):
        """EMBEDDING_PROVIDER=mock selects mock."""
        try:
            from governance.embedding_config import get_embedding_provider
            with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "mock"}):
                return {"is_mock": get_embedding_provider() == "mock"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Invalid Provider Defaults To Ollama")
    def invalid_provider_defaults_to_ollama(self):
        """Invalid EMBEDDING_PROVIDER falls back to ollama."""
        try:
            from governance.embedding_config import get_embedding_provider
            with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "invalid"}):
                return {"is_ollama": get_embedding_provider() == "ollama"}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Embedding Generator Factory Tests
    # =============================================================================

    @keyword("Create Mock When Use Mock True")
    def create_mock_when_use_mock_true(self):
        """create_embedding_generator returns MockEmbeddings when use_mock=True."""
        try:
            from governance.embedding_config import create_embedding_generator
            from governance.vector_store.embeddings import MockEmbeddings
            generator = create_embedding_generator(use_mock=True)
            return {"is_mock": isinstance(generator, MockEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Ollama When Provider Ollama")
    def create_ollama_when_provider_ollama(self):
        """create_embedding_generator returns OllamaEmbeddings for ollama provider."""
        try:
            from governance.embedding_config import create_embedding_generator
            from governance.vector_store.embeddings import OllamaEmbeddings
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false", "EMBEDDING_PROVIDER": "ollama"}):
                generator = create_embedding_generator()
                return {"is_ollama": isinstance(generator, OllamaEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Litellm When Provider Litellm")
    def create_litellm_when_provider_litellm(self):
        """create_embedding_generator returns LiteLLMEmbeddings for litellm provider."""
        try:
            from governance.embedding_config import create_embedding_generator
            from governance.vector_store.embeddings import LiteLLMEmbeddings
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false", "EMBEDDING_PROVIDER": "litellm"}):
                generator = create_embedding_generator()
                return {"is_litellm": isinstance(generator, LiteLLMEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Use Mock Overrides Provider")
    def use_mock_overrides_provider(self):
        """use_mock=True overrides provider setting."""
        try:
            from governance.embedding_config import create_embedding_generator
            from governance.vector_store.embeddings import MockEmbeddings
            with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "ollama"}):
                generator = create_embedding_generator(use_mock=True)
                return {"is_mock": isinstance(generator, MockEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Mock Uses Dimension Parameter")
    def mock_uses_dimension_parameter(self):
        """MockEmbeddings uses the dimension parameter."""
        try:
            from governance.embedding_config import create_embedding_generator
            generator = create_embedding_generator(use_mock=True, dimension=768)
            return {"dimension_768": generator.dimension == 768}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Default Dimension Is 384")
    def default_dimension_is_384(self):
        """Default dimension is 384."""
        try:
            from governance.embedding_config import create_embedding_generator
            generator = create_embedding_generator(use_mock=True)
            return {"dimension_384": generator.dimension == 384}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Host/Port Configuration Tests
    # =============================================================================

    @keyword("Get Ollama Config Defaults")
    def get_ollama_config_defaults(self):
        """Ollama defaults to localhost:11434."""
        try:
            from governance.embedding_config import get_ollama_config
            with patch.dict(os.environ, {}, clear=True):
                host, port = get_ollama_config()
                return {
                    "host_localhost": host == "localhost",
                    "port_11434": port == 11434
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Ollama Config From Env")
    def get_ollama_config_from_env(self):
        """Ollama config from environment variables."""
        try:
            from governance.embedding_config import get_ollama_config
            with patch.dict(os.environ, {"OLLAMA_HOST": "ollama.local", "OLLAMA_PORT": "11435"}):
                host, port = get_ollama_config()
                return {
                    "host_correct": host == "ollama.local",
                    "port_correct": port == 11435
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Litellm Config Defaults")
    def get_litellm_config_defaults(self):
        """LiteLLM defaults to localhost:4000."""
        try:
            from governance.embedding_config import get_litellm_config
            with patch.dict(os.environ, {}, clear=True):
                host, port = get_litellm_config()
                return {
                    "host_localhost": host == "localhost",
                    "port_4000": port == 4000
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Litellm Config From Env")
    def get_litellm_config_from_env(self):
        """LiteLLM config from environment variables."""
        try:
            from governance.embedding_config import get_litellm_config
            with patch.dict(os.environ, {"LITELLM_HOST": "litellm.local", "LITELLM_PORT": "4001"}):
                host, port = get_litellm_config()
                return {
                    "host_correct": host == "litellm.local",
                    "port_correct": port == 4001
                }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Config Summary Tests
    # =============================================================================

    @keyword("Get Embedding Config Summary Returns Dict")
    def get_embedding_config_summary_returns_dict(self):
        """get_embedding_config_summary returns a dictionary."""
        try:
            from governance.embedding_config import get_embedding_config_summary
            summary = get_embedding_config_summary()
            return {"is_dict": isinstance(summary, dict)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Config Summary Has Required Keys")
    def config_summary_has_required_keys(self):
        """Config summary includes all required keys."""
        try:
            from governance.embedding_config import get_embedding_config_summary
            summary = get_embedding_config_summary()
            return {
                "has_use_mock": "use_mock" in summary,
                "has_provider": "provider" in summary,
                "has_ollama_config": "ollama_config" in summary,
                "has_litellm_config": "litellm_config" in summary,
                "has_env_vars": "env_vars" in summary
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Pipeline Integration Tests
    # =============================================================================

    @keyword("Pipeline Uses Env Config By Default")
    def pipeline_uses_env_config_by_default(self):
        """EmbeddingPipeline uses environment config by default."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store.embeddings import MockEmbeddings
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
                pipeline = EmbeddingPipeline()
                return {"is_mock": isinstance(pipeline.generator, MockEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Embedding Pipeline Uses Env Config")
    def create_embedding_pipeline_uses_env_config(self):
        """create_embedding_pipeline uses environment config."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline
            from governance.vector_store.embeddings import MockEmbeddings
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "true"}):
                pipeline = create_embedding_pipeline()
                return {"is_mock": isinstance(pipeline.generator, MockEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Embedding Pipeline Override Works")
    def create_embedding_pipeline_override_works(self):
        """create_embedding_pipeline use_mock parameter overrides env."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline
            from governance.vector_store.embeddings import MockEmbeddings
            with patch.dict(os.environ, {"USE_MOCK_EMBEDDINGS": "false"}):
                pipeline = create_embedding_pipeline(use_mock=True)
                return {"is_mock": isinstance(pipeline.generator, MockEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Production Safety Tests
    # =============================================================================

    @keyword("No Env Vars Means Real Embeddings")
    def no_env_vars_means_real_embeddings(self):
        """Without env vars, real embeddings are used (OllamaEmbeddings)."""
        try:
            from governance.embedding_config import create_embedding_generator
            from governance.vector_store.embeddings import OllamaEmbeddings
            with patch.dict(os.environ, {}, clear=True):
                for var in ["USE_MOCK_EMBEDDINGS", "EMBEDDING_PROVIDER"]:
                    os.environ.pop(var, None)
                generator = create_embedding_generator()
                return {"is_ollama": isinstance(generator, OllamaEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Pipeline Default Not Mock")
    def pipeline_default_not_mock(self):
        """EmbeddingPipeline default is not MockEmbeddings in production."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline
            from governance.vector_store.embeddings import OllamaEmbeddings
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("USE_MOCK_EMBEDDINGS", None)
                os.environ.pop("EMBEDDING_PROVIDER", None)
                pipeline = create_embedding_pipeline(use_mock=None)
                return {"is_ollama": isinstance(pipeline.generator, OllamaEmbeddings)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
