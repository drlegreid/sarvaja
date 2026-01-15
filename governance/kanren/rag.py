"""
RAG Chunk Validation (RULE-007).

Per RULE-007: MCP Usage Protocol - verify data sources.
"""

from typing import Dict, List, Tuple
from kanren import run, var, eq, lall, membero


# Allowed sources for RAG chunks
ALLOWED_SOURCES = ['typedb', 'chromadb', 'evidence', 'session', 'rule']

# Trusted chunk types
TRUSTED_TYPES = ['rule', 'decision', 'evidence', 'task']


def valid_rag_chunk(source: str, verified: bool, chunk_type: str) -> Tuple:
    """
    Validate RAG chunk before including in LLM context.

    Per RULE-007: MCP Usage Protocol - verify data sources.
    """
    x = var()
    return run(1, x, lall(
        membero(source, ALLOWED_SOURCES),
        eq(verified, True),
        membero(chunk_type, TRUSTED_TYPES),
        eq(x, True)
    ))


def filter_rag_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Filter RAG chunks using Kanren constraints.

    Returns only chunks that pass governance validation.
    """
    valid_chunks = []
    for chunk in chunks:
        result = valid_rag_chunk(
            chunk.get('source', ''),
            chunk.get('verified', False),
            chunk.get('type', '')
        )
        if result and result[0]:
            valid_chunks.append(chunk)
    return valid_chunks
