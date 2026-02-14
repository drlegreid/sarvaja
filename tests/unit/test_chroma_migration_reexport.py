"""Tests for governance/chroma_migration.py — Deprecated re-export hub.

Verifies: deprecation warning emitted, all symbols re-exported,
consistency with governance.migration source package.
"""

import unittest
import warnings


class TestChromaMigrationDeprecation(unittest.TestCase):
    def test_deprecation_warning_emitted(self):
        import importlib
        import governance.chroma_migration as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertGreater(len(dep_warnings), 0)
            self.assertIn("deprecated", str(dep_warnings[0].message).lower())

    def test_warning_mentions_migration(self):
        import importlib
        import governance.chroma_migration as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertIn("governance.migration", str(dep_warnings[0].message))


class TestChromaMigrationExports(unittest.TestCase):
    def test_all_defined(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_migration as mod
        self.assertTrue(hasattr(mod, "__all__"))

    def test_all_count(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_migration as mod
        self.assertEqual(len(mod.__all__), 5)

    def test_all_symbols_accessible(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_migration as mod
        for name in mod.__all__:
            self.assertTrue(hasattr(mod, name), f"{name} not accessible")

    def test_key_classes_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.chroma_migration import (
                MigrationResult, ChromaScanner, DocumentTransformer,
                ChromaMigration, create_chroma_migration,
            )
        self.assertTrue(callable(ChromaMigration))
        self.assertTrue(callable(create_chroma_migration))

    def test_main_callable(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.chroma_migration import main
        self.assertTrue(callable(main))


class TestChromaMigrationConsistency(unittest.TestCase):
    def test_same_objects(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_migration as hub
        import governance.migration as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(hub_obj, pkg_obj, f"{name} differs")


if __name__ == "__main__":
    unittest.main()
