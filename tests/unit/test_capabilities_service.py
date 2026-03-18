"""
Unit tests for Capabilities Service Layer.

Per DOC-SIZE-01-v1: Tests for governance/services/capabilities.py module.
Tests: bind_rule_to_agent, unbind_rule_from_agent, get_capabilities_for_agent,
get_agents_for_rule, list_capabilities, update_capability_status,
get_capability_summary, seed data.
"""

from unittest.mock import patch

import pytest

_P = "governance.services.capabilities"


@pytest.fixture(autouse=True)
def _reset_store():
    """Reset in-memory capabilities store for each test."""
    with patch(f"{_P}._capabilities_store", {}) as store, \
         patch(f"{_P}.record_audit"):
        yield store


# ── seed defaults ─────────────────────────────────────────────────


class TestSeedDefaults:
    def test_seed_populates_store_when_empty(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        assert len(_capabilities_store) == 0
        _seed_defaults()
        # Should have bindings from _DEFAULT_BINDINGS
        assert len(_capabilities_store) > 0

    def test_seed_includes_code_agent_rules(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        _seed_defaults()
        code_agent_keys = [k for k in _capabilities_store if k.startswith("code-agent::")]
        assert len(code_agent_keys) == 4
        rule_ids = [_capabilities_store[k]["rule_id"] for k in code_agent_keys]
        assert "TEST-GUARD-01" in rule_ids
        assert "TEST-COMP-02" in rule_ids
        assert "DOC-SIZE-01" in rule_ids
        assert "TEST-FIX-01" in rule_ids

    def test_seed_includes_security_agent(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        _seed_defaults()
        sec_keys = [k for k in _capabilities_store if k.startswith("security-agent::")]
        assert len(sec_keys) == 2
        rule_ids = [_capabilities_store[k]["rule_id"] for k in sec_keys]
        assert "SAFETY-HEALTH-01" in rule_ids
        assert "SAFETY-DESTR-01" in rule_ids

    def test_seed_sets_correct_categories(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        _seed_defaults()
        # All code-agent entries should be category "coding"
        for k, v in _capabilities_store.items():
            if v["agent_id"] == "code-agent":
                assert v["category"] == "coding"
            elif v["agent_id"] == "research-agent":
                assert v["category"] == "research"

    def test_seed_all_entries_active_status(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        _seed_defaults()
        for v in _capabilities_store.values():
            assert v["status"] == "active"

    def test_seed_all_entries_have_created_at(self):
        from governance.services.capabilities import _seed_defaults, _capabilities_store
        _seed_defaults()
        for v in _capabilities_store.values():
            assert "created_at" in v
            assert v["created_at"]  # non-empty

    def test_seed_does_not_overwrite_existing(self):
        from governance.services.capabilities import (
            _seed_defaults, _capabilities_store, _key,
        )
        # Pre-populate one entry
        k = _key("code-agent", "TEST-GUARD-01")
        _capabilities_store[k] = {"agent_id": "code-agent", "rule_id": "TEST-GUARD-01",
                                   "category": "custom", "status": "suspended",
                                   "created_at": "2026-01-01T00:00:00"}
        _seed_defaults()
        # Should not have overwritten the store since it was non-empty
        assert _capabilities_store[k]["category"] == "custom"
        assert _capabilities_store[k]["status"] == "suspended"

    def test_seed_total_binding_count(self):
        from governance.services.capabilities import (
            _seed_defaults, _capabilities_store, _DEFAULT_BINDINGS,
        )
        _seed_defaults()
        expected = sum(len(cfg["rules"]) for cfg in _DEFAULT_BINDINGS.values())
        assert len(_capabilities_store) == expected


# ── bind_rule_to_agent ────────────────────────────────────────────


class TestBindRuleToAgent:
    def test_bind_new_creates_entry(self):
        from governance.services.capabilities import bind_rule_to_agent
        result = bind_rule_to_agent("my-agent", "MY-RULE-01", category="testing")
        assert result["agent_id"] == "my-agent"
        assert result["rule_id"] == "MY-RULE-01"
        assert result["category"] == "testing"
        assert result["status"] == "active"
        assert "created_at" in result

    def test_bind_default_category_is_general(self):
        from governance.services.capabilities import bind_rule_to_agent
        result = bind_rule_to_agent("my-agent", "MY-RULE-01")
        assert result["category"] == "general"

    def test_bind_duplicate_returns_existing(self):
        from governance.services.capabilities import bind_rule_to_agent
        first = bind_rule_to_agent("my-agent", "MY-RULE-01", category="coding")
        second = bind_rule_to_agent("my-agent", "MY-RULE-01", category="testing")
        # Duplicate returns existing; category should not change
        assert second["category"] == "coding"
        assert first is second

    def test_bind_records_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit:
            from governance.services.capabilities import bind_rule_to_agent
            bind_rule_to_agent("agt", "RULE-01", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "CREATE"
            assert call_args[0][1] == "capability"
            assert call_args[1]["metadata"]["source"] == "api"

    def test_bind_duplicate_does_not_record_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit:
            from governance.services.capabilities import bind_rule_to_agent
            bind_rule_to_agent("agt", "RULE-01")
            mock_audit.reset_mock()
            bind_rule_to_agent("agt", "RULE-01")
            mock_audit.assert_not_called()

    def test_bind_different_agents_same_rule(self):
        from governance.services.capabilities import bind_rule_to_agent
        r1 = bind_rule_to_agent("agent-a", "SHARED-RULE")
        r2 = bind_rule_to_agent("agent-b", "SHARED-RULE")
        assert r1["agent_id"] == "agent-a"
        assert r2["agent_id"] == "agent-b"
        assert r1 is not r2

    def test_bind_same_agent_different_rules(self):
        from governance.services.capabilities import bind_rule_to_agent
        r1 = bind_rule_to_agent("agent-a", "RULE-01")
        r2 = bind_rule_to_agent("agent-a", "RULE-02")
        assert r1["rule_id"] == "RULE-01"
        assert r2["rule_id"] == "RULE-02"

    def test_bind_triggers_seed(self):
        """Calling bind on empty store should seed defaults first."""
        from governance.services.capabilities import (
            bind_rule_to_agent, _capabilities_store,
        )
        bind_rule_to_agent("new-agent", "NEW-RULE")
        # Store has seed data + the new binding
        assert len(_capabilities_store) > 1


# ── unbind_rule_from_agent ────────────────────────────────────────


class TestUnbindRuleFromAgent:
    def test_unbind_existing_returns_true(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, unbind_rule_from_agent,
        )
        bind_rule_to_agent("agt", "RULE-01")
        result = unbind_rule_from_agent("agt", "RULE-01")
        assert result is True

    def test_unbind_nonexistent_returns_false(self):
        from governance.services.capabilities import unbind_rule_from_agent
        result = unbind_rule_from_agent("no-agent", "NO-RULE")
        assert result is False

    def test_unbind_removes_from_store(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, unbind_rule_from_agent,
            _capabilities_store, _key,
        )
        bind_rule_to_agent("agt", "RULE-01")
        k = _key("agt", "RULE-01")
        assert k in _capabilities_store
        unbind_rule_from_agent("agt", "RULE-01")
        assert k not in _capabilities_store

    def test_unbind_records_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit:
            from governance.services.capabilities import (
                bind_rule_to_agent, unbind_rule_from_agent,
            )
            bind_rule_to_agent("agt", "RULE-01")
            mock_audit.reset_mock()
            unbind_rule_from_agent("agt", "RULE-01", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "DELETE"
            assert call_args[1]["metadata"]["source"] == "api"

    def test_unbind_nonexistent_does_not_record_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit:
            from governance.services.capabilities import unbind_rule_from_agent
            unbind_rule_from_agent("no-agent", "NO-RULE")
            mock_audit.assert_not_called()

    def test_unbind_idempotent(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, unbind_rule_from_agent,
        )
        bind_rule_to_agent("agt", "RULE-01")
        assert unbind_rule_from_agent("agt", "RULE-01") is True
        assert unbind_rule_from_agent("agt", "RULE-01") is False


# ── get_capabilities_for_agent ────────────────────────────────────


class TestGetCapabilitiesForAgent:
    def test_agent_with_bindings(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, get_capabilities_for_agent,
        )
        bind_rule_to_agent("agt", "RULE-01", category="coding")
        bind_rule_to_agent("agt", "RULE-02", category="testing")
        caps = get_capabilities_for_agent("agt")
        assert len(caps) == 2
        rule_ids = [c["rule_id"] for c in caps]
        assert "RULE-01" in rule_ids
        assert "RULE-02" in rule_ids

    def test_agent_without_bindings(self):
        from governance.services.capabilities import get_capabilities_for_agent
        caps = get_capabilities_for_agent("unknown-agent")
        # Seed data is loaded but unknown-agent has no bindings
        assert isinstance(caps, list)
        assert all(c["agent_id"] != "unknown-agent" for c in caps)
        assert len([c for c in caps if c["agent_id"] == "unknown-agent"]) == 0

    def test_only_returns_matching_agent(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, get_capabilities_for_agent,
        )
        bind_rule_to_agent("agt-a", "RULE-01")
        bind_rule_to_agent("agt-b", "RULE-02")
        caps = get_capabilities_for_agent("agt-a")
        assert all(c["agent_id"] == "agt-a" for c in caps)

    def test_returns_seeded_bindings(self):
        from governance.services.capabilities import get_capabilities_for_agent
        caps = get_capabilities_for_agent("code-agent")
        rule_ids = [c["rule_id"] for c in caps]
        assert "TEST-GUARD-01" in rule_ids


# ── get_agents_for_rule ───────────────────────────────────────────


class TestGetAgentsForRule:
    def test_rule_with_agents(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, get_agents_for_rule,
        )
        bind_rule_to_agent("agt-a", "SHARED", category="coding")
        bind_rule_to_agent("agt-b", "SHARED", category="testing")
        result = get_agents_for_rule("SHARED")
        assert len(result) == 2
        agent_ids = [r["agent_id"] for r in result]
        assert "agt-a" in agent_ids
        assert "agt-b" in agent_ids

    def test_rule_without_agents(self):
        from governance.services.capabilities import get_agents_for_rule
        result = get_agents_for_rule("UNBOUND-RULE")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_seeded_rule_has_agents(self):
        from governance.services.capabilities import get_agents_for_rule
        # GOV-RULE-01 is seeded for research-agent and curator-agent
        result = get_agents_for_rule("GOV-RULE-01")
        agent_ids = [r["agent_id"] for r in result]
        assert "research-agent" in agent_ids
        assert "curator-agent" in agent_ids


# ── list_capabilities ─────────────────────────────────────────────


class TestListCapabilities:
    def test_list_all_no_filters(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities()
        # Should have seed data
        assert len(result) > 0

    def test_filter_by_agent_id(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(agent_id="code-agent")
        assert all(c["agent_id"] == "code-agent" for c in result)
        assert len(result) == 4  # 4 seeded rules for code-agent

    def test_filter_by_rule_id(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(rule_id="TEST-GUARD-01")
        assert all(c["rule_id"] == "TEST-GUARD-01" for c in result)
        assert len(result) >= 1

    def test_filter_by_category(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(category="coding")
        assert all(c["category"] == "coding" for c in result)
        assert len(result) == 4

    def test_filter_by_status(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(status="active")
        assert all(c["status"] == "active" for c in result)

    def test_filter_by_status_suspended_empty(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(status="suspended")
        assert len(result) == 0  # no suspended in seed data

    def test_combined_filters(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(agent_id="code-agent", category="coding", status="active")
        assert len(result) == 4
        assert all(
            c["agent_id"] == "code-agent" and c["category"] == "coding" and c["status"] == "active"
            for c in result
        )

    def test_combined_filters_no_match(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(agent_id="code-agent", category="governance")
        assert len(result) == 0

    def test_filter_by_nonexistent_agent(self):
        from governance.services.capabilities import list_capabilities
        result = list_capabilities(agent_id="nonexistent-agent")
        assert len(result) == 0


# ── update_capability_status ──────────────────────────────────────


class TestUpdateCapabilityStatus:
    def test_update_active_to_suspended(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, update_capability_status,
        )
        bind_rule_to_agent("agt", "RULE-01")
        result = update_capability_status("agt", "RULE-01", "suspended")
        assert result is not None
        assert result["status"] == "suspended"

    def test_update_suspended_to_active(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, update_capability_status,
        )
        bind_rule_to_agent("agt", "RULE-01")
        update_capability_status("agt", "RULE-01", "suspended")
        result = update_capability_status("agt", "RULE-01", "active")
        assert result["status"] == "active"

    def test_update_nonexistent_returns_none(self):
        from governance.services.capabilities import update_capability_status
        result = update_capability_status("no-agent", "NO-RULE", "active")
        assert result is None

    def test_update_records_audit(self):
        with patch(f"{_P}.record_audit") as mock_audit:
            from governance.services.capabilities import (
                bind_rule_to_agent, update_capability_status,
            )
            bind_rule_to_agent("agt", "RULE-01")
            mock_audit.reset_mock()
            update_capability_status("agt", "RULE-01", "suspended", source="api")
            mock_audit.assert_called_once()
            call_args = mock_audit.call_args
            assert call_args[0][0] == "UPDATE"
            assert call_args[1]["old_value"] == "active"
            assert call_args[1]["new_value"] == "suspended"
            assert call_args[1]["metadata"]["source"] == "api"

    def test_update_seeded_capability(self):
        from governance.services.capabilities import update_capability_status
        result = update_capability_status("code-agent", "TEST-GUARD-01", "suspended")
        assert result is not None
        assert result["status"] == "suspended"
        assert result["agent_id"] == "code-agent"


# ── get_capability_summary ────────────────────────────────────────


class TestGetCapabilitySummary:
    def test_summary_structure(self):
        from governance.services.capabilities import get_capability_summary
        summary = get_capability_summary()
        assert "total_bindings" in summary
        assert "agents_with_rules" in summary
        assert "rules_applied" in summary
        assert "by_category" in summary
        assert "active" in summary
        assert "suspended" in summary

    def test_summary_counts_seed_data(self):
        from governance.services.capabilities import (
            get_capability_summary, _DEFAULT_BINDINGS,
        )
        summary = get_capability_summary()
        expected_total = sum(len(cfg["rules"]) for cfg in _DEFAULT_BINDINGS.values())
        assert summary["total_bindings"] == expected_total
        assert summary["agents_with_rules"] == len(_DEFAULT_BINDINGS)
        assert summary["active"] == expected_total
        assert summary["suspended"] == 0

    def test_summary_categories(self):
        from governance.services.capabilities import get_capability_summary
        summary = get_capability_summary()
        cats = summary["by_category"]
        assert "coding" in cats
        assert "research" in cats
        assert "governance" in cats
        assert "security" in cats
        assert "infrastructure" in cats
        assert cats["coding"] == 4
        assert cats["security"] == 2

    def test_summary_after_suspend(self):
        from governance.services.capabilities import (
            update_capability_status, get_capability_summary,
        )
        update_capability_status("code-agent", "TEST-GUARD-01", "suspended")
        summary = get_capability_summary()
        assert summary["suspended"] == 1
        assert summary["active"] == summary["total_bindings"] - 1

    def test_summary_after_unbind(self):
        from governance.services.capabilities import (
            unbind_rule_from_agent, get_capability_summary, _DEFAULT_BINDINGS,
        )
        original_total = sum(len(cfg["rules"]) for cfg in _DEFAULT_BINDINGS.values())
        unbind_rule_from_agent("code-agent", "TEST-GUARD-01")
        summary = get_capability_summary()
        assert summary["total_bindings"] == original_total - 1

    def test_summary_after_bind(self):
        from governance.services.capabilities import (
            bind_rule_to_agent, get_capability_summary, _DEFAULT_BINDINGS,
        )
        original_total = sum(len(cfg["rules"]) for cfg in _DEFAULT_BINDINGS.values())
        bind_rule_to_agent("new-agent", "NEW-RULE", category="custom")
        summary = get_capability_summary()
        assert summary["total_bindings"] == original_total + 1
        assert "custom" in summary["by_category"]

    def test_summary_rules_applied_count(self):
        from governance.services.capabilities import get_capability_summary
        summary = get_capability_summary()
        # Count unique rules across all seed bindings
        all_rules = set()
        from governance.services.capabilities import _DEFAULT_BINDINGS
        for cfg in _DEFAULT_BINDINGS.values():
            all_rules.update(cfg["rules"])
        assert summary["rules_applied"] == len(all_rules)

    def test_summary_empty_store(self):
        """Summary on truly empty store still works (seed gets called)."""
        from governance.services.capabilities import get_capability_summary
        # Store is reset by fixture; summary triggers seed
        summary = get_capability_summary()
        assert summary["total_bindings"] > 0


# ── key function ──────────────────────────────────────────────────


class TestKeyFunction:
    def test_key_format(self):
        from governance.services.capabilities import _key
        assert _key("agent-a", "RULE-01") == "agent-a::RULE-01"

    def test_key_uniqueness(self):
        from governance.services.capabilities import _key
        assert _key("a", "b") != _key("b", "a")
        assert _key("a", "b") != _key("a", "c")
