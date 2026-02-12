"""
Unit tests for State Constants.

Per DOC-SIZE-01-v1: Tests for agent/governance_ui/state/constants.py.
Tests: color maps, navigation items, form options, icon maps.
"""

from agent.governance_ui.state.constants import (
    STATUS_COLORS,
    PRIORITY_COLORS,
    RISK_COLORS,
    TOOLBAR_HEALTH_ICONS,
    CATEGORY_ICONS,
    NAVIGATION_ITEMS,
    TRUST_LEVEL_COLORS,
    PROPOSAL_STATUS_COLORS,
    EVENT_TYPE_COLORS,
    EVENT_TYPE_ICONS,
    SEVERITY_COLORS,
    RULE_CATEGORIES,
    RULE_PRIORITIES,
    RULE_STATUSES,
    TASK_STATUSES,
    TASK_PHASES,
    GAP_PRIORITY_COLORS,
    TASK_STATUS_COLORS,
    EXECUTIVE_STATUS_COLORS,
    SECTION_STATUS_COLORS,
    CHAT_ROLE_COLORS,
    CHAT_STATUS_ICONS,
    EXECUTION_EVENT_TYPES,
)


# ── Color Maps ────────────────────────────────────────


class TestStatusColors:
    def test_active_is_success(self):
        assert STATUS_COLORS["ACTIVE"] == "success"

    def test_deprecated_is_warning(self):
        assert STATUS_COLORS["DEPRECATED"] == "warning"

    def test_all_keys(self):
        assert set(STATUS_COLORS.keys()) == {"ACTIVE", "DRAFT", "DEPRECATED", "PROPOSED"}


class TestPriorityColors:
    def test_critical_is_error(self):
        assert PRIORITY_COLORS["CRITICAL"] == "error"

    def test_all_keys(self):
        assert set(PRIORITY_COLORS.keys()) == {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


class TestRiskColors:
    def test_critical_is_error(self):
        assert RISK_COLORS["CRITICAL"] == "error"

    def test_low_is_success(self):
        assert RISK_COLORS["LOW"] == "success"


# ── Navigation ────────────────────────────────────────


class TestNavigationItems:
    def test_has_items(self):
        assert len(NAVIGATION_ITEMS) >= 10

    def test_each_has_required_fields(self):
        for item in NAVIGATION_ITEMS:
            assert "title" in item
            assert "icon" in item
            assert "value" in item

    def test_chat_first(self):
        assert NAVIGATION_ITEMS[0]["value"] == "chat"

    def test_all_values_unique(self):
        values = [item["value"] for item in NAVIGATION_ITEMS]
        assert len(values) == len(set(values))

    def test_icons_are_mdi(self):
        for item in NAVIGATION_ITEMS:
            assert item["icon"].startswith("mdi-")

    def test_key_items_present(self):
        values = {item["value"] for item in NAVIGATION_ITEMS}
        expected = {"chat", "rules", "agents", "tasks", "sessions", "trust"}
        assert expected.issubset(values)


# ── Form Options ──────────────────────────────────────


class TestFormOptions:
    def test_rule_categories(self):
        assert "governance" in RULE_CATEGORIES
        assert "technical" in RULE_CATEGORIES
        assert "operational" in RULE_CATEGORIES

    def test_rule_priorities(self):
        assert RULE_PRIORITIES == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    def test_rule_statuses(self):
        assert "ACTIVE" in RULE_STATUSES
        assert "DEPRECATED" in RULE_STATUSES

    def test_task_statuses(self):
        assert "TODO" in TASK_STATUSES
        assert "IN_PROGRESS" in TASK_STATUSES
        assert "DONE" in TASK_STATUSES

    def test_task_phases(self):
        assert len(TASK_PHASES) >= 5


# ── Icon Maps ─────────────────────────────────────────


class TestIconMaps:
    def test_toolbar_health_icons(self):
        assert TOOLBAR_HEALTH_ICONS["healthy"] == "mdi-shield-check"
        assert "unhealthy" in TOOLBAR_HEALTH_ICONS

    def test_category_icons_all_mdi(self):
        for icon in CATEGORY_ICONS.values():
            assert icon.startswith("mdi-")

    def test_event_type_icons_match_colors(self):
        assert set(EVENT_TYPE_ICONS.keys()) == set(EVENT_TYPE_COLORS.keys())

    def test_chat_status_icons(self):
        assert "pending" in CHAT_STATUS_ICONS
        assert "complete" in CHAT_STATUS_ICONS


# ── Execution Event Types ─────────────────────────────


class TestExecutionEventTypes:
    def test_has_icon_and_color(self):
        for event_type, config in EXECUTION_EVENT_TYPES.items():
            assert "icon" in config
            assert "color" in config

    def test_key_events_present(self):
        assert "claimed" in EXECUTION_EVENT_TYPES
        assert "completed" in EXECUTION_EVENT_TYPES
        assert "failed" in EXECUTION_EVENT_TYPES


# ── Trust and Proposal Colors ─────────────────────────


class TestTrustColors:
    def test_trust_levels(self):
        assert TRUST_LEVEL_COLORS["HIGH"] == "success"
        assert TRUST_LEVEL_COLORS["LOW"] == "error"

    def test_proposal_statuses(self):
        assert PROPOSAL_STATUS_COLORS["approved"] == "success"
        assert PROPOSAL_STATUS_COLORS["rejected"] == "error"

    def test_severity_colors(self):
        assert SEVERITY_COLORS["CRITICAL"] == "error"
        assert SEVERITY_COLORS["INFO"] == "info"
