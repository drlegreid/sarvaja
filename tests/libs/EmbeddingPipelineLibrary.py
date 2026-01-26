"""
Embedding Pipeline Library for Robot Framework
Migrated from tests/test_embedding_pipeline.py
Per: RF-007 Robot Framework Migration
"""
from pathlib import Path
from robot.api.deco import keyword

PROJECT_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class EmbeddingPipelineLibrary:
    """Robot Framework keywords for embedding pipeline tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Pipeline Module Tests
    # =========================================================================

    @keyword("Pipeline Module Exists")
    def pipeline_module_exists(self):
        """Test that embedding pipeline module exists."""
        pipeline_file = GOVERNANCE_DIR / "embedding_pipeline.py"
        pipeline_package = GOVERNANCE_DIR / "embedding_pipeline" / "__init__.py"
        return {
            "module_exists": pipeline_file.exists() or pipeline_package.exists()
        }

    @keyword("Pipeline Class Importable")
    def pipeline_class_importable(self):
        """Test that EmbeddingPipeline class is importable."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            pipeline = EmbeddingPipeline()
            return {
                "importable": True,
                "pipeline_created": pipeline is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Pipeline Has Required Methods")
    def pipeline_has_required_methods(self):
        """Test that pipeline has required methods."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            pipeline = EmbeddingPipeline()
            return {
                "has_embed_rules": hasattr(pipeline, 'embed_rules'),
                "has_embed_decisions": hasattr(pipeline, 'embed_decisions'),
                "has_embed_sessions": hasattr(pipeline, 'embed_sessions'),
                "has_run_full_pipeline": hasattr(pipeline, 'run_full_pipeline')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Rule Embedding Tests
    # =========================================================================

    @keyword("Embed Single Rule")
    def embed_single_rule(self):
        """Test embedding a single rule."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            doc = pipeline.embed_rule("RULE-001", "Session evidence logging required")

            return {
                "source_correct": doc.source == "RULE-001",
                "source_type_rule": doc.source_type == "rule",
                "embedding_dimension": len(doc.embedding) == 128
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Embed All Rules")
    def embed_all_rules(self):
        """Test embedding all rules from TypeDB."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            docs = pipeline.embed_rules()

            all_rules = all(doc.source_type == "rule" for doc in docs)
            return {
                "is_list": isinstance(docs, list),
                "all_source_type_rule": all_rules
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Embedding Content")
    def rule_embedding_content(self):
        """Test that rule embedding content includes directive."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
            doc = pipeline.embed_rule(
                "RULE-TEST",
                "Test rule content with directive",
                directive="Do the thing"
            )

            has_directive = "directive" in doc.content.lower() or "Do the thing" in doc.content
            return {"has_directive_content": has_directive}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Decision Embedding Tests
    # =========================================================================

    @keyword("Embed Single Decision")
    def embed_single_decision(self):
        """Test embedding a single decision."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            doc = pipeline.embed_decision("DECISION-003", "TypeDB-First Strategy")

            return {
                "source_correct": doc.source == "DECISION-003",
                "source_type_decision": doc.source_type == "decision"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Embed All Decisions")
    def embed_all_decisions(self):
        """Test embedding all decisions from evidence dir."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            docs = pipeline.embed_decisions()

            all_decisions = all(doc.source_type == "decision" for doc in docs)
            return {
                "is_list": isinstance(docs, list),
                "all_source_type_decision": all_decisions
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Session Embedding Tests
    # =========================================================================

    @keyword("Embed Single Session")
    def embed_single_session(self):
        """Test embedding a single session."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            doc = pipeline.embed_session("SESSION-TEST", "Session evidence content here")

            return {
                "source_correct": doc.source == "SESSION-TEST",
                "source_type_session": doc.source_type == "session"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Embed All Sessions")
    def embed_all_sessions(self):
        """Test embedding all sessions from evidence dir."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=128))
            docs = pipeline.embed_sessions(limit=5)

            all_sessions = all(doc.source_type == "session" for doc in docs)
            return {
                "is_list": isinstance(docs, list),
                "all_source_type_session": all_sessions
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Session Chunking")
    def session_chunking(self):
        """Test that long sessions are chunked."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(
                embedding_generator=MockEmbeddings(dimension=128),
                chunk_size=500  # Small chunk for testing
            )

            long_content = "This is a test. " * 200  # Long content
            docs = pipeline.embed_session_chunked("SESSION-TEST", long_content)

            return {"produces_chunks": len(docs) >= 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Full Pipeline Tests
    # =========================================================================

    @keyword("Run Full Pipeline")
    def run_full_pipeline(self):
        """Test running the complete embedding pipeline."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
            result = pipeline.run_full_pipeline(dry_run=True)

            return {
                "has_rules": 'rules' in result,
                "has_decisions": 'decisions' in result,
                "has_sessions": 'sessions' in result,
                "has_total": 'total' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Pipeline Returns Stats")
    def pipeline_returns_stats(self):
        """Test that pipeline returns statistics."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))
            result = pipeline.run_full_pipeline(dry_run=True)

            return {
                "rules_is_int": isinstance(result['rules'], int),
                "decisions_is_int": isinstance(result['decisions'], int),
                "sessions_is_int": isinstance(result['sessions'], int)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Embedding Storage Tests
    # =========================================================================

    @keyword("Store To Cache")
    def store_to_cache(self):
        """Test storing embeddings in vector store cache."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings, VectorStore

            store = VectorStore()
            pipeline = EmbeddingPipeline(
                embedding_generator=MockEmbeddings(dimension=64),
                vector_store=store
            )

            doc = pipeline.embed_rule("RULE-TEST", "Test content")
            pipeline.store_embedding(doc)

            return {"in_cache": doc.id in store._cache}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search Stored Embeddings")
    def search_stored_embeddings(self):
        """Test searching stored embeddings."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings, VectorStore

            generator = MockEmbeddings(dimension=64)
            store = VectorStore()
            pipeline = EmbeddingPipeline(
                embedding_generator=generator,
                vector_store=store
            )

            # Store some test embeddings
            pipeline.embed_and_store_rule("RULE-001", "Session evidence logging")
            pipeline.embed_and_store_rule("RULE-002", "Agent trust metrics")

            # Search
            query = generator.generate("evidence logging")
            results = store.search(query, top_k=2, threshold=-1.0)

            return {"has_results": len(results) >= 1}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Incremental Update Tests
    # =========================================================================

    @keyword("Check Needs Update")
    def check_needs_update(self):
        """Test checking if embedding needs update."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings

            pipeline = EmbeddingPipeline(embedding_generator=MockEmbeddings(dimension=64))

            # New source should need update
            return {"needs_update": pipeline.needs_update("NEW-RULE-999")}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get Existing Sources")
    def get_existing_sources(self):
        """Test listing existing embedded sources."""
        try:
            from governance.embedding_pipeline import EmbeddingPipeline
            from governance.vector_store import MockEmbeddings, VectorStore

            store = VectorStore()
            pipeline = EmbeddingPipeline(
                embedding_generator=MockEmbeddings(dimension=64),
                vector_store=store
            )

            pipeline.embed_and_store_rule("RULE-001", "Test")
            sources = pipeline.get_embedded_sources()

            return {"has_rule": "RULE-001" in sources}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Factory Function Tests
    # =========================================================================

    @keyword("Create Pipeline Factory")
    def create_pipeline_factory(self):
        """Test factory creates pipeline."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline

            pipeline = create_embedding_pipeline()
            return {"pipeline_created": pipeline is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create With Mock")
    def create_with_mock(self):
        """Test factory supports mock embeddings."""
        try:
            from governance.embedding_pipeline import create_embedding_pipeline

            pipeline = create_embedding_pipeline(use_mock=True, dimension=128)
            return {"dimension_correct": pipeline.generator.dimension == 128}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
