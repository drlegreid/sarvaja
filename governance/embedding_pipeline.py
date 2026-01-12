"""
Embedding Pipeline (P7.2)
Created: 2024-12-25

Pipeline for generating and storing embeddings for:
- Rules (from TypeDB)
- Decisions (from evidence dir)
- Sessions (from evidence dir)

Per DECISION-003: TypeDB-First Strategy
Per RULE-010: Evidence-Based Wisdom

Dependencies:
    pip install typedb-driver==2.29.2
"""

import json
import glob
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from governance.vector_store import (
    VectorStore,
    VectorDocument,
    EmbeddingGenerator,
    MockEmbeddings,
    OllamaEmbeddings,
    LiteLLMEmbeddings,
    create_vector_from_rule,
    create_vector_from_decision,
    create_vector_from_session,
)
from governance.compat import (
    governance_query_rules,
    governance_list_decisions,
    governance_list_sessions,
    governance_get_session,
)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "evidence"


class EmbeddingPipeline:
    """
    Pipeline for generating and storing embeddings.

    Workflow:
    1. Fetch artifacts (rules, decisions, sessions)
    2. Generate embeddings using configured generator
    3. Store in VectorStore (cache + optional TypeDB)

    Example:
        pipeline = EmbeddingPipeline()
        result = pipeline.run_full_pipeline()
        print(f"Embedded {result['total']} artifacts")
    """

    def __init__(
        self,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        vector_store: Optional[VectorStore] = None,
        chunk_size: int = 2000
    ):
        """
        Initialize embedding pipeline.

        Args:
            embedding_generator: Generator for embeddings (default: MockEmbeddings)
            vector_store: Store for embeddings (default: new VectorStore)
            chunk_size: Max characters per chunk for long content
        """
        self.generator = embedding_generator or MockEmbeddings(dimension=384)
        self.store = vector_store or VectorStore()
        self.chunk_size = chunk_size

    # =========================================================================
    # RULE EMBEDDINGS
    # =========================================================================

    def embed_rule(
        self,
        rule_id: str,
        rule_content: str,
        directive: Optional[str] = None
    ) -> VectorDocument:
        """
        Embed a single rule.

        Args:
            rule_id: Rule ID
            rule_content: Rule name/description
            directive: Optional directive text

        Returns:
            VectorDocument with embedding
        """
        # Combine content for embedding
        full_content = f"{rule_id}: {rule_content}"
        if directive:
            full_content += f" | Directive: {directive}"

        return create_vector_from_rule(rule_id, full_content, self.generator)

    def embed_rules(self) -> List[VectorDocument]:
        """
        Embed all rules from TypeDB.

        Returns:
            List of VectorDocuments
        """
        try:
            result = json.loads(governance_query_rules())

            # Handle both list and dict with 'error'
            if isinstance(result, dict) and 'error' in result:
                print(f"Warning: Could not fetch rules: {result['error']}")
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
            print(f"Error embedding rules: {e}")
            return []

    def embed_and_store_rule(self, rule_id: str, rule_content: str) -> VectorDocument:
        """Embed and store a rule."""
        doc = self.embed_rule(rule_id, rule_content)
        self.store_embedding(doc)
        return doc

    # =========================================================================
    # DECISION EMBEDDINGS
    # =========================================================================

    def embed_decision(self, decision_id: str, decision_content: str) -> VectorDocument:
        """
        Embed a single decision.

        Args:
            decision_id: Decision ID
            decision_content: Decision content/name

        Returns:
            VectorDocument with embedding
        """
        return create_vector_from_decision(decision_id, decision_content, self.generator)

    def embed_decisions(self) -> List[VectorDocument]:
        """
        Embed all decisions from evidence dir.

        Returns:
            List of VectorDocuments
        """
        try:
            result = json.loads(governance_list_decisions())

            if 'error' in result:
                print(f"Warning: Could not fetch decisions: {result['error']}")
                return []

            decisions = result.get('decisions', [])

            docs = []
            for decision in decisions:
                decision_id = decision.get('decision_id', 'UNKNOWN')
                name = decision.get('name', '')
                content = decision.get('context', name)

                doc = self.embed_decision(decision_id, f"{name}: {content}")
                docs.append(doc)

            return docs

        except Exception as e:
            print(f"Error embedding decisions: {e}")
            return []

    # =========================================================================
    # SESSION EMBEDDINGS
    # =========================================================================

    def embed_session(self, session_id: str, session_content: str) -> VectorDocument:
        """
        Embed a single session.

        Args:
            session_id: Session ID
            session_content: Session content

        Returns:
            VectorDocument with embedding
        """
        # Truncate to chunk size for single embedding
        if len(session_content) > self.chunk_size:
            session_content = session_content[:self.chunk_size]

        return create_vector_from_session(session_id, session_content, self.generator)

    def embed_session_chunked(
        self,
        session_id: str,
        session_content: str
    ) -> List[VectorDocument]:
        """
        Embed a session in chunks.

        Args:
            session_id: Session ID
            session_content: Full session content

        Returns:
            List of VectorDocuments (one per chunk)
        """
        docs = []
        chunks = self._chunk_content(session_content)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{session_id}_chunk_{i}"
            doc = create_vector_from_session(chunk_id, chunk, self.generator)
            doc.source = session_id  # Keep original session_id as source
            docs.append(doc)

        return docs

    def _chunk_content(self, content: str) -> List[str]:
        """
        Split content into chunks.

        Args:
            content: Content to chunk

        Returns:
            List of chunks
        """
        chunks = []
        current_chunk = ""

        for line in content.split('\n'):
            if len(current_chunk) + len(line) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += '\n' + line if current_chunk else line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks if chunks else [content]

    def embed_sessions(self, limit: int = 50) -> List[VectorDocument]:
        """
        Embed sessions from evidence dir.

        Args:
            limit: Max sessions to embed

        Returns:
            List of VectorDocuments
        """
        try:
            result = json.loads(governance_list_sessions(limit=limit))

            if 'error' in result:
                print(f"Warning: Could not fetch sessions: {result['error']}")
                return []

            sessions = result.get('sessions', [])

            docs = []
            for session in sessions:
                session_id = session.get('session_id', 'UNKNOWN')

                # Get full session content
                session_result = json.loads(governance_get_session(session_id))
                content = session_result.get('content', '')

                if content:
                    doc = self.embed_session(session_id, content)
                    docs.append(doc)

            return docs

        except Exception as e:
            print(f"Error embedding sessions: {e}")
            return []

    # =========================================================================
    # STORAGE
    # =========================================================================

    def store_embedding(self, doc: VectorDocument) -> bool:
        """
        Store embedding in vector store.

        Args:
            doc: VectorDocument to store

        Returns:
            True if stored successfully
        """
        self.store._cache[doc.id] = doc
        return True

    def store_embeddings(self, docs: List[VectorDocument]) -> int:
        """
        Store multiple embeddings.

        Args:
            docs: Documents to store

        Returns:
            Number stored
        """
        count = 0
        for doc in docs:
            if self.store_embedding(doc):
                count += 1
        return count

    # =========================================================================
    # INCREMENTAL UPDATES
    # =========================================================================

    def needs_update(self, source_id: str) -> bool:
        """
        Check if source needs embedding update.

        Args:
            source_id: Source identifier

        Returns:
            True if needs update
        """
        # Check cache directly without triggering TypeDB connection
        for doc in self.store._cache.values():
            if doc.source == source_id:
                return False
        return True

    def get_embedded_sources(self) -> List[str]:
        """
        Get list of already embedded sources.

        Returns:
            List of source IDs
        """
        return [doc.source for doc in self.store._cache.values()]

    # =========================================================================
    # FULL PIPELINE
    # =========================================================================

    def run_full_pipeline(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run complete embedding pipeline.

        Args:
            dry_run: If True, don't store embeddings

        Returns:
            Statistics dict
        """
        print("Starting embedding pipeline...")

        # Embed rules
        print("Embedding rules...")
        rule_docs = self.embed_rules()
        if not dry_run:
            self.store_embeddings(rule_docs)
        print(f"  Embedded {len(rule_docs)} rules")

        # Embed decisions
        print("Embedding decisions...")
        decision_docs = self.embed_decisions()
        if not dry_run:
            self.store_embeddings(decision_docs)
        print(f"  Embedded {len(decision_docs)} decisions")

        # Embed sessions
        print("Embedding sessions...")
        session_docs = self.embed_sessions(limit=20)
        if not dry_run:
            self.store_embeddings(session_docs)
        print(f"  Embedded {len(session_docs)} sessions")

        total = len(rule_docs) + len(decision_docs) + len(session_docs)
        print(f"Pipeline complete: {total} total embeddings")

        return {
            'rules': len(rule_docs),
            'decisions': len(decision_docs),
            'sessions': len(session_docs),
            'total': total,
            'dry_run': dry_run
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_embedding_pipeline(
    use_mock: bool = True,
    dimension: int = 384,
    ollama_host: str = "localhost",
    ollama_port: int = 11434
) -> EmbeddingPipeline:
    """
    Factory function to create embedding pipeline.

    Args:
        use_mock: Use mock embeddings (default True for testing)
        dimension: Embedding dimension
        ollama_host: Ollama host for real embeddings
        ollama_port: Ollama port

    Returns:
        EmbeddingPipeline instance
    """
    if use_mock:
        generator = MockEmbeddings(dimension=dimension)
    else:
        generator = OllamaEmbeddings(host=ollama_host, port=ollama_port)

    return EmbeddingPipeline(embedding_generator=generator)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for embedding pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Pipeline")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Don't store embeddings")
    parser.add_argument("--mock", "-m", action="store_true", default=True, help="Use mock embeddings")
    parser.add_argument("--dimension", "-d", type=int, default=384, help="Embedding dimension")
    args = parser.parse_args()

    pipeline = create_embedding_pipeline(use_mock=args.mock, dimension=args.dimension)
    result = pipeline.run_full_pipeline(dry_run=args.dry_run)

    print("\n=== Pipeline Results ===")
    print(f"Rules:     {result['rules']}")
    print(f"Decisions: {result['decisions']}")
    print(f"Sessions:  {result['sessions']}")
    print(f"Total:     {result['total']}")
    print(f"Dry Run:   {result['dry_run']}")


if __name__ == "__main__":
    main()
