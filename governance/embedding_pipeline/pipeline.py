"""Embedding Pipeline Core (P7.2). Per GAP-FILE-021, DOC-SIZE-01-v1."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

from governance.vector_store import (
    VectorStore,
    VectorDocument,
    EmbeddingGenerator,
    create_vector_from_rule,
    create_vector_from_decision,
    create_vector_from_session,
)
from governance.embedding_config import create_embedding_generator
from governance.compat import (
    governance_query_rules,
    governance_list_decisions,
    governance_list_sessions,
    governance_get_session,
)

from .chunking import chunk_content, truncate_content

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

class EmbeddingPipeline:
    """Pipeline for generating and storing embeddings (rules, decisions, sessions)."""

    def __init__(self, embedding_generator: Optional[EmbeddingGenerator] = None,
                 vector_store: Optional[VectorStore] = None, chunk_size: int = 2000):
        """Initialize embedding pipeline. Per GAP-EMBED-001: Default uses environment config."""
        self.generator = embedding_generator or create_embedding_generator()
        self.store = vector_store or VectorStore()
        self.chunk_size = chunk_size

    def embed_rule(self, rule_id: str, rule_content: str, directive: Optional[str] = None) -> VectorDocument:
        """Embed a single rule."""
        full_content = f"{rule_id}: {rule_content}"
        if directive:
            full_content += f" | Directive: {directive}"

        return create_vector_from_rule(rule_id, full_content, self.generator)

    def embed_rules(self) -> List[VectorDocument]:
        """Embed all rules from TypeDB."""
        try:
            result = json.loads(governance_query_rules())

            if isinstance(result, dict) and 'error' in result:
                logger.warning(f"Could not fetch rules: {result['error']}")
                return []

            rules = result if isinstance(result, list) else result.get('rules', [])

            docs = []
            for rule in rules:
                rule_id = rule.get('id') or rule.get('rule_id', 'UNKNOWN')
                name = rule.get('name') or rule.get('title', '')
                directive = rule.get('directive', '')

                doc = self.embed_rule(rule_id, name, directive)
                docs.append(doc)

            return docs

        except Exception as e:
            logger.error(f"Error embedding rules: {e}")
            return []

    def embed_and_store_rule(self, rule_id: str, rule_content: str) -> VectorDocument:
        """Embed and store a rule."""
        doc = self.embed_rule(rule_id, rule_content)
        self.store_embedding(doc)
        return doc

    def embed_decision(self, decision_id: str, decision_content: str) -> VectorDocument:
        """Embed a single decision."""
        return create_vector_from_decision(decision_id, decision_content, self.generator)

    def embed_decisions(self) -> List[VectorDocument]:
        """Embed all decisions from evidence dir."""
        try:
            result = json.loads(governance_list_decisions())

            # BUG-201-EMBED-001: Guard against list result (no .get() on list)
            if isinstance(result, dict) and 'error' in result:
                logger.warning(f"Could not fetch decisions: {result['error']}")
                return []

            decisions = result.get('decisions', []) if isinstance(result, dict) else result if isinstance(result, list) else []

            docs = []
            for decision in decisions:
                decision_id = decision.get('decision_id', 'UNKNOWN')
                name = decision.get('name', '')
                content = decision.get('context', name)

                doc = self.embed_decision(decision_id, f"{name}: {content}")
                docs.append(doc)

            return docs

        except Exception as e:
            logger.error(f"Error embedding decisions: {e}")
            return []

    def embed_session(self, session_id: str, session_content: str) -> VectorDocument:
        """Embed a single session (truncated to chunk_size)."""
        content = truncate_content(session_content, self.chunk_size)
        return create_vector_from_session(session_id, content, self.generator)

    def embed_session_chunked(self, session_id: str, session_content: str) -> List[VectorDocument]:
        """Embed a session in chunks."""
        docs = []
        chunks = chunk_content(session_content, self.chunk_size)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{session_id}_chunk_{i}"
            doc = create_vector_from_session(chunk_id, chunk, self.generator)
            doc.source = session_id
            docs.append(doc)

        return docs

    def embed_sessions(self, limit: int = 50) -> List[VectorDocument]:
        """Embed sessions from evidence dir."""
        try:
            result = json.loads(governance_list_sessions(limit=limit))

            # BUG-201-EMBED-002: Guard against list result (no .get() on list)
            if isinstance(result, dict) and 'error' in result:
                logger.warning(f"Could not fetch sessions: {result['error']}")
                return []

            sessions = result.get('sessions', []) if isinstance(result, dict) else result if isinstance(result, list) else []

            docs = []
            for session in sessions:
                session_id = session.get('session_id', 'UNKNOWN')
                # BUG-250-PIP-001: Catch per-session errors to avoid aborting entire loop
                # BUG-338-PIP-001: Separate exception catches; (JSONDecodeError, Exception)
                # was tautological — Exception subsumes JSONDecodeError
                try:
                    session_result = json.loads(governance_get_session(session_id))
                    content = session_result.get('content', '')
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse session {session_id} JSON: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to fetch session {session_id}: {e}")
                    continue

                if content:
                    doc = self.embed_session(session_id, content)
                    docs.append(doc)

            return docs

        except Exception as e:
            logger.error(f"Error embedding sessions: {e}")
            return []

    def store_embedding(self, doc: VectorDocument) -> bool:
        """Store embedding in vector store.

        BUG-338-PIP-002: Use public insert() API when connected; fall back to
        cache-only when TypeDB is unavailable. Previous code always wrote to
        _cache directly, so embeddings were never persisted to TypeDB.
        """
        if self.store._connected:
            return self.store.insert(doc)
        # Fallback: cache-only when store is not connected
        self.store._cache[doc.id] = doc
        return True

    def store_embeddings(self, docs: List[VectorDocument]) -> int:
        """Store multiple embeddings."""
        count = 0
        for doc in docs:
            if self.store_embedding(doc):
                count += 1
        return count

    def needs_update(self, source_id: str) -> bool:
        """Check if source needs embedding update."""
        for doc in self.store._cache.values():
            if doc.source == source_id:
                return False
        return True

    def get_embedded_sources(self) -> List[str]:
        """Get list of already embedded sources."""
        # BUG-232-LOG-002: Deduplicate sources (chunked sessions produce N entries per source)
        return list({doc.source for doc in self.store._cache.values()})

    def run_full_pipeline(self, dry_run: bool = False) -> Dict[str, Any]:
        """Run complete embedding pipeline."""
        logger.info("Starting embedding pipeline...")

        logger.info("Embedding rules...")
        rule_docs = self.embed_rules()
        if not dry_run:
            self.store_embeddings(rule_docs)
        logger.info(f"Embedded {len(rule_docs)} rules")

        logger.info("Embedding decisions...")
        decision_docs = self.embed_decisions()
        if not dry_run:
            self.store_embeddings(decision_docs)
        logger.info(f"Embedded {len(decision_docs)} decisions")

        logger.info("Embedding sessions...")
        session_docs = self.embed_sessions(limit=20)
        if not dry_run:
            self.store_embeddings(session_docs)
        logger.info(f"Embedded {len(session_docs)} sessions")

        total = len(rule_docs) + len(decision_docs) + len(session_docs)
        logger.info(f"Pipeline complete: {total} total embeddings")

        return {
            'rules': len(rule_docs),
            'decisions': len(decision_docs),
            'sessions': len(session_docs),
            'total': total,
            'dry_run': dry_run
        }

def create_embedding_pipeline(use_mock: Optional[bool] = None, dimension: int = 384,
                              ollama_host: str = "localhost", ollama_port: int = 11434) -> EmbeddingPipeline:
    """Factory function to create embedding pipeline. Per GAP-EMBED-001."""
    generator = create_embedding_generator(use_mock=use_mock, dimension=dimension)
    return EmbeddingPipeline(embedding_generator=generator)

__all__ = ["EmbeddingPipeline", "create_embedding_pipeline"]
