"""
Unit tests for Data Router Models.

Per DOC-SIZE-01-v1: Tests for router/models.py module.
Tests: RouteResult dataclass.
"""

import pytest
from dataclasses import asdict

from governance.router.models import RouteResult


class TestRouteResult:
    """Tests for RouteResult dataclass."""

    def test_required_fields(self):
        r = RouteResult(
            success=True,
            destination="typedb",
            item_type="rule",
            item_id="RULE-001",
        )
        assert r.success is True
        assert r.destination == "typedb"
        assert r.item_type == "rule"
        assert r.item_id == "RULE-001"

    def test_defaults(self):
        r = RouteResult(
            success=True, destination="typedb",
            item_type="rule", item_id="R-1",
        )
        assert r.embedded is False
        assert r.error is None
        assert r.metadata is None
        assert r.evidence_file is None

    def test_with_error(self):
        r = RouteResult(
            success=False, destination="none",
            item_type="rule", item_id="R-1",
            error="validation failed",
        )
        assert r.error == "validation failed"

    def test_with_metadata(self):
        r = RouteResult(
            success=True, destination="typedb",
            item_type="session", item_id="S-1",
            metadata={"date": "2026-02-11"},
        )
        assert r.metadata["date"] == "2026-02-11"

    def test_asdict(self):
        r = RouteResult(
            success=True, destination="typedb",
            item_type="rule", item_id="R-1",
            embedded=True,
        )
        d = asdict(r)
        assert d["success"] is True
        assert d["embedded"] is True
        assert isinstance(d, dict)

    def test_with_evidence_file(self):
        r = RouteResult(
            success=True, destination="typedb",
            item_type="decision", item_id="D-1",
            evidence_file="evidence/DECISION-001.md",
        )
        assert r.evidence_file == "evidence/DECISION-001.md"
