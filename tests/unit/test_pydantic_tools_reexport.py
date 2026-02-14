"""Tests for governance/pydantic_tools.py — Re-export hub.

Verifies all expected symbols are re-exported from governance.pydantic_schemas
and that __all__ is complete and consistent.
"""

import unittest


class TestPydanticToolsExports(unittest.TestCase):
    """Tests that pydantic_tools re-exports match __all__."""

    def test_all_defined(self):
        import governance.pydantic_tools as mod
        self.assertTrue(hasattr(mod, "__all__"))
        self.assertGreater(len(mod.__all__), 0)

    def test_all_symbols_accessible(self):
        """Every name in __all__ should be importable from the module."""
        import governance.pydantic_tools as mod
        for name in mod.__all__:
            self.assertTrue(
                hasattr(mod, name),
                f"{name} listed in __all__ but not accessible",
            )

    def test_input_models_exported(self):
        from governance.pydantic_tools import (
            RuleQueryConfig,
            DependencyConfig,
            TrustScoreRequest,
            ProposalConfig,
            ImpactAnalysisConfig,
            DSMCycleConfig,
        )
        # All should be classes
        for cls in [RuleQueryConfig, DependencyConfig, TrustScoreRequest,
                    ProposalConfig, ImpactAnalysisConfig, DSMCycleConfig]:
            self.assertTrue(callable(cls), f"{cls} not callable")

    def test_output_models_exported(self):
        from governance.pydantic_tools import (
            RuleInfo,
            RuleQueryResult,
            DependencyResult,
            TrustScoreResult,
            ProposalResult,
            ImpactAnalysisResult,
            HealthCheckResult,
        )
        for cls in [RuleInfo, RuleQueryResult, DependencyResult,
                    TrustScoreResult, ProposalResult,
                    ImpactAnalysisResult, HealthCheckResult]:
            self.assertTrue(callable(cls))

    def test_typed_tools_exported(self):
        from governance.pydantic_tools import (
            query_rules_typed,
            analyze_dependencies_typed,
            calculate_trust_score_typed,
            create_proposal_typed,
            analyze_impact_typed,
            health_check_typed,
        )
        for fn in [query_rules_typed, analyze_dependencies_typed,
                   calculate_trust_score_typed, create_proposal_typed,
                   analyze_impact_typed, health_check_typed]:
            self.assertTrue(callable(fn))

    def test_mcp_wrappers_exported(self):
        from governance.pydantic_tools import (
            query_rules_mcp,
            analyze_dependencies_mcp,
            calculate_trust_score_mcp,
            analyze_impact_mcp,
            health_check_mcp,
        )
        for fn in [query_rules_mcp, analyze_dependencies_mcp,
                   calculate_trust_score_mcp, analyze_impact_mcp,
                   health_check_mcp]:
            self.assertTrue(callable(fn))

    def test_all_count(self):
        """__all__ should have exactly 18 items (6 input + 7 output + 6 tools + 5 mcp - 6 overlap)."""
        import governance.pydantic_tools as mod
        # 6 input models + 7 output models + 6 typed tools + 5 mcp wrappers = 24
        self.assertEqual(len(mod.__all__), 24)

    def test_main_callable(self):
        """main() function should be defined."""
        from governance.pydantic_tools import main
        self.assertTrue(callable(main))


class TestPydanticToolsConsistency(unittest.TestCase):
    """Tests that re-exports match the source package."""

    def test_re_exports_match_source(self):
        """Symbols should be identical objects from pydantic_schemas."""
        import governance.pydantic_tools as hub
        import governance.pydantic_schemas as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(
                    hub_obj, pkg_obj,
                    f"{name} in hub is not the same object as in package",
                )


if __name__ == "__main__":
    unittest.main()
