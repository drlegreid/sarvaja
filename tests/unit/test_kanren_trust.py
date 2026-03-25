"""
Unit tests for Kanren Trust Level Constraints.

Per DOC-SIZE-01-v1: Tests for kanren/trust.py module.
Tests: trust_level(), requires_supervisor(), can_execute_priority().
"""

import pytest
pytest.importorskip("kanren")  # BUG-014: skip if kanren not installed

from governance.kanren.trust import trust_level, requires_supervisor, can_execute_priority


class TestTrustLevel:
    def test_expert(self):
        assert trust_level(0.95) == "expert"
        assert trust_level(0.90) == "expert"

    def test_trusted(self):
        assert trust_level(0.85) == "trusted"
        assert trust_level(0.70) == "trusted"

    def test_supervised(self):
        assert trust_level(0.65) == "supervised"
        assert trust_level(0.50) == "supervised"

    def test_restricted(self):
        assert trust_level(0.49) == "restricted"
        assert trust_level(0.0) == "restricted"

    def test_boundary_expert(self):
        assert trust_level(0.9) == "expert"
        assert trust_level(0.89) == "trusted"

    def test_boundary_trusted(self):
        assert trust_level(0.7) == "trusted"
        assert trust_level(0.69) == "supervised"

    def test_boundary_supervised(self):
        assert trust_level(0.5) == "supervised"
        assert trust_level(0.49) == "restricted"


class TestRequiresSupervisor:
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

    def test_any_medium(self):
        result = can_execute_priority("restricted", "MEDIUM")
        assert result and result[0] is True

    def test_any_low(self):
        result = can_execute_priority("restricted", "LOW")
        assert result and result[0] is True
