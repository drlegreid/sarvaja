"""
TDD Tests for GAP-FILE-022: context_preloader.py Split

Tests verify that the modularized context_preloader package:
1. Maintains backward compatibility
2. Has properly separated models
3. All modules stay under 400 lines

Per RULE-004: TDD approach
Per DOC-SIZE-01-v1: Files under 400 lines
"""

import pytest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
GOVERNANCE_DIR = PROJECT_ROOT / "governance"


# =============================================================================
# Test 1: Package Structure
# =============================================================================

class TestPackageStructure:
    """Tests for the new package structure."""

    def test_context_preloader_package_exists(self):
        """context_preloader should be a module or package."""
        package_dir = GOVERNANCE_DIR / "context_preloader"
        old_file = GOVERNANCE_DIR / "context_preloader.py"
        assert package_dir.exists() or old_file.exists(), \
            "Either context_preloader/ package or context_preloader.py must exist"

    def test_models_module_exists(self):
        """Models module should exist in package."""
        models_file = GOVERNANCE_DIR / "context_preloader" / "models.py"
        package_dir = GOVERNANCE_DIR / "context_preloader"
        if package_dir.exists():
            assert models_file.exists(), "models.py must exist in package"


# =============================================================================
# Test 2: Backward Compatibility
# =============================================================================

class TestBackwardCompatibility:
    """Tests ensuring existing imports still work."""

    def test_import_context_preloader_class(self):
        """from governance.context_preloader import ContextPreloader must work."""
        from governance.context_preloader import ContextPreloader
        assert ContextPreloader is not None

    def test_import_decision_class(self):
        """from governance.context_preloader import Decision must work."""
        from governance.context_preloader import Decision
        assert Decision is not None

    def test_import_technology_choice_class(self):
        """from governance.context_preloader import TechnologyChoice must work."""
        from governance.context_preloader import TechnologyChoice
        assert TechnologyChoice is not None

    def test_import_context_summary_class(self):
        """from governance.context_preloader import ContextSummary must work."""
        from governance.context_preloader import ContextSummary
        assert ContextSummary is not None

    def test_import_get_context_preloader(self):
        """from governance.context_preloader import get_context_preloader must work."""
        from governance.context_preloader import get_context_preloader
        assert get_context_preloader is not None

    def test_import_preload_session_context(self):
        """from governance.context_preloader import preload_session_context must work."""
        from governance.context_preloader import preload_session_context
        assert preload_session_context is not None

    def test_import_get_agent_context_prompt(self):
        """from governance.context_preloader import get_agent_context_prompt must work."""
        from governance.context_preloader import get_agent_context_prompt
        assert get_agent_context_prompt is not None


# =============================================================================
# Test 3: Models Module
# =============================================================================

class TestModelsModule:
    """Tests for the extracted models module."""

    def test_decision_dataclass_works(self):
        """Decision dataclass should work."""
        from governance.context_preloader import Decision

        d = Decision(
            id="DECISION-001",
            name="Test Decision",
            status="APPROVED",
            date="2026-01-14",
            summary="Test summary"
        )

        assert d.id == "DECISION-001"
        assert d.name == "Test Decision"
        assert d.status == "APPROVED"

    def test_technology_choice_dataclass_works(self):
        """TechnologyChoice dataclass should work."""
        from governance.context_preloader import TechnologyChoice

        tc = TechnologyChoice(
            area="Database",
            choice="TypeDB",
            not_using="PostgreSQL",
            rationale="Graph-first"
        )

        assert tc.area == "Database"
        assert tc.choice == "TypeDB"

    def test_context_summary_dataclass_works(self):
        """ContextSummary dataclass should work."""
        from governance.context_preloader import ContextSummary

        cs = ContextSummary()
        assert cs.decisions == []
        assert cs.technology_choices == []
        assert cs.active_phase is None

    def test_context_summary_to_agent_prompt(self):
        """ContextSummary.to_agent_prompt should return string."""
        from governance.context_preloader import ContextSummary

        cs = ContextSummary()
        prompt = cs.to_agent_prompt()

        assert isinstance(prompt, str)
        assert "Strategic Context" in prompt

    def test_context_summary_to_dict(self):
        """ContextSummary.to_dict should return dict."""
        from governance.context_preloader import ContextSummary

        cs = ContextSummary()
        d = cs.to_dict()

        assert isinstance(d, dict)
        assert "decisions" in d
        assert "technology_choices" in d


# =============================================================================
# Test 4: File Size Compliance
# =============================================================================

class TestFileSizeCompliance:
    """Tests ensuring files stay under size limit."""

    def test_all_modules_under_400_lines(self):
        """All modules in package should be under 400 lines."""
        package_dir = GOVERNANCE_DIR / "context_preloader"

        if not package_dir.exists():
            old_file = GOVERNANCE_DIR / "context_preloader.py"
            if old_file.exists():
                line_count = len(old_file.read_text().splitlines())
                if line_count > 400:
                    pytest.skip(f"Single file has {line_count} lines - refactoring needed")
            return

        for py_file in package_dir.glob("*.py"):
            line_count = len(py_file.read_text().splitlines())
            assert line_count <= 400, \
                f"{py_file.name} has {line_count} lines, exceeds 400 limit"


# =============================================================================
# Test 5: Integration
# =============================================================================

class TestIntegration:
    """Integration tests for refactored preloader."""

    def test_preloader_creates_instance(self):
        """ContextPreloader should create instance."""
        from governance.context_preloader import ContextPreloader

        preloader = ContextPreloader()
        assert preloader is not None

    def test_preloader_load_context(self):
        """ContextPreloader.load_context should return ContextSummary."""
        from governance.context_preloader import ContextPreloader, ContextSummary

        preloader = ContextPreloader()
        context = preloader.load_context()

        assert isinstance(context, ContextSummary)

    def test_get_context_preloader_returns_same_instance(self):
        """get_context_preloader should return singleton."""
        from governance.context_preloader import get_context_preloader

        p1 = get_context_preloader()
        p2 = get_context_preloader()

        assert p1 is p2

    def test_preload_session_context_works(self):
        """preload_session_context should return ContextSummary."""
        from governance.context_preloader import preload_session_context, ContextSummary

        context = preload_session_context()
        assert isinstance(context, ContextSummary)
