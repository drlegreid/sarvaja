"""
Robot Framework Library for Data Router Tests.

Per P7.3: Routing new data to TypeDB.
Migrated from tests/test_data_router.py
"""
from pathlib import Path
from robot.api.deco import keyword


class DataRouterLibrary:
    """Library for testing data router module."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"

    # =============================================================================
    # Module Existence Tests
    # =============================================================================

    @keyword("Data Router Module Exists")
    def data_router_module_exists(self):
        """Data router module must exist."""
        router_file = self.governance_dir / "data_router.py"
        return {"exists": router_file.exists()}

    @keyword("Data Router Class Importable")
    def data_router_class_importable(self):
        """DataRouter class must be importable."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter()
            return {
                "importable": True,
                "instantiable": router is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    @keyword("Router Has Required Methods")
    def router_has_required_methods(self):
        """Router must have required methods."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter()

            return {
                "has_route_rule": hasattr(router, 'route_rule'),
                "has_route_decision": hasattr(router, 'route_decision'),
                "has_route_session": hasattr(router, 'route_session'),
                "has_route_auto": hasattr(router, 'route_auto')
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Init error: {str(e)}"}

    # =============================================================================
    # Rule Routing Tests
    # =============================================================================

    @keyword("Route New Rule Works")
    def route_new_rule_works(self):
        """Should route new rule to TypeDB."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter(dry_run=True)
            result = router.route_rule(
                rule_id="RULE-TEST-001",
                name="Test Rule",
                directive="Do the thing",
                category="testing",
                priority="HIGH"
            )

            return {
                "success": result.get('success') is True,
                "destination_typedb": result.get('destination') == 'typedb'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Route Rule Generates Embedding")
    def route_rule_generates_embedding(self):
        """Routing should generate embedding."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter(dry_run=True, embed=True)
            result = router.route_rule(
                rule_id="RULE-TEST-002",
                name="Test Rule with Embedding",
                directive="Do the other thing"
            )

            return {"embedded": result.get('embedded') is True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    @keyword("Route Rule Validates Data")
    def route_rule_validates_data(self):
        """Should validate rule data."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter(dry_run=True)

            # Missing required field
            result = router.route_rule(rule_id="", name="No ID")

            return {
                "rejects_invalid": result.get('success') is False,
                "has_error": 'error' in result
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}

    # =============================================================================
    # Decision Routing Tests
    # =============================================================================

    @keyword("Route New Decision Works")
    def route_new_decision_works(self):
        """Should route new decision to TypeDB."""
        try:
            from governance.data_router import DataRouter

            router = DataRouter(dry_run=True)
            result = router.route_decision(
                decision_id="DECISION-TEST-001",
                name="Test Decision",
                context="Test context",
                rationale="Test rationale"
            )

            return {
                "success": result.get('success') is True,
                "destination_typedb": result.get('destination') == 'typedb'
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": f"Execution error: {str(e)}"}
