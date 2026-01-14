"""
Chunking Utilities for Embedding Pipeline.

Per GAP-FILE-021: Extracted from embedding_pipeline.py
Per DOC-SIZE-01-v1: Files under 400 lines

Functions for splitting long content into manageable chunks
for embedding generation.

Created: 2026-01-14
"""

from typing import List


def chunk_content(content: str, chunk_size: int = 2000) -> List[str]:
    """
    Split content into chunks for embedding.

    Splits at line boundaries to preserve context.
    If a single line exceeds chunk_size, it will be in its own chunk.

    Args:
        content: Content to chunk
        chunk_size: Maximum characters per chunk (default: 2000)

    Returns:
        List of chunks, each <= chunk_size characters
        (except single lines that exceed limit)
    """
    if not content:
        return [""]

    if len(content) <= chunk_size:
        return [content]

    chunks = []
    current_chunk = ""

    for line in content.split('\n'):
        # If adding this line would exceed limit
        if len(current_chunk) + len(line) + 1 > chunk_size:
            # Save current chunk if not empty
            if current_chunk:
                chunks.append(current_chunk)
            # Start new chunk with this line
            current_chunk = line
        else:
            # Add line to current chunk
            if current_chunk:
                current_chunk += '\n' + line
            else:
                current_chunk = line

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [content]


def truncate_content(content: str, max_length: int = 2000) -> str:
    """
    Truncate content to max_length characters.

    Args:
        content: Content to truncate
        max_length: Maximum characters

    Returns:
        Truncated content
    """
    if len(content) <= max_length:
        return content
    return content[:max_length]


__all__ = ["chunk_content", "truncate_content"]
