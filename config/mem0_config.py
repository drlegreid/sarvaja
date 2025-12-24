"""
Mem0 Configuration for sim-ai
=============================

Uses Ollama for both LLM and embeddings (no OpenAI dependency).
Validated: 2024-12-24 per DECISION-002

Requirements:
- pip install mem0ai ollama
- Ollama running with models: gemma3:4b, nomic-embed-text

Usage:
    from config.mem0_config import get_mem0_config, create_memory

    m = create_memory()
    m.add("Your memory content", user_id="sim-ai")
    results = m.search("query", user_id="sim-ai")
"""

from mem0 import Memory

# Ollama-based config (no OpenAI needed)
MEM0_CONFIG = {
    'llm': {
        'provider': 'ollama',
        'config': {
            'model': 'gemma3:4b',
            'ollama_base_url': 'http://localhost:11434'
        }
    },
    'embedder': {
        'provider': 'ollama',
        'config': {
            'model': 'nomic-embed-text',
            'ollama_base_url': 'http://localhost:11434'
        }
    },
    'vector_store': {
        'provider': 'qdrant',
        'config': {
            'collection_name': 'sim_ai_memories',
            'embedding_model_dims': 768  # nomic-embed-text dimension
        }
    }
}


def get_mem0_config():
    """Return the Mem0 configuration dict."""
    return MEM0_CONFIG.copy()


def create_memory():
    """Create and return a configured Mem0 Memory instance."""
    return Memory.from_config(MEM0_CONFIG)


if __name__ == "__main__":
    # Test the configuration
    print("Testing Mem0 configuration...")
    m = create_memory()

    # Add test memory
    result = m.add(
        "Test memory from sim-ai config validation",
        user_id="sim-ai-test"
    )
    print(f"Add result: {result}")

    # Search
    search = m.search("sim-ai config", user_id="sim-ai-test")
    print(f"Search found {len(search.get('results', []))} results")

    print("Configuration validated successfully!")
