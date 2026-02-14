"""Tests for governance/data_integrity.py — Deprecated re-export hub.

Verifies: deprecation warning emitted, all symbols re-exported,
consistency with governance.integrity source package.
"""

import unittest
import warnings


class TestDataIntegrityDeprecation(unittest.TestCase):
    def test_deprecation_warning_emitted(self):
        import importlib
        import governance.data_integrity as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertGreater(len(dep_warnings), 0)
            self.assertIn("deprecated", str(dep_warnings[0].message).lower())

    def test_warning_mentions_integrity(self):
        import importlib
        import governance.data_integrity as mod
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(mod)
            dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            self.assertIn("governance.integrity", str(dep_warnings[0].message))


class TestDataIntegrityExports(unittest.TestCase):
    def test_all_defined(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.data_integrity as mod
        self.assertTrue(hasattr(mod, "__all__"))

    def test_all_count(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.data_integrity as mod
        self.assertEqual(len(mod.__all__), 10)

    def test_all_symbols_accessible(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.data_integrity as mod
        for name in mod.__all__:
            self.assertTrue(hasattr(mod, name), f"{name} not accessible")

    def test_key_classes_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.data_integrity import (
                ValidationLevel, ValidationResult, DataIntegrityValidator,
                validate_edge_to_edge,
            )
        self.assertTrue(callable(DataIntegrityValidator))
        self.assertTrue(callable(validate_edge_to_edge))

    def test_utility_functions_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.data_integrity import (
                get_entity_id, get_field_value, camel_case,
            )
        self.assertTrue(callable(get_entity_id))
        self.assertTrue(callable(get_field_value))
        self.assertTrue(callable(camel_case))

    def test_constants_exported(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from governance.data_integrity import (
                ENTITY_SCHEMAS, VALID_VALUES, RELATION_SCHEMAS,
            )
        self.assertIsInstance(ENTITY_SCHEMAS, dict)
        self.assertIsInstance(VALID_VALUES, dict)
        self.assertIsInstance(RELATION_SCHEMAS, dict)


class TestDataIntegrityConsistency(unittest.TestCase):
    def test_same_objects(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import governance.data_integrity as hub
        import governance.integrity as pkg
        for name in hub.__all__:
            hub_obj = getattr(hub, name)
            pkg_obj = getattr(pkg, name, None)
            if pkg_obj is not None:
                self.assertIs(hub_obj, pkg_obj, f"{name} differs")


if __name__ == "__main__":
    unittest.main()
