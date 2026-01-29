"""
TDD Tests for GAP-UI-EXP-001: Decisions missing dates.

Per TEST-FIX-01-v1: Fix MUST include verification evidence.
Per DOC-SIZE-01-v1: Files under 400 lines.

Created: 2026-01-14
"""

import pytest
from datetime import datetime


class TestDecisionDateRetrieval:
    """Test decision date retrieval from TypeDB."""

    def test_decision_entity_has_date_field(self):
        """Verify Decision dataclass has decision_date field."""
        from governance.typedb.entities import Decision
        import dataclasses

        fields = {f.name for f in dataclasses.fields(Decision)}
        assert "decision_date" in fields

    def test_get_all_decisions_returns_dates(self):
        """Verify get_all_decisions includes decision_date."""
        pytest.importorskip("typedb.driver")

        from governance.client import get_client

        client = get_client()
        if not client or not client.is_connected():
            pytest.skip("TypeDB not available")

        decisions = client.get_all_decisions()
        assert len(decisions) > 0, "Should have decisions"

        # At least one decision should have a date
        decisions_with_dates = [d for d in decisions if d.decision_date is not None]
        assert len(decisions_with_dates) > 0, "At least one decision should have a date"

    def test_decision_date_is_datetime(self):
        """Verify decision_date is datetime type when present."""
        pytest.importorskip("typedb.driver")

        from governance.client import get_client

        client = get_client()
        if not client or not client.is_connected():
            pytest.skip("TypeDB not available")

        decisions = client.get_all_decisions()
        for d in decisions:
            if d.decision_date is not None:
                assert isinstance(d.decision_date, datetime), \
                    f"decision_date should be datetime, got {type(d.decision_date)}"


class TestDecisionMCPEndpoint:
    """Test decision MCP endpoint returns dates."""

    def test_list_decisions_includes_date(self):
        """Verify governance_list_decisions returns dates."""
        import json
        import requests

        try:
            resp = requests.get("http://localhost:8082/api/decisions", timeout=5)
            if resp.status_code != 200:
                pytest.skip("API not available")
        except Exception:
            pytest.skip("API not available")

        data = resp.json()
        decisions = data.get("decisions", data) if isinstance(data, dict) else data

        # At least one decision should have a date
        decisions_with_dates = [
            d for d in decisions
            if (d.get("decision_date") or d.get("date")) is not None
            and (d.get("decision_date") or d.get("date")) != "null"
        ]
        assert len(decisions_with_dates) > 0, \
            f"At least one decision should have a date. Got: {decisions}"


class TestDecisionQueryStructure:
    """Test the query structure retrieves dates."""

    def test_query_fetches_date_attribute(self):
        """Verify the TypeDB query includes decision-date."""
        from governance.typedb.queries.rules.decisions import DecisionQueries
        import inspect

        source = inspect.getsource(DecisionQueries.get_all_decisions)

        # The query should fetch decision-date
        assert "decision-date" in source, \
            "Query should fetch decision-date attribute"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
