"""
Robot Framework Library for UI Filter Function Tests.

Per DOC-SIZE-01-v1: Split from test_governance_ui.py.
Migrated from tests/unit/ui/test_ui_filters.py
"""
from robot.api.deco import keyword


class UIFiltersLibrary:
    """Library for testing rule filter pure functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def _get_sample_rules(self):
        """Sample rules for filter testing."""
        return [
            {'rule_id': 'RULE-001', 'status': 'ACTIVE', 'category': 'governance', 'title': 'Session Evidence'},
            {'rule_id': 'RULE-002', 'status': 'ACTIVE', 'category': 'technical', 'title': 'Code Standards'},
            {'rule_id': 'RULE-003', 'status': 'DRAFT', 'category': 'governance', 'title': 'Gap Tracking'},
        ]

    @keyword("Filter Rules By Status Works")
    def filter_rules_by_status_works(self):
        """Should filter rules by status."""
        try:
            from agent.governance_ui import filter_rules_by_status

            sample_rules = self._get_sample_rules()
            active = filter_rules_by_status(sample_rules, 'ACTIVE')

            correct_count = len(active) == 2
            all_active = all(rule['status'] == 'ACTIVE' for rule in active)

            return {
                "correct_count": correct_count,
                "all_active": all_active,
                "filtered_count": len(active)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Rules By Category Works")
    def filter_rules_by_category_works(self):
        """Should filter rules by category."""
        try:
            from agent.governance_ui import filter_rules_by_category

            sample_rules = self._get_sample_rules()
            governance = filter_rules_by_category(sample_rules, 'governance')

            correct_count = len(governance) == 2
            all_governance = all(rule['category'] == 'governance' for rule in governance)

            return {
                "correct_count": correct_count,
                "all_governance": all_governance,
                "filtered_count": len(governance)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Filter Rules By Search Works")
    def filter_rules_by_search_works(self):
        """Should filter rules by search query."""
        try:
            from agent.governance_ui import filter_rules_by_search

            sample_rules = self._get_sample_rules()
            matches = filter_rules_by_search(sample_rules, 'Evidence')

            correct_count = len(matches) == 1
            correct_match = matches[0]['rule_id'] == 'RULE-001' if matches else False

            return {
                "correct_count": correct_count,
                "correct_match": correct_match,
                "matched_count": len(matches)
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Sort Rules Works")
    def sort_rules_works(self):
        """Should sort rules by column."""
        try:
            from agent.governance_ui import sort_rules

            sample_rules = self._get_sample_rules()
            sorted_asc = sort_rules(sample_rules, 'rule_id', ascending=True)
            sorted_desc = sort_rules(sample_rules, 'rule_id', ascending=False)

            asc_correct = sorted_asc[0]['rule_id'] == 'RULE-001' and sorted_asc[-1]['rule_id'] == 'RULE-003'
            desc_correct = sorted_desc[0]['rule_id'] == 'RULE-003'

            return {
                "asc_first_correct": sorted_asc[0]['rule_id'] == 'RULE-001',
                "asc_last_correct": sorted_asc[-1]['rule_id'] == 'RULE-003',
                "desc_first_correct": sorted_desc[0]['rule_id'] == 'RULE-003',
                "both_correct": asc_correct and desc_correct
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
