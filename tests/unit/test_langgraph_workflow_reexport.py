"""Tests for governance/langgraph_workflow.py — Re-export hub.

Verifies all expected symbols are re-exported from governance.langgraph
and that __all__ is complete and consistent.
"""

import unittest


class TestLangGraphWorkflowExports(unittest.TestCase):
    """Tests that langgraph_workflow re-exports match __all__."""

    def test_all_defined(self):
        import governance.langgraph_workflow as mod
        self.assertTrue(hasattr(mod, "__all__"))
        self.assertGreater(len(mod.__all__), 0)

    def test_all_symbols_accessible(self):
        """Every name in __all__ should be importable."""
        import governance.langgraph_workflow as mod
        for name in mod.__all__:
            self.assertTrue(
                hasattr(mod, name),
                f"{name} listed in __all__ but not accessible",
            )

    def test_state_exports(self):
        from governance.langgraph_workflow import (
            Vote,
            ProposalState,
            QUORUM_THRESHOLD,
            APPROVAL_THRESHOLD,
            DISPUTE_THRESHOLD,
            TRUST_WEIGHTS,
        )
        # Constants should be numeric
        self.assertIsInstance(QUORUM_THRESHOLD, (int, float))
        self.assertIsInstance(APPROVAL_THRESHOLD, (int, float))
        self.assertIsInstance(DISPUTE_THRESHOLD, (int, float))
        self.assertIsInstance(TRUST_WEIGHTS, dict)

    def test_node_exports(self):
        from governance.langgraph_workflow import (
            submit_node,
            validate_node,
            assess_node,
            vote_node,
            decide_node,
            implement_node,
            complete_node,
            reject_node,
        )
        for fn in [submit_node, validate_node, assess_node, vote_node,
                   decide_node, implement_node, complete_node, reject_node]:
            self.assertTrue(callable(fn))

    def test_edge_exports(self):
        from governance.langgraph_workflow import (
            check_validation,
            check_decision,
            check_status,
        )
        for fn in [check_validation, check_decision, check_status]:
            self.assertTrue(callable(fn))

    def test_graph_exports(self):
        from governance.langgraph_workflow import (
            build_proposal_graph,
            create_initial_state,
            run_proposal_workflow,
            print_workflow_diagram,
            LANGGRAPH_AVAILABLE,
        )
        self.assertTrue(callable(build_proposal_graph))
        self.assertTrue(callable(create_initial_state))
        self.assertTrue(callable(run_proposal_workflow))
        self.assertTrue(callable(print_workflow_diagram))
        self.assertIsInstance(LANGGRAPH_AVAILABLE, bool)

    def test_mcp_export(self):
        from governance.langgraph_workflow import proposal_submit_mcp
        self.assertTrue(callable(proposal_submit_mcp))

    def test_all_count(self):
        """__all__ has expected number of entries."""
        import governance.langgraph_workflow as mod
        # 6 state + 8 nodes + 3 edges + 5 graph + 1 mcp = 23
        self.assertEqual(len(mod.__all__), 23)

    def test_langgraph_available_is_bool(self):
        """Mock StateGraph implementation should make LANGGRAPH_AVAILABLE True."""
        from governance.langgraph_workflow import LANGGRAPH_AVAILABLE
        # It's True because MockStateGraph is used
        self.assertIsInstance(LANGGRAPH_AVAILABLE, bool)


class TestLangGraphWorkflowConsistency(unittest.TestCase):
    """Verify re-exports match governance.langgraph source."""

    def test_re_exports_match_source(self):
        import governance.langgraph_workflow as hub
        import governance.langgraph as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(
                    hub_obj, pkg_obj,
                    f"{name} in hub differs from package",
                )


class TestWorkflowConstants(unittest.TestCase):
    """Test governance workflow constants have sane values."""

    def test_quorum_threshold_range(self):
        from governance.langgraph_workflow import QUORUM_THRESHOLD
        self.assertGreater(QUORUM_THRESHOLD, 0)
        self.assertLessEqual(QUORUM_THRESHOLD, 1.0)

    def test_approval_threshold_range(self):
        from governance.langgraph_workflow import APPROVAL_THRESHOLD
        self.assertGreater(APPROVAL_THRESHOLD, 0)
        self.assertLessEqual(APPROVAL_THRESHOLD, 1.0)

    def test_dispute_threshold_range(self):
        from governance.langgraph_workflow import DISPUTE_THRESHOLD
        self.assertGreater(DISPUTE_THRESHOLD, 0)
        self.assertLessEqual(DISPUTE_THRESHOLD, 1.0)

    def test_trust_weights_non_empty(self):
        from governance.langgraph_workflow import TRUST_WEIGHTS
        self.assertGreater(len(TRUST_WEIGHTS), 0)


if __name__ == "__main__":
    unittest.main()
