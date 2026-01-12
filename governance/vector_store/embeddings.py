"""
Embedding Generators.

Per RULE-032: Modularized from vector_store.py (531 lines).
Contains: EmbeddingGenerator base class and implementations.
"""

import hashlib
from typing import List


class EmbeddingGenerator:
    """
    Abstract embedding generator interface.

    Implementations:
    - OpenAIEmbeddings: text-embedding-3-small (1536 dims)
    - OllamaEmbeddings: nomic-embed-text (768 dims)
    - MockEmbeddings: for testing
    """

    def generate(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return [self.generate(text) for text in texts]

    @property
    def model_name(self) -> str:
        """Return model name."""
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        raise NotImplementedError


class MockEmbeddings(EmbeddingGenerator):
    """Mock embeddings for testing."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def generate(self, text: str) -> List[float]:
        """Generate deterministic mock embedding based on text hash."""
        # Create deterministic embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to floats in range [-1, 1]
        embedding = []
        for i in range(self._dimension):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] - 128) / 128.0
            embedding.append(value)
        return embedding

    @property
    def model_name(self) -> str:
        return "mock-embeddings"

    @property
    def dimension(self) -> int:
        return self._dimension


class OllamaEmbeddings(EmbeddingGenerator):
    """Ollama embeddings using nomic-embed-text model."""

    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "nomic-embed-text"):
        self.host = host
        self.port = port
        self.model = model
        self._dimension = 768  # nomic-embed-text dimension

    def generate(self, text: str) -> List[float]:
        """Generate embedding using Ollama."""
        import httpx

        url = f"http://{self.host}:{self.port}/api/embeddings"
        response = httpx.post(url, json={"model": self.model, "prompt": text}, timeout=30)
        response.raise_for_status()
        return response.json()["embedding"]

    @property
    def model_name(self) -> str:
        return f"ollama/{self.model}"

    @property
    def dimension(self) -> int:
        return self._dimension


class LiteLLMEmbeddings(EmbeddingGenerator):
    """LiteLLM embeddings using configured model."""

    def __init__(self, host: str = "localhost", port: int = 4000, model: str = "text-embedding-3-small"):
        self.host = host
        self.port = port
        self.model = model
        self._dimension = 1536  # OpenAI default

    def generate(self, text: str) -> List[float]:
        """Generate embedding using LiteLLM proxy."""
        import httpx

        url = f"http://{self.host}:{self.port}/embeddings"
        response = httpx.post(
            url,
            json={"model": self.model, "input": text},
            headers={"Authorization": "Bearer sk-litellm-master-key-change-me"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]

    @property
    def model_name(self) -> str:
        return f"litellm/{self.model}"

    @property
    def dimension(self) -> int:
        return self._dimension
