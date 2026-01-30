"""
Tests for Skill Composition Engine.

Per AGENT-WORKSPACES.md, RULE-011: Agent wisdom composition.
Covers rule filtering by tags, roles, priorities, and wisdom composition.

Created: 2026-01-30
"""

import pytest
from pathlib import Path

from governance.skill_composer import (
    Skill,
    AgentWisdom,
    ROLE_TAG_MAP,
    ROLE_PRIORITY_FILTER,
    filter_rules_by_tags,
    filter_rules_by_role,
    compose_agent_wisdom,
)


# Test fixtures
def _rule(tags="", roles="", priority="MEDIUM"):
    return {"tags": tags, "applicable_roles": roles, "priority": priority}


class TestFilterRulesByTags:
    """Test tag-based rule filtering."""

    def test_matching_tag(self):
        rules = [_rule(tags="governance, quality")]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 1

    def test_no_matching_tag(self):
        rules = [_rule(tags="coding, testing")]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 0

    def test_rules_without_tags_always_included(self):
        rules = [_rule(tags="")]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 1

    def test_none_tags_treated_as_empty(self):
        rules = [{"tags": None}]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 1

    def test_multiple_matching_tags(self):
        rules = [_rule(tags="governance, quality, review")]
        result = filter_rules_by_tags(rules, {"quality", "review"})
        assert len(result) == 1

    def test_mixed_rules(self):
        rules = [
            _rule(tags="governance"),
            _rule(tags="coding"),
            _rule(tags=""),
        ]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 2  # matching + untagged

    def test_case_insensitive(self):
        rules = [_rule(tags="Governance, Quality")]
        result = filter_rules_by_tags(rules, {"governance"})
        assert len(result) == 1

    def test_empty_filter_tags(self):
        rules = [_rule(tags="governance")]
        result = filter_rules_by_tags(rules, set())
        assert len(result) == 0  # Only untagged rules would match


class TestFilterRulesByRole:
    """Test role-based rule filtering."""

    def test_matching_role(self):
        rules = [_rule(roles="CURATOR, CODING")]
        result = filter_rules_by_role(rules, "CURATOR")
        assert len(result) == 1

    def test_no_matching_role(self):
        rules = [_rule(roles="CODING")]
        result = filter_rules_by_role(rules, "CURATOR")
        assert len(result) == 0

    def test_rules_without_roles_always_included(self):
        rules = [_rule(roles="")]
        result = filter_rules_by_role(rules, "CURATOR")
        assert len(result) == 1

    def test_case_insensitive(self):
        rules = [_rule(roles="curator")]
        result = filter_rules_by_role(rules, "CURATOR")
        assert len(result) == 1

    def test_none_roles_treated_as_empty(self):
        rules = [{"applicable_roles": None}]
        result = filter_rules_by_role(rules, "RESEARCH")
        assert len(result) == 1


class TestRoleTagMap:
    """Test ROLE_TAG_MAP configuration."""

    def test_research_tags(self):
        assert "research" in ROLE_TAG_MAP["RESEARCH"]

    def test_coding_tags(self):
        assert "coding" in ROLE_TAG_MAP["CODING"]
        assert "testing" in ROLE_TAG_MAP["CODING"]

    def test_curator_tags(self):
        assert "governance" in ROLE_TAG_MAP["CURATOR"]

    def test_sync_tags(self):
        assert "sync" in ROLE_TAG_MAP["SYNC"]

    def test_all_roles_defined(self):
        assert set(ROLE_TAG_MAP.keys()) == {"RESEARCH", "CODING", "CURATOR", "SYNC"}


class TestRolePriorityFilter:
    """Test ROLE_PRIORITY_FILTER configuration."""

    def test_curator_sees_all(self):
        """Curator role sees all priority levels."""
        assert "LOW" in ROLE_PRIORITY_FILTER["CURATOR"]

    def test_research_only_critical_high(self):
        assert ROLE_PRIORITY_FILTER["RESEARCH"] == ["CRITICAL", "HIGH"]

    def test_coding_includes_medium(self):
        assert "MEDIUM" in ROLE_PRIORITY_FILTER["CODING"]


class TestAgentWisdom:
    """Test AgentWisdom dataclass."""

    def test_to_dict(self):
        wisdom = AgentWisdom(agent_role="CURATOR", rules=[{"id": "R1"}])
        d = wisdom.to_dict()
        assert d["agent_role"] == "CURATOR"
        assert d["rules_count"] == 1
        assert d["skills_count"] == 0

    def test_empty_wisdom(self):
        wisdom = AgentWisdom(agent_role="RESEARCH")
        d = wisdom.to_dict()
        assert d["rules_count"] == 0
        assert d["skills_count"] == 0


class TestComposeAgentWisdom:
    """Test wisdom composition for agent roles."""

    def test_curator_gets_governance_rules(self):
        rules = [
            _rule(tags="governance", roles="", priority="CRITICAL"),
            _rule(tags="coding", roles="CODING", priority="LOW"),
        ]
        wisdom = compose_agent_wisdom("CURATOR", rules)
        assert wisdom.agent_role == "CURATOR"
        # Curator should get governance-tagged rules
        assert len(wisdom.rules) >= 1

    def test_unknown_role_gets_defaults(self):
        rules = [_rule(tags="", roles="", priority="CRITICAL")]
        wisdom = compose_agent_wisdom("UNKNOWN", rules)
        assert wisdom.agent_role == "UNKNOWN"

    def test_no_workspace_no_skills(self):
        wisdom = compose_agent_wisdom("CODING", [], workspace_path=None)
        assert wisdom.skills == []

    def test_wisdom_has_filter_info(self):
        wisdom = compose_agent_wisdom("CODING", [])
        assert "role" in wisdom.rule_filter
        assert wisdom.rule_filter["role"] == "CODING"


class TestSkill:
    """Test Skill dataclass."""

    def test_from_markdown_missing_file(self, tmp_path):
        result = Skill.from_markdown(tmp_path / "nonexistent.md")
        assert result is None

    def test_from_markdown_no_id(self, tmp_path):
        p = tmp_path / "skill.md"
        p.write_text("# Skill: Test\nNo ID field")
        result = Skill.from_markdown(p)
        assert result is None

    def test_from_markdown_valid(self, tmp_path):
        p = tmp_path / "skill.md"
        p.write_text(
            "# Skill: Test Skill\n"
            "**ID:** SKILL-001\n"
            "**Tags:** governance, testing\n"
            "**Requires:** typedb, pytest\n"
            "## Procedure\n"
            "Step 1: Do thing\n"
            "## Evidence Output\n"
            "Output evidence\n"
        )
        skill = Skill.from_markdown(p)
        assert skill is not None
        assert skill.skill_id == "SKILL-001"
        assert skill.name == "Test Skill"
        assert "governance" in skill.tags
        assert "typedb" in skill.requires
        assert "Step 1" in skill.procedure
        assert "Output evidence" in skill.evidence_output
