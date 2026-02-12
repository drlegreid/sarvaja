"""
Unit tests for Kanren Trust Level Constraints.

Per DOC-SIZE-01-v1: Tests for kanren/trust.py module.
Tests: trust_level, requires_supervisor, can_execute_priority.
"""

import pytest

from governance.kanren.trust import (
    trust_level,
    requires_supervisor,
    can_execute_priority,
)


class TestTrustLevel:
    """Tests for trust_level()."""

    def test_expert(self):
        assert trust_level(0.95) == "expert"
        assert trust_level(0.9) == "expert"
        assert trust_level(1.0) == "expert"

    def test_trusted(self):
        assert trust_level(0.7) == "trusted"
        assert trust_level(0.8) == "trusted"
        assert trust_level(0.89) == "trusted"

    def test_supervised(self):
        assert trust_level(0.5) == "supervised"
        assert trust_level(0.6) == "supervised"
        assert trust_level(0.69) == "supervised"

    def test_restricted(self):
        assert trust_level(0.0) == "restricted"
        assert trust_level(0.3) == "restricted"
        assert trust_level(0.49) == "restricted"


class TestRequiresSupervisor:
    """Tests for requires_supervisor()."""

    def test_restricted_needs_supervisor(self):
        result = requires_supervisor("restricted")
        assert result and result[0] is True

    def test_supervised_needs_supervisor(self):
        result = requires_supervisor("supervised")
        assert result and result[0] is True

    def test_trusted_no_supervisor(self):
        result = requires_supervisor("trusted")
        assert result and result[0] is False

    def test_expert_no_supervisor(self):
        result = requires_supervisor("expert")
        assert result and result[0] is False


class TestCanExecutePriority:
    """Tests for can_execute_priority()."""

    def test_expert_critical(self):
        result = can_execute_priority("expert", "CRITICAL")
        assert result and result[0] is True

    def test_trusted_critical(self):
        result = can_execute_priority("trusted", "CRITICAL")
        assert result and result[0] is True

    def test_supervised_critical(self):
        result = can_execute_priority("supervised", "CRITICAL")
        assert result and result[0] is False

    def test_restricted_critical(self):
        result = can_execute_priority("restricted", "CRITICAL")
        assert result and result[0] is False

    def test_trusted_high(self):
        result = can_execute_priority("trusted", "HIGH")
        assert result and result[0] is True

    def test_restricted_high(self):
        result = can_execute_priority("restricted", "HIGH")
        assert result and result[0] is False

    def test_medium_any_trust(self):
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "MEDIUM")
            assert result and result[0] is True

    def test_low_any_trust(self):
        for trust in ["expert", "trusted", "supervised", "restricted"]:
            result = can_execute_priority(trust, "LOW")
            assert result and result[0] is True
