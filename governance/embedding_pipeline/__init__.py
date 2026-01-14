"""
Embedding Pipeline Package.

Per GAP-FILE-021: Split from monolithic embedding_pipeline.py (476 lines)
Per DOC-SIZE-01-v1: Files under 400 lines

Maintains backward compatibility by re-exporting all public symbols.

Modules:
    - pipeline: Core EmbeddingPipeline class and factory
    - chunking: Content chunking utilities

Created: 2026-01-14
"""

# Re-export for backward compatibility
from .pipeline import EmbeddingPipeline, create_embedding_pipeline
from .chunking import chunk_content, truncate_content

__all__ = [
    "EmbeddingPipeline",
    "create_embedding_pipeline",
    "chunk_content",
    "truncate_content",
]
