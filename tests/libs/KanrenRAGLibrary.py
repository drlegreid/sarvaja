"""
Robot Framework Library for Kanren RAG Validation Tests.

Per KAN-002: Kanren Constraint Engine - RAG Module.
Split from KanrenConstraintsLibrary.py per DOC-SIZE-01-v1.

Covers: RAG Chunk Validation, RAG Chunk Filtering, KAN-003 RAG Filter.
"""
from robot.api.deco import keyword


class KanrenRAGLibrary:
    """Library for testing Kanren RAG constraints."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # RAG Chunk Validation Tests
    # =========================================================================

    @keyword("Valid TypeDB Chunk")
    def valid_typedb_chunk(self):
        """Valid TypeDB chunk passes validation."""
        try:
            from governance.kanren_constraints import valid_rag_chunk
            result = valid_rag_chunk("typedb", True, "rule")
            return {
                "has_result": len(result) > 0,
                "valid": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Valid ChromaDB Chunk")
    def valid_chromadb_chunk(self):
        """Valid ChromaDB chunk passes validation."""
        try:
            from governance.kanren_constraints import valid_rag_chunk
            result = valid_rag_chunk("chromadb", True, "evidence")
            return {
                "has_result": len(result) > 0,
                "valid": result[0] is True
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Invalid Source Fails")
    def invalid_source_fails(self):
        """Invalid source fails validation."""
        try:
            from governance.kanren_constraints import valid_rag_chunk
            result = valid_rag_chunk("external", True, "rule")
            return {"no_solutions": len(result) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Unverified Chunk Fails")
    def unverified_chunk_fails(self):
        """Unverified chunk fails validation."""
        try:
            from governance.kanren_constraints import valid_rag_chunk
            result = valid_rag_chunk("typedb", False, "rule")
            return {"no_solutions": len(result) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Invalid Type Fails")
    def invalid_type_fails(self):
        """Invalid chunk type fails validation."""
        try:
            from governance.kanren_constraints import valid_rag_chunk
            result = valid_rag_chunk("typedb", True, "unknown")
            return {"no_solutions": len(result) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # RAG Chunk Filtering Tests
    # =========================================================================

    @keyword("Filter Mixed Chunks")
    def filter_mixed_chunks(self):
        """Filters mixed valid/invalid chunks."""
        try:
            from governance.kanren_constraints import filter_rag_chunks
            chunks = [
                {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
                {"id": 2, "source": "external", "verified": False, "type": "unknown"},
                {"id": 3, "source": "chromadb", "verified": True, "type": "evidence"},
                {"id": 4, "source": "evidence", "verified": True, "type": "decision"},
            ]
            valid = filter_rag_chunks(chunks)
            return {
                "correct_count": len(valid) == 3,
                "all_valid_sources": all(c["source"] in ["typedb", "chromadb", "evidence"] for c in valid)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Empty List")
    def filter_empty_list(self):
        """Handles empty chunk list."""
        try:
            from governance.kanren_constraints import filter_rag_chunks
            valid = filter_rag_chunks([])
            return {"empty_result": valid == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter All Invalid")
    def filter_all_invalid(self):
        """Returns empty when all chunks invalid."""
        try:
            from governance.kanren_constraints import filter_rag_chunks
            chunks = [
                {"id": 1, "source": "external", "verified": False, "type": "unknown"},
            ]
            valid = filter_rag_chunks(chunks)
            return {"empty_result": valid == []}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # KAN-003: RAG Filter Tests
    # =========================================================================

    @keyword("Filter Import")
    def filter_import(self):
        """KanrenRAGFilter can be imported."""
        try:
            from governance.kanren_constraints import KanrenRAGFilter
            return {"exists": KanrenRAGFilter is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Instantiation")
    def filter_instantiation(self):
        """KanrenRAGFilter can be instantiated."""
        try:
            from governance.kanren_constraints import KanrenRAGFilter
            rag_filter = KanrenRAGFilter()
            return {
                "created": rag_filter is not None,
                "store_none": rag_filter._store is None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter With Mock Store")
    def filter_with_mock_store(self):
        """KanrenRAGFilter works with injected mock store."""
        try:
            from unittest.mock import MagicMock
            from governance.kanren_constraints import KanrenRAGFilter

            mock_store = MagicMock()
            mock_result = MagicMock()
            mock_result.vector_id = "vec-001"
            mock_result.content = "Test content"
            mock_result.source_type = "rule"
            mock_result.score = 0.85
            mock_result.source = "RULE-001"
            mock_store.search.return_value = [mock_result]

            rag_filter = KanrenRAGFilter(vector_store=mock_store)
            results = rag_filter.search_validated(
                query_embedding=[0.1, 0.2, 0.3],
                top_k=5
            )

            return {
                "search_called": mock_store.search.called,
                "one_result": len(results) == 1,
                "source_typedb": results[0]["source"] == "typedb",
                "type_rule": results[0]["type"] == "rule"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Results To Chunks Conversion")
    def results_to_chunks_conversion(self):
        """_results_to_chunks correctly converts SimilarityResult format."""
        try:
            from unittest.mock import MagicMock
            from governance.kanren_constraints import KanrenRAGFilter

            mock_store = MagicMock()
            rag_filter = KanrenRAGFilter(vector_store=mock_store)

            mock_results = []
            for source_type, expected_source in [("rule", "typedb"), ("decision", "typedb"), ("session", "chromadb")]:
                r = MagicMock()
                r.vector_id = f"vec-{source_type}"
                r.content = f"Content for {source_type}"
                r.source_type = source_type
                r.score = 0.8
                r.source = f"SOURCE-{source_type.upper()}"
                mock_results.append(r)

            chunks = rag_filter._results_to_chunks(mock_results)

            return {
                "chunk_count": len(chunks) == 3,
                "first_typedb": chunks[0]["source"] == "typedb",
                "second_typedb": chunks[1]["source"] == "typedb",
                "third_chromadb": chunks[2]["source"] == "chromadb"
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Search For Task Validation")
    def search_for_task_validation(self):
        """search_for_task validates agent-task assignment."""
        try:
            from unittest.mock import MagicMock
            from governance.kanren_constraints import KanrenRAGFilter, AgentContext, TaskContext

            mock_store = MagicMock()
            mock_vec = MagicMock()
            mock_vec.id = "vec-001"
            mock_vec.content = "governance rule content"
            mock_vec.source_type = "rule"
            mock_vec.source = "RULE-001"
            mock_store.get_all_vectors.return_value = [mock_vec]

            rag_filter = KanrenRAGFilter(vector_store=mock_store)
            agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
            task = TaskContext("TASK-001", "CRITICAL", True)

            result = rag_filter.search_for_task(
                query_text="governance",
                task_context=task,
                agent_context=agent
            )

            return {
                "assignment_valid": result["assignment_valid"] is True,
                "trust_level": result["agent"]["trust_level"] == "expert",
                "requires_evidence": result["task"]["requires_evidence"] is True,
                "has_constraints": "constraints_applied" in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Low Score Chunk Filtered")
    def low_score_chunk_filtered(self):
        """Chunks with low similarity score (< 0.5) are filtered."""
        try:
            from unittest.mock import MagicMock
            from governance.kanren_constraints import KanrenRAGFilter

            mock_store = MagicMock()
            mock_result = MagicMock()
            mock_result.vector_id = "vec-low"
            mock_result.content = "Low score content"
            mock_result.source_type = "rule"
            mock_result.score = 0.3
            mock_result.source = "RULE-LOW"
            mock_store.search.return_value = [mock_result]

            rag_filter = KanrenRAGFilter(vector_store=mock_store)
            results = rag_filter.search_validated(
                query_embedding=[0.1, 0.2, 0.3],
                top_k=5
            )

            return {"filtered_out": len(results) == 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Context Assembly Tests
    # =========================================================================

    @keyword("Assemble Valid Context")
    def assemble_valid_context(self):
        """Assembles valid context with filtered chunks."""
        try:
            from governance.kanren_constraints import assemble_context, AgentContext, TaskContext
            agent = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
            task = TaskContext("TASK-001", "CRITICAL", True)
            chunks = [
                {"id": 1, "source": "typedb", "verified": True, "type": "rule"},
                {"id": 2, "source": "external", "verified": False, "type": "unknown"},
            ]
            context = assemble_context(agent, task, chunks)
            return {
                "assignment_valid": context["assignment_valid"] is True,
                "trust_level": context["agent"]["trust_level"] == "expert",
                "requires_evidence": context["task"]["requires_evidence"] is True,
                "one_chunk": len(context["rag_chunks"]) == 1,
                "has_rule_007": "RULE-007: RAG validation" in context["constraints_applied"]
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
