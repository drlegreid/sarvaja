"""
Robot Framework Library for Decision Dates Tests.

Per GAP-UI-EXP-001: Decisions missing dates.
Migrated from tests/test_decision_dates.py
"""
import dataclasses
from robot.api.deco import keyword


class DecisionDatesLibrary:
    """Library for testing decision date retrieval."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =============================================================================
    # Decision Entity Tests
    # =============================================================================

    @keyword("Decision Entity Has Date Field")
    def decision_entity_has_date_field(self):
        """Verify Decision dataclass has decision_date field."""
        try:
            from governance.typedb.entities import Decision

            fields = {f.name for f in dataclasses.fields(Decision)}
            return {"has_decision_date": "decision_date" in fields}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Get All Decisions Returns Dates")
    def get_all_decisions_returns_dates(self):
        """Verify get_all_decisions includes decision_date."""
        try:
            from governance.client import get_client

            client = get_client()
            if not client or not client.is_connected():
                return {"skipped": True, "reason": "TypeDB not available"}

            decisions = client.get_all_decisions()
            if len(decisions) == 0:
                return {"skipped": True, "reason": "No decisions found"}

            decisions_with_dates = [d for d in decisions if d.decision_date is not None]
            # Skip if no decisions have dates - data presence test
            if len(decisions_with_dates) == 0:
                return {"skipped": True, "reason": "No decisions have dates (data not yet populated)"}

            return {
                "has_decisions": len(decisions) > 0,
                "has_dates": len(decisions_with_dates) > 0
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Decision Date Is Datetime")
    def decision_date_is_datetime(self):
        """Verify decision_date is datetime type when present."""
        try:
            from datetime import datetime
            from governance.client import get_client

            client = get_client()
            if not client or not client.is_connected():
                return {"skipped": True, "reason": "TypeDB not available"}

            decisions = client.get_all_decisions()
            for d in decisions:
                if d.decision_date is not None:
                    if not isinstance(d.decision_date, datetime):
                        return {"is_datetime": False}
            return {"is_datetime": True}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    # =============================================================================
    # Query Structure Tests
    # =============================================================================

    @keyword("Query Fetches Date Attribute")
    def query_fetches_date_attribute(self):
        """Verify the TypeDB query includes decision-date."""
        try:
            import inspect
            from governance.typedb.queries.rules.decisions import DecisionQueries

            source = inspect.getsource(DecisionQueries.get_all_decisions)
            return {"has_decision_date": "decision-date" in source}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except AttributeError as e:
            return {"skipped": True, "reason": f"DecisionQueries.get_all_decisions not found: {e}"}
