"""Tests for governance/chroma_readonly.py — Deprecated re-export hub.

Verifies: deprecation warning emitted, all symbols re-exported,
consistency with governance.readonly source package.
"""

import unittest
import warnings


class TestChromaReadonlyDeprecation(unittest.TestCase):
    def test_deprecation_warning_emitted(self):
        import importlib
        import governance.chroma_readonly as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertGreater(len(dep_warnings), 0)
            self.assertIn("deprecated", str(dep_warnings[0].message).lower())

    def test_warning_mentions_readonly(self):
        import importlib
        import governance.chroma_readonly as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertIn("governance.readonly", str(dep_warnings[0].message))


class TestChromaReadonlyExports(unittest.TestCase):
    def test_all_defined(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_readonly as mod
        self.assertTrue(hasattr(mod, "__all__"))

    def test_all_count(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_readonly as mod
        self.assertEqual(len(mod.__all__), 4)

    def test_all_symbols_accessible(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_readonly as mod
        for name in mod.__all__:
            self.assertTrue(hasattr(mod, name), f"{name} not accessible")

    def test_key_classes_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.chroma_readonly import (
                DeprecationResult, ReadOnlyCollection,
                ChromaReadOnly, create_readonly_client,
            )
        self.assertTrue(callable(ChromaReadOnly))
        self.assertTrue(callable(create_readonly_client))

    def test_main_callable(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.chroma_readonly import main
        self.assertTrue(callable(main))


class TestChromaReadonlyConsistency(unittest.TestCase):
    def test_same_objects(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.chroma_readonly as hub
        import governance.readonly as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(hub_obj, pkg_obj, f"{name} differs")


if __name__ == "__main__":
    unittest.main()
