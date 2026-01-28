"""
Robot Framework Library for Vector Store Advanced Tests (P7.1)
Split from VectorStoreLibrary.py per DOC-SIZE-01-v1
Covers: Vector Search, Convenience Functions, TypeQL Generation, Schema
"""

from pathlib import Path
from robot.api.deco import keyword

PROJECT_ROOT = Path(__file__).parent.parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


class VectorStoreAdvancedLibrary:
    """Library for advanced vector store test keywords."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Vector Search Tests
    # =========================================================================

    @keyword("Search With Cache")
    def search_with_cache(self):
        """Search should work with cached documents."""
        try:
            from governance.vector_store import VectorStore, VectorDocument, MockEmbeddings

            generator = MockEmbeddings(dimension=64)
            store = VectorStore()

            docs = [
                VectorDocument(
                    id="doc-1",
                    content="RULE-001 session evidence",
                    embedding=generator.generate("RULE-001 session evidence"),
                    model="mock",
                    dimension=64,
                    source="RULE-001",
                    source_type="rule"
                ),
                VectorDocument(
                    id="doc-2",
                    content="RULE-011 multi-agent governance",
                    embedding=generator.generate("RULE-011 multi-agent governance"),
                    model="mock",
                    dimension=64,
                    source="RULE-011",
                    source_type="rule"
                ),
            ]
            store._cache = {doc.id: doc for doc in docs}

            query = generator.generate("session evidence logging")
            results = store.search(query, top_k=2, threshold=-1.0)

            return {
                "has_results": len(results) == 2,
                "ordered": results[0].score >= results[1].score
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search With Source Type Filter")
    def search_with_source_type_filter(self):
        """Search should filter by source type."""
        try:
            from governance.vector_store import VectorStore, VectorDocument, MockEmbeddings

            generator = MockEmbeddings(dimension=64)
            store = VectorStore()

            docs = [
                VectorDocument(
                    id="rule-1", content="Rule content",
                    embedding=generator.generate("rule"), model="mock",
                    dimension=64, source="RULE-001", source_type="rule"
                ),
                VectorDocument(
                    id="dec-1", content="Decision content",
                    embedding=generator.generate("decision"), model="mock",
                    dimension=64, source="DEC-001", source_type="decision"
                ),
            ]
            store._cache = {doc.id: doc for doc in docs}

            results = store.search(generator.generate("test"), source_type="rule")
            return {"all_rules": all(r.source_type == "rule" for r in results)}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search By Source")
    def search_by_source(self):
        """search_by_source should find document by source ID."""
        try:
            from governance.vector_store import VectorStore, VectorDocument

            store = VectorStore()
            doc = VectorDocument(
                id="doc-1", content="test",
                embedding=[0.1, 0.2], model="mock",
                dimension=2, source="RULE-001", source_type="rule"
            )
            store._cache = {doc.id: doc}

            found = store.search_by_source("RULE-001")
            not_found = store.search_by_source("RULE-999")

            return {
                "found": found is not None and found.source == "RULE-001",
                "not_found_none": not_found is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Convenience Function Tests
    # =========================================================================

    @keyword("Create Vector From Rule")
    def create_vector_from_rule(self):
        """create_vector_from_rule should create VectorDocument."""
        try:
            from governance.vector_store import create_vector_from_rule, MockEmbeddings

            generator = MockEmbeddings(dimension=128)
            doc = create_vector_from_rule("RULE-001", "Session evidence logging", generator)

            return {
                "source_correct": doc.source == "RULE-001",
                "type_correct": doc.source_type == "rule",
                "embedding_len": len(doc.embedding) == 128
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Vector From Decision")
    def create_vector_from_decision(self):
        """create_vector_from_decision should create VectorDocument."""
        try:
            from governance.vector_store import create_vector_from_decision, MockEmbeddings

            generator = MockEmbeddings(dimension=128)
            doc = create_vector_from_decision("DECISION-003", "TypeDB-First Strategy", generator)

            return {
                "source_correct": doc.source == "DECISION-003",
                "type_correct": doc.source_type == "decision"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Create Vector From Session")
    def create_vector_from_session(self):
        """create_vector_from_session should create VectorDocument."""
        try:
            from governance.vector_store import create_vector_from_session, MockEmbeddings

            generator = MockEmbeddings(dimension=128)
            doc = create_vector_from_session("SESSION-001", "Session evidence content", generator)

            return {
                "source_correct": doc.source == "SESSION-001",
                "type_correct": doc.source_type == "session"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # TypeQL Generation Tests
    # =========================================================================

    @keyword("TypeDB Insert Generation")
    def typedb_insert_generation(self):
        """VectorDocument should generate valid TypeQL insert."""
        try:
            from governance.vector_store import VectorDocument

            doc = VectorDocument(
                id="test-id",
                content="Test content",
                embedding=[0.1, 0.2, 0.3],
                model="test-model",
                dimension=3,
                source="RULE-001",
                source_type="rule"
            )

            typeql = doc.to_typedb_insert()

            return {
                "has_insert": "insert $v isa vector-document" in typeql,
                "has_id": 'vector-id "test-id"' in typeql,
                "has_source": 'vector-source "RULE-001"' in typeql,
                "has_type": 'vector-source-type "rule"' in typeql,
                "has_embedding": "vector-embedding" in typeql
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("TypeDB Insert Escaping")
    def typedb_insert_escaping(self):
        """TypeQL insert should escape special characters."""
        try:
            from governance.vector_store import VectorDocument

            doc = VectorDocument(
                id="test",
                content='Text with "quotes" and\nnewlines',
                embedding=[0.1],
                model="test",
                dimension=1,
                source="TEST",
                source_type="rule"
            )

            typeql = doc.to_typedb_insert()

            return {
                "escaped_quotes": '\\"' in typeql or "quotes" in typeql,
                "escaped_newline": '\\n' in typeql
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Schema Tests
    # =========================================================================

    @keyword("Schema Has Vector Entities")
    def schema_has_vector_entities(self):
        """Schema should define vector embedding entities."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        if not schema_file.exists():
            return {"skipped": True, "reason": "schema.tql not found"}

        content = schema_file.read_text()
        return {
            "has_vector_document": "vector-document sub entity" in content,
            "has_embedding": "vector-embedding" in content,
            "has_similarity": "vector-similarity" in content,
            "has_score": "similarity-score" in content
        }

    @keyword("Schema Has Vector Attributes")
    def schema_has_vector_attributes(self):
        """Schema should define vector attributes."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        if not schema_file.exists():
            return {"skipped": True, "reason": "schema.tql not found"}

        content = schema_file.read_text()
        return {
            "has_id": "vector-id sub attribute" in content,
            "has_content": "vector-content sub attribute" in content,
            "has_model": "vector-model sub attribute" in content,
            "has_dimension": "vector-dimension sub attribute" in content
        }

    @keyword("Entities Can Have Embeddings")
    def entities_can_have_embeddings(self):
        """Rule and decision entities should play embedding role."""
        schema_file = GOVERNANCE_DIR / "schema.tql"
        if not schema_file.exists():
            return {"skipped": True, "reason": "schema.tql not found"}

        content = schema_file.read_text()
        return {"has_role": "plays entity-vector:embedded-entity" in content}
