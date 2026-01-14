"""
Embedding Configuration.

Per GAP-EMBED-001: Environment-based embedding provider configuration.
Per RULE-004: Production code must not default to mocks.

Environment Variables:
    USE_MOCK_EMBEDDINGS: "true" to use mock embeddings (default: "false")
    EMBEDDING_PROVIDER: "ollama", "litellm", or "mock" (default: "ollama")
    OLLAMA_HOST: Ollama server host (default: "localhost")
    OLLAMA_PORT: Ollama server port (default: 11434)
    LITELLM_HOST: LiteLLM proxy host (default: "localhost")
    LITELLM_PORT: LiteLLM proxy port (default: 4000)

Created: 2026-01-14
"""

import os
from typing import Optional

from governance.vector_store.embeddings import (
    EmbeddingGenerator,
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
)


# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

def get_use_mock() -> bool:
    """Check if mock embeddings should be used.

    Returns True only if USE_MOCK_EMBEDDINGS is explicitly "true".
    Default is False for production safety.
    """
    return os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"


def get_embedding_provider() -> str:
    """Get configured embedding provider.

    Returns: "ollama", "litellm", or "mock"
    Default: "ollama" (real embeddings)
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
    if provider not in ("ollama", "litellm", "mock"):
        return "ollama"
    return provider


def get_ollama_config() -> tuple:
    """Get Ollama configuration from environment.

    Returns: (host, port)
    """
    host = os.getenv("OLLAMA_HOST", "localhost")
    port = int(os.getenv("OLLAMA_PORT", "11434"))
    return host, port


def get_litellm_config() -> tuple:
    """Get LiteLLM configuration from environment.

    Returns: (host, port)
    """
    host = os.getenv("LITELLM_HOST", "localhost")
    port = int(os.getenv("LITELLM_PORT", "4000"))
    return host, port


# =============================================================================
# EMBEDDING GENERATOR FACTORY
# =============================================================================

def create_embedding_generator(
    use_mock: Optional[bool] = None,
    provider: Optional[str] = None,
    dimension: int = 384
) -> EmbeddingGenerator:
    """Create embedding generator based on configuration.

    Per GAP-EMBED-001: Production default is real embeddings.

    Args:
        use_mock: Override USE_MOCK_EMBEDDINGS env var (None = use env)
        provider: Override EMBEDDING_PROVIDER env var (None = use env)
        dimension: Embedding dimension for mock generator

    Returns:
        Configured EmbeddingGenerator instance
    """
    # Determine if mock should be used
    if use_mock is None:
        use_mock = get_use_mock()

    if use_mock:
        return MockEmbeddings(dimension=dimension)

    # Get provider
    if provider is None:
        provider = get_embedding_provider()

    # Create generator based on provider
    if provider == "mock":
        return MockEmbeddings(dimension=dimension)
    elif provider == "litellm":
        host, port = get_litellm_config()
        return LiteLLMEmbeddings(host=host, port=port)
    else:  # default: ollama
        host, port = get_ollama_config()
        return OllamaEmbeddings(host=host, port=port)


def get_embedding_config_summary() -> dict:
    """Get summary of embedding configuration for diagnostics.

    Returns:
        Dict with configuration state
    """
    return {
        "use_mock": get_use_mock(),
        "provider": get_embedding_provider(),
        "ollama_config": get_ollama_config(),
        "litellm_config": get_litellm_config(),
        "env_vars": {
            "USE_MOCK_EMBEDDINGS": os.getenv("USE_MOCK_EMBEDDINGS"),
            "EMBEDDING_PROVIDER": os.getenv("EMBEDDING_PROVIDER"),
            "OLLAMA_HOST": os.getenv("OLLAMA_HOST"),
            "OLLAMA_PORT": os.getenv("OLLAMA_PORT"),
        }
    }


__all__ = [
    "get_use_mock",
    "get_embedding_provider",
    "get_ollama_config",
    "get_litellm_config",
    "create_embedding_generator",
    "get_embedding_config_summary",
]
