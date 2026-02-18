"""
Evidence Search MCP Tools
=========================
Semantic and keyword search across evidence artifacts.

Per RULE-012: DSP Semantic Code Structure
Per GAP-FILE-008: Extracted from evidence.py
Per MCP-NAMING-01-v1: Compact domain-based naming

Tools:
- evidence_search: Semantic search across all evidence

Created: 2024-12-28
"""

import glob
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from .common import EVIDENCE_DIR, DOCS_DIR
from governance.mcp_tools.common import format_mcp_result


def register_search_tools(mcp) -> None:
    """Register search-related MCP tools."""

    @mcp.tool()
    def evidence_search(
        query: str,
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> str:
        """
        Semantic search across all evidence artifacts.

        Uses vector store for semantic search with keyword fallback.

        Args:
            query: Search query (e.g., "authentication security rules")
            top_k: Number of results to return (default 5)
            source_type: Filter by type (session, decision, rule)

        Returns:
            JSON array of matching evidence with relevance scores
        """
        # Try to use vector store for semantic search
        # Per GAP-EMBED-001: Use env-configured embedding generator
        semantic_results = []
        try:
            from governance.vector_store import VectorStore
            from governance.embedding_config import create_embedding_generator

            store = VectorStore()
            generator = create_embedding_generator()

            # Connect if possible
            if store.connect():
                query_embedding = generator.generate(query)
                semantic_results = store.search(query_embedding, top_k=top_k, source_type=source_type)
                store.close()

                # Only return semantic results if we found something
                if semantic_results:
                    return format_mcp_result({
                        "query": query,
                        "results": [
                            {
                                "source": r.source,
                                "source_type": r.source_type,
                                "score": round(r.score, 4),
                                "content": r.content[:200] + "..." if len(r.content) > 200 else r.content
                            }
                            for r in semantic_results
                        ],
                        "count": len(semantic_results),
                        "search_method": "semantic_vector"
                    })
        except Exception as e:
            # BUG-477-SRC-1: Sanitize debug/info logger
            logger.debug(f"Semantic search failed, falling back to keyword: {type(e).__name__}")

        # Fall back to keyword search
        results = []
        query_lower = query.lower()

        # Search evidence files
        for pattern in [EVIDENCE_DIR / "*.md", DOCS_DIR / "rules/*.md"]:
            for filepath in glob.glob(str(pattern)):
                try:
                    path = Path(filepath)
                    content = path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        # Count occurrences as relevance score
                        score = content.lower().count(query_lower)
                        results.append({
                            "source": path.stem,
                            "source_type": "evidence" if "evidence" in str(path) else "rule",
                            "score": score,
                            "path": str(filepath),
                            "content": content[:200] + "..."
                        })
                except Exception as e:
                    # BUG-477-SRC-2: Sanitize debug/info logger
                    logger.debug(f"Failed to search evidence file {filepath}: {type(e).__name__}")
                    continue

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return format_mcp_result({
            "query": query,
            "results": results[:top_k],
            "count": len(results[:top_k]),
            "search_method": "keyword_fallback"
        })
