"""Tests for Rule Dependency Graph — EPIC-RULES-V3-P2.

TDD: Written FIRST (RED), then implementation (GREEN), then refactor.

Covers:
- DependencyGraph class with DFS cycle detection
- get_all_dependencies() batch query
- populate_rule_dependencies.py idempotency + --verify
- BUG-015: get_rule() detail includes linkage counts
- BUG-016: UI table data includes linked counts fields
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# ── DependencyGraph class tests ──────────────────────────────────────────────


class TestDependencyGraphCycleDetection:
    """DFS-based circular dependency detection."""

    def test_acyclic_graph_no_cycles(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
        })
        assert graph.detect_cycles() == []
        assert graph.is_acyclic is True
        assert graph.circular_count == 0

    def test_simple_cycle_detected(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B"},
            "B": {"C"},
            "C": {"A"},
        })
        cycles = graph.detect_cycles()
        assert len(cycles) >= 1
        # The cycle should contain A, B, C
        cycle_nodes = set(cycles[0])
        assert cycle_nodes == {"A", "B", "C"}
        assert graph.is_acyclic is False
        assert graph.circular_count >= 1

    def test_self_loop_detected(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"A"},
        })
        cycles = graph.detect_cycles()
        assert len(cycles) >= 1
        assert "A" in cycles[0]

    def test_multiple_cycles(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B"},
            "B": {"A"},  # cycle 1: A<->B
            "C": {"D"},
            "D": {"C"},  # cycle 2: C<->D
        })
        cycles = graph.detect_cycles()
        assert len(cycles) >= 2

    def test_empty_graph(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({})
        assert graph.detect_cycles() == []
        assert graph.is_acyclic is True
        assert graph.circular_count == 0

    def test_single_node_no_edges(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({"A": set()})
        assert graph.detect_cycles() == []

    def test_diamond_no_cycle(self):
        """Diamond shape (A→B, A→C, B→D, C→D) is NOT a cycle."""
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B", "C"},
            "B": {"D"},
            "C": {"D"},
        })
        assert graph.detect_cycles() == []

    def test_long_chain_with_back_edge(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B"},
            "B": {"C"},
            "C": {"D"},
            "D": {"E"},
            "E": {"B"},  # back edge to B → cycle B,C,D,E
        })
        cycles = graph.detect_cycles()
        assert len(cycles) >= 1
        cycle_nodes = set(cycles[0])
        assert {"B", "C", "D", "E"}.issubset(cycle_nodes) or cycle_nodes == {"B", "C", "D", "E"}


class TestDependencyGraphTransitive:
    """Transitive dependency resolution."""

    def test_transitive_deps(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B"},
            "B": {"C"},
            "C": {"D"},
        })
        deps = graph.get_transitive_dependencies("A")
        assert deps == {"B", "C", "D"}

    def test_no_deps(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({"A": set(), "B": set()})
        assert graph.get_transitive_dependencies("A") == set()

    def test_nonexistent_node(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({"A": {"B"}})
        assert graph.get_transitive_dependencies("Z") == set()

    def test_cyclic_transitive_deps_dont_infinite_loop(self):
        from governance.services.dependency_graph import DependencyGraph
        graph = DependencyGraph({
            "A": {"B"},
            "B": {"C"},
            "C": {"A"},
        })
        # Should not hang — returns all reachable nodes (including A via back-edge)
        deps = graph.get_transitive_dependencies("A")
        assert deps == {"A", "B", "C"}


# ── get_all_dependencies batch query ────────────────────────────────────────


class TestGetAllDependenciesBatch:
    """Test the batch query on RuleInferenceQueries."""

    def test_get_all_dependencies_returns_graph(self):
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        instance = RuleInferenceQueries()
        instance._execute_query = MagicMock(return_value=[
            {"id1": "ARCH-MCP-01-v1", "id2": "SESSION-EVID-01-v1"},
            {"id1": "ARCH-MCP-01-v1", "id2": "GOV-RULE-01-v1"},
            {"id1": "TEST-GUARD-01-v1", "id2": "SESSION-EVID-01-v1"},
        ])
        result = instance.get_all_dependencies()
        assert "ARCH-MCP-01-v1" in result
        assert "SESSION-EVID-01-v1" in result["ARCH-MCP-01-v1"]
        assert "GOV-RULE-01-v1" in result["ARCH-MCP-01-v1"]
        assert len(result["ARCH-MCP-01-v1"]) == 2
        assert result["TEST-GUARD-01-v1"] == ["SESSION-EVID-01-v1"]

    def test_get_all_dependencies_empty(self):
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        instance = RuleInferenceQueries()
        instance._execute_query = MagicMock(return_value=[])
        result = instance.get_all_dependencies()
        assert result == {}

    def test_get_all_dependencies_handles_error(self):
        from governance.typedb.queries.rules.inference import RuleInferenceQueries

        instance = RuleInferenceQueries()
        instance._execute_query = MagicMock(side_effect=Exception("DB down"))
        result = instance.get_all_dependencies()
        assert result == {}


# ── dependency_overview real circular count ──────────────────────────────────


class TestDependencyOverviewCircularCount:
    """Verify dependency_overview uses real DFS, not hardcoded 0."""

    @patch("governance.services.rules_relations.get_client")
    def test_overview_returns_real_circular_count(self, mock_gc):
        from governance.services.rules_relations import dependency_overview

        mock_client = MagicMock()
        mock_gc.return_value = mock_client

        # Set up rules
        rule_a = MagicMock(id="A")
        rule_b = MagicMock(id="B")
        rule_c = MagicMock(id="C")
        mock_client.get_all_rules.return_value = [rule_a, rule_b, rule_c]

        # A→B→C→A cycle
        mock_client.get_rule_dependencies.side_effect = lambda rid: {
            "A": ["B"], "B": ["C"], "C": ["A"],
        }.get(rid, [])
        mock_client.get_rules_depending_on.side_effect = lambda rid: {
            "A": ["C"], "B": ["A"], "C": ["B"],
        }.get(rid, [])

        # Batch query returns the adjacency list
        mock_client.get_all_dependencies.return_value = {
            "A": ["B"], "B": ["C"], "C": ["A"],
        }

        result = dependency_overview()
        assert result["circular_count"] >= 1, "circular_count must not be hardcoded to 0"

    @patch("governance.services.rules_relations.get_client")
    def test_overview_zero_circular_when_acyclic(self, mock_gc):
        from governance.services.rules_relations import dependency_overview

        mock_client = MagicMock()
        mock_gc.return_value = mock_client

        rule_a = MagicMock(id="A")
        rule_b = MagicMock(id="B")
        mock_client.get_all_rules.return_value = [rule_a, rule_b]

        mock_client.get_rule_dependencies.side_effect = lambda rid: {
            "A": ["B"],
        }.get(rid, [])
        mock_client.get_rules_depending_on.side_effect = lambda rid: {
            "B": ["A"],
        }.get(rid, [])

        mock_client.get_all_dependencies.return_value = {"A": ["B"]}

        result = dependency_overview()
        assert result["circular_count"] == 0


# ── populate_rule_dependencies.py ────────────────────────────────────────────


class TestBuildDependencyGraphFromLeafDocs:
    """Test graph building from markdown files."""

    def test_build_graph_extracts_references(self, tmp_path):
        from scripts.populate_rule_dependencies import build_dependency_graph
        # Create two leaf docs
        (tmp_path / "ARCH-MCP-01-v1.md").write_text(
            "# ARCH-MCP-01-v1\nDepends on SESSION-EVID-01-v1 and GOV-RULE-01-v1."
        )
        (tmp_path / "SESSION-EVID-01-v1.md").write_text(
            "# SESSION-EVID-01-v1\nStandalone rule."
        )
        graph = build_dependency_graph(tmp_path)
        assert "ARCH-MCP-01-v1" in graph
        assert "SESSION-EVID-01-v1" in graph["ARCH-MCP-01-v1"]
        assert "GOV-RULE-01-v1" in graph["ARCH-MCP-01-v1"]
        # SESSION-EVID-01-v1 has no outgoing refs (standalone)
        assert "SESSION-EVID-01-v1" not in graph

    def test_self_references_excluded(self, tmp_path):
        from scripts.populate_rule_dependencies import build_dependency_graph
        (tmp_path / "ARCH-MCP-01-v1.md").write_text(
            "# ARCH-MCP-01-v1\nSee ARCH-MCP-01-v1 for details."
        )
        graph = build_dependency_graph(tmp_path)
        # Self-reference should be excluded
        assert "ARCH-MCP-01-v1" not in graph


class TestSeedingIdempotency:
    """Seeding should not create duplicate relations."""

    @patch("governance.stores.get_typedb_client")
    def test_idempotent_seeding(self, mock_get_client):
        from scripts.populate_rule_dependencies import populate_via_typedb

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate existing dependency A→B
        mock_client.get_rule_dependencies.return_value = ["B"]
        mock_client.create_rule_dependency.return_value = True

        graph = {"A": {"B"}}
        existing = {"A", "B"}

        stats = populate_via_typedb(graph, existing, dry_run=False)
        # Should skip because A→B already exists
        assert stats["skipped"] >= 1
        # create_rule_dependency should NOT be called
        mock_client.create_rule_dependency.assert_not_called()


# ── BUG-015: get_rule() detail includes linkage counts ──────────────────────


class TestBug015GetRuleDetailLinkageCounts:
    """BUG-015: get_rule() must return real linkage counts, not 0."""

    @patch("governance.services.rules.get_client")
    def test_get_rule_includes_linkage_counts(self, mock_gc):
        from governance.services.rules import get_rule

        mock_client = MagicMock()
        mock_gc.return_value = mock_client

        mock_rule = MagicMock()
        mock_rule.id = "TEST-RULE-01-v1"
        mock_rule.name = "Test Rule"
        mock_rule.category = "test"
        mock_rule.priority = "HIGH"
        mock_rule.status = "ACTIVE"
        mock_rule.directive = "Test directive"
        mock_rule.created_date = None
        mock_rule.applicability = "MANDATORY"
        mock_client.get_rule_by_id.return_value = mock_rule

        with patch("governance.services.rules.get_rule_document_paths", return_value={}):
            with patch("governance.services.rules.get_rule_linkage_counts",
                       return_value={"TEST-RULE-01-v1": {"tasks": 5, "sessions": 3}}) as mock_lc:
                result = get_rule("TEST-RULE-01-v1")
                # MUST call get_rule_linkage_counts
                mock_lc.assert_called_once()
                assert result["linked_tasks_count"] == 5
                assert result["linked_sessions_count"] == 3


# ── BUG-016: UI table data includes linked counts ───────────────────────────


class TestBug016UITableLinkedCounts:
    """BUG-016: list_rules() API response has linked count fields."""

    @patch("governance.services.rules.get_client")
    def test_list_rules_items_have_linked_counts(self, mock_gc):
        from governance.services.rules import list_rules

        mock_client = MagicMock()
        mock_gc.return_value = mock_client

        mock_rule = MagicMock()
        mock_rule.id = "RULE-001"
        mock_rule.name = "Rule 001"
        mock_rule.category = "test"
        mock_rule.priority = "HIGH"
        mock_rule.status = "ACTIVE"
        mock_rule.directive = "Do thing"
        mock_rule.created_date = None
        mock_rule.applicability = "MANDATORY"
        mock_client.get_all_rules.return_value = [mock_rule]

        with patch("governance.services.rules.get_rule_document_paths", return_value={}):
            with patch("governance.services.rules.get_rule_linkage_counts",
                       return_value={"RULE-001": {"tasks": 8, "sessions": 2}}):
                result = list_rules()
                item = result["items"][0]
                assert "linked_tasks_count" in item
                assert "linked_sessions_count" in item
                assert item["linked_tasks_count"] == 8
                assert item["linked_sessions_count"] == 2


# ── Verify flag for populate script ─────────────────────────────────────────


class TestPopulateVerifyFlag:
    """--verify flag reports graph stats."""

    def test_verify_graph_stats(self, tmp_path):
        from scripts.populate_rule_dependencies import verify_graph

        # Create a simple graph
        graph = {"A": {"B"}, "B": {"C"}}
        stats = verify_graph(graph)
        assert stats["nodes"] >= 2
        assert stats["edges"] >= 2
        assert "cycles" in stats
        assert isinstance(stats["cycles"], list)
