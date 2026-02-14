"""Tests for governance/rule_quality.py — Deprecated re-export hub.

Verifies: deprecation warning emitted, all symbols re-exported,
consistency with governance.quality source package.
"""

import unittest
import warnings


class TestRuleQualityDeprecation(unittest.TestCase):
    """Tests that importing rule_quality emits a DeprecationWarning."""

    def test_deprecation_warning_emitted(self):
        """Importing governance.rule_quality should warn."""
        # Module is already imported, so trigger by reloading
        import importlib
        import governance.rule_quality as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertGreater(len(dep_warnings), 0)
            self.assertIn("deprecated", str(dep_warnings[0].message).lower())

    def test_warning_message_content(self):
        import importlib
        import governance.rule_quality as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertIn("governance.quality", str(dep_warnings[0].message))


class TestRuleQualityExports(unittest.TestCase):
    """Tests that all expected symbols are re-exported."""

    def test_all_defined(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.rule_quality as mod
        self.assertTrue(hasattr(mod, "__all__"))

    def test_all_count(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.rule_quality as mod
        self.assertEqual(len(mod.__all__), 8)

    def test_all_symbols_accessible(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.rule_quality as mod
        for name in mod.__all__:
            self.assertTrue(
                hasattr(mod, name),
                f"{name} in __all__ but not accessible",
            )

    def test_enums_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.rule_quality import IssueSeverity, IssueType
        self.assertTrue(callable(IssueSeverity))
        self.assertTrue(callable(IssueType))

    def test_classes_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.rule_quality import (
                RuleIssue, RuleHealthReport, RuleQualityAnalyzer,
            )
        for cls in [RuleIssue, RuleHealthReport, RuleQualityAnalyzer]:
            self.assertTrue(callable(cls))

    def test_functions_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.rule_quality import (
                analyze_rule_quality, get_rule_impact, find_rule_issues,
            )
        for fn in [analyze_rule_quality, get_rule_impact, find_rule_issues]:
            self.assertTrue(callable(fn))


class TestRuleQualityConsistency(unittest.TestCase):
    """Verify re-exports match governance.quality source."""

    def test_same_objects(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.rule_quality as hub
        import governance.quality as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(
                    hub_obj, pkg_obj,
                    f"{name} differs between hub and package",
                )


if __name__ == "__main__":
    unittest.main()
