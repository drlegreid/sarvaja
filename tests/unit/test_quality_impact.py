"""
Tests for rule impact analysis module.

Per GAP-FILE-025: Pure function impact calculation.
Covers impact scoring, transitive dependents, and recommendations.

Created: 2026-01-30
"""

import pytest

from governance.quality.impact import calculate_rule_impact


class TestCalculateRuleImpact:
    """Test calculate_rule_impact pure function."""

    def test_no_dependents_low_priority(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Test", "priority": "LOW", "category": "operational"},
            dependents_cache={},
            all_rules={"R1": {"name": "Test"}}
        )
        assert result["rule_id"] == "R1"
        assert result["impact_score"] == 10  # LOW priority only
        assert "LOW RISK" in result["recommendation"]
        assert result["direct_dependents"] == []
        assert result["all_affected_rules"] == []

    def test_critical_priority_no_dependents(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Critical", "priority": "CRITICAL", "category": "operational"},
            dependents_cache={},
            all_rules={"R1": {}}
        )
        assert result["impact_score"] == 40  # CRITICAL=40
        assert "MEDIUM RISK" in result["recommendation"]

    def test_governance_category_bonus(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Gov", "priority": "MEDIUM", "category": "governance"},
            dependents_cache={},
            all_rules={"R1": {}}
        )
        # MEDIUM=20 + governance=20 = 40
        assert result["impact_score"] == 40

    def test_direct_dependents(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Base", "priority": "HIGH", "category": "technical"},
            dependents_cache={"R1": {"R2", "R3"}},
            all_rules={"R1": {}, "R2": {}, "R3": {}}
        )
        # HIGH=30 + 2 dependents*10=20 = 50
        assert result["impact_score"] == 50
        assert len(result["direct_dependents"]) == 2
        assert set(result["direct_dependents"]) == {"R2", "R3"}

    def test_transitive_dependents(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Root", "priority": "HIGH", "category": "governance"},
            dependents_cache={
                "R1": {"R2"},
                "R2": {"R3"},
                "R3": {"R4"},
            },
            all_rules={"R1": {}, "R2": {}, "R3": {}, "R4": {}}
        )
        # HIGH=30 + 3 total dependents*10=30 + governance=20 = 80
        assert result["impact_score"] == 80
        assert len(result["all_affected_rules"]) == 3
        assert set(result["all_affected_rules"]) == {"R2", "R3", "R4"}
        assert "HIGH RISK" in result["recommendation"]

    def test_max_score_capped_at_100(self):
        # 5+ dependents with CRITICAL priority and governance category
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Max", "priority": "CRITICAL", "category": "governance"},
            dependents_cache={"R1": {f"R{i}" for i in range(2, 12)}},
            all_rules={}
        )
        assert result["impact_score"] == 100

    def test_dependents_impact_capped_at_40(self):
        # Many dependents, cap at 40
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Hub", "priority": "LOW", "category": "operational"},
            dependents_cache={"R1": {f"R{i}" for i in range(2, 20)}},
            all_rules={}
        )
        # LOW=10 + min(18*10, 40)=40 = 50
        assert result["impact_score"] == 50

    def test_unknown_priority_defaults_medium(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Unknown", "category": "technical"},
            dependents_cache={},
            all_rules={}
        )
        # default MEDIUM=20
        assert result["impact_score"] == 20

    def test_missing_rule_data(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={},
            dependents_cache={},
            all_rules={}
        )
        assert result["rule_name"] == "Unknown"
        assert result["priority"] is None
        assert result["category"] is None
        # default MEDIUM=20
        assert result["impact_score"] == 20

    def test_strategic_category_bonus(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Strat", "priority": "MEDIUM", "category": "strategic"},
            dependents_cache={},
            all_rules={}
        )
        # MEDIUM=20 + strategic=20 = 40
        assert result["impact_score"] == 40

    def test_architecture_category_bonus(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Arch", "priority": "MEDIUM", "category": "architecture"},
            dependents_cache={},
            all_rules={}
        )
        # MEDIUM=20 + architecture=20 = 40
        assert result["impact_score"] == 40

    def test_high_risk_recommendation(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "X", "priority": "CRITICAL", "category": "governance"},
            dependents_cache={"R1": {"R2"}},
            all_rules={}
        )
        # CRITICAL=40 + 1*10=10 + governance=20 = 70
        assert result["impact_score"] == 70
        assert "HIGH RISK" in result["recommendation"]

    def test_medium_risk_recommendation(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "X", "priority": "HIGH", "category": "operational"},
            dependents_cache={"R1": {"R2"}},
            all_rules={}
        )
        # HIGH=30 + 1*10=10 = 40
        assert result["impact_score"] == 40
        assert "MEDIUM RISK" in result["recommendation"]

    def test_low_risk_recommendation(self):
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "X", "priority": "LOW", "category": "operational"},
            dependents_cache={},
            all_rules={}
        )
        # LOW=10
        assert result["impact_score"] == 10
        assert "LOW RISK" in result["recommendation"]

    def test_circular_dependents_no_infinite_loop(self):
        """Transitive traversal should handle cycles without infinite loop."""
        result = calculate_rule_impact(
            rule_id="R1",
            rule={"name": "Cycle", "priority": "MEDIUM", "category": "operational"},
            dependents_cache={
                "R1": {"R2"},
                "R2": {"R3"},
                "R3": {"R1"},  # Cycle back
            },
            all_rules={}
        )
        # Should complete without infinite loop
        assert result["rule_id"] == "R1"
        assert set(result["all_affected_rules"]) == {"R2", "R3", "R1"}
