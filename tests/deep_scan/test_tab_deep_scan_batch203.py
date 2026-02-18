"""Batch 203 — Models + compat + stores defense tests.

Validates fixes for:
- BUG-203-EMBED-CFG-001: Port env var parsing with try/except
- BUG-203-VSTORE-001: insert_batch only commits on success
- BUG-203-AGENT-001: agents.yaml encoding="utf-8"
"""
import os
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-203-EMBED-CFG-001: Port env var parsing ─────────────────────

class TestEmbeddingConfigPortParsing:
    """Port env vars must not crash on non-integer values."""

    def test_get_ollama_config_invalid_port(self):
        """get_ollama_config should fall back to default on invalid port."""
        from governance.embedding_config import get_ollama_config
        with patch.dict(os.environ, {"OLLAMA_PORT": "invalid"}):
            host, port = get_ollama_config()
            assert port == 11434, f"Expected default port 11434, got {port}"

    def test_get_litellm_config_invalid_port(self):
        """get_litellm_config should fall back to default on invalid port."""
        from governance.embedding_config import get_litellm_config
        with patch.dict(os.environ, {"LITELLM_PORT": "not_a_number"}):
            host, port = get_litellm_config()
            assert port == 4000, f"Expected default port 4000, got {port}"

    def test_get_ollama_config_empty_port(self):
        """get_ollama_config should handle empty string port."""
        from governance.embedding_config import get_ollama_config
        with patch.dict(os.environ, {"OLLAMA_PORT": ""}):
            host, port = get_ollama_config()
            assert port == 11434

    def test_port_parsing_has_try_except(self):
        """Both config functions must have try/except around int()."""
        src = (SRC / "governance/embedding_config.py").read_text()
        ollama_section = False
        litellm_section = False
        ollama_has_try = False
        litellm_has_try = False
        for line in src.splitlines():
            if "def get_ollama_config" in line:
                ollama_section = True
                litellm_section = False
            elif "def get_litellm_config" in line:
                litellm_section = True
                ollama_section = False
            elif line.strip().startswith("def ") and "config" not in line:
                ollama_section = False
                litellm_section = False
            if ollama_section and "except" in line:
                ollama_has_try = True
            if litellm_section and "except" in line:
                litellm_has_try = True
        assert ollama_has_try, "get_ollama_config must have try/except around int()"
        assert litellm_has_try, "get_litellm_config must have try/except around int()"


# ── BUG-203-VSTORE-001: insert_batch commit guard ───────────────────

class TestInsertBatchCommitGuard:
    """insert_batch must only commit when at least one insert succeeded."""

    def test_insert_batch_has_success_count_check(self):
        """insert_batch must check success_count before commit."""
        src = (SRC / "governance/vector_store/store.py").read_text()
        in_func = False
        found_guard = False
        for line in src.splitlines():
            if "def insert_batch" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "success_count > 0" in line:
                found_guard = True
        assert found_guard, "insert_batch must check success_count > 0 before commit"


# ── BUG-203-AGENT-001: agents.yaml encoding ─────────────────────────

class TestAgentsYamlEncoding:
    """agents.yaml file open must specify encoding."""

    def test_agents_yaml_open_has_encoding(self):
        """_load_workflow_configs must open agents.yaml with encoding='utf-8'."""
        src = (SRC / "governance/stores/agents.py").read_text()
        in_func = False
        for line in src.splitlines():
            if "def _load_workflow_configs" in line:
                in_func = True
            elif in_func and line.strip().startswith("def "):
                break
            elif in_func and "open(" in line and "YAML" in line.upper() or (in_func and "_AGENTS_YAML_FILE" in line and "open" in line):
                assert "encoding" in line, f"open() missing encoding: {line.strip()}"


# ── Embedding config functional tests ────────────────────────────────

class TestEmbeddingConfigFunctional:
    """Functional tests for embedding configuration."""

    def test_create_embedding_generator_mock(self):
        """create_embedding_generator(use_mock=True) returns MockEmbeddings."""
        from governance.embedding_config import create_embedding_generator
        gen = create_embedding_generator(use_mock=True)
        assert gen is not None

    def test_get_embedding_config_summary(self):
        """get_embedding_config_summary returns expected keys."""
        from governance.embedding_config import get_embedding_config_summary
        summary = get_embedding_config_summary()
        assert "use_mock" in summary
        assert "provider" in summary
        assert "ollama_config" in summary

    def test_get_embedding_provider_default(self):
        """Default provider should be ollama."""
        from governance.embedding_config import get_embedding_provider
        provider = get_embedding_provider()
        assert provider in ("ollama", "litellm", "mock")

    def test_get_embedding_provider_invalid_falls_back(self):
        """Invalid provider should fall back to ollama."""
        from governance.embedding_config import get_embedding_provider
        with patch.dict(os.environ, {"EMBEDDING_PROVIDER": "invalid_provider"}):
            provider = get_embedding_provider()
            assert provider == "ollama"


# ── Vector store defense tests ───────────────────────────────────────

class TestVectorStoreDefense:
    """Defense tests for vector store operations."""

    def test_cosine_similarity_zero_vectors(self):
        """cosine_similarity of zero vectors returns 0.0."""
        from governance.vector_store.store import VectorStore
        assert VectorStore._cosine_similarity([0, 0, 0], [0, 0, 0]) == 0.0

    def test_cosine_similarity_identical_vectors(self):
        """cosine_similarity of identical vectors returns ~1.0."""
        from governance.vector_store.store import VectorStore
        score = VectorStore._cosine_similarity([1, 2, 3], [1, 2, 3])
        assert abs(score - 1.0) < 0.001

    def test_cosine_similarity_different_lengths(self):
        """cosine_similarity of different-length vectors returns 0.0."""
        from governance.vector_store.store import VectorStore
        assert VectorStore._cosine_similarity([1, 2], [1, 2, 3]) == 0.0
