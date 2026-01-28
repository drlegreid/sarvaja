"""
Test Rule Linker - Maps tests to governance rules/gaps.

Per GAP-TEST-EVIDENCE-001: Rule traceability in test evidence.
Per RD-TESTING-STRATEGY TEST-004: Test restructuring for rules conformity.

Created: 2026-01-21
"""

import re
from typing import List, Optional, Dict, Set, Tuple


# Patterns for extracting rule/gap references from test docstrings and names
RULE_PATTERNS = [
    r"RULE-\d{3}",  # Legacy: RULE-001, RULE-012
    r"[A-Z]+-[A-Z]+-\d{2}-v\d+",  # Semantic: SESSION-EVID-01-v1
]

GAP_PATTERNS = [
    r"GAP-[A-Z]+-\d{3}",  # GAP-MCP-001
    r"GAP-[A-Z]+-[A-Z]+-\d{3}",  # GAP-UI-AUDIT-001
]


class RuleLinker:
    """
    Links tests to governance rules and gaps. Renamed to avoid pytest collection.

    Usage:
        linker = RuleLinker()

        # Extract from docstring
        rules, gaps = linker.extract_references('''
            Test validates RULE-001 compliance.
            Per GAP-UI-001: Button visibility fix.
        ''')
        # rules = ['RULE-001']
        # gaps = ['GAP-UI-001']

        # Use pytest marker
        @pytest.mark.rules("RULE-001", "SESSION-EVID-01-v1")
        @pytest.mark.gaps("GAP-TEST-001")
        def test_example():
            pass
    """

    def __init__(self):
        """Initialize linker with compiled patterns."""
        self._rule_patterns = [re.compile(p) for p in RULE_PATTERNS]
        self._gap_patterns = [re.compile(p) for p in GAP_PATTERNS]
        self._test_rule_map: Dict[str, Set[str]] = {}
        self._test_gap_map: Dict[str, Set[str]] = {}

    def extract_references(
        self,
        text: str
    ) -> Tuple[List[str], List[str]]:
        """
        Extract rule and gap references from text.

        Args:
            text: Text to search (docstring, comment, etc.)

        Returns:
            Tuple of (rules, gaps) lists
        """
        rules: Set[str] = set()
        gaps: Set[str] = set()

        if not text:
            return [], []

        # Extract rules
        for pattern in self._rule_patterns:
            matches = pattern.findall(text)
            rules.update(matches)

        # Extract gaps
        for pattern in self._gap_patterns:
            matches = pattern.findall(text)
            gaps.update(matches)

        return sorted(rules), sorted(gaps)

    def register_test(
        self,
        test_id: str,
        docstring: Optional[str] = None,
        rules: Optional[List[str]] = None,
        gaps: Optional[List[str]] = None
    ) -> Tuple[List[str], List[str]]:
        """
        Register a test with its rule/gap links.

        Args:
            test_id: Test identifier (e.g., pytest nodeid)
            docstring: Test docstring for reference extraction
            rules: Explicit rule IDs from markers
            gaps: Explicit gap IDs from markers

        Returns:
            Tuple of (all_rules, all_gaps) for this test
        """
        all_rules: Set[str] = set(rules or [])
        all_gaps: Set[str] = set(gaps or [])

        # Extract from docstring
        if docstring:
            doc_rules, doc_gaps = self.extract_references(docstring)
            all_rules.update(doc_rules)
            all_gaps.update(doc_gaps)

        # Store mappings
        self._test_rule_map[test_id] = all_rules
        self._test_gap_map[test_id] = all_gaps

        return sorted(all_rules), sorted(all_gaps)

    def get_test_rules(self, test_id: str) -> List[str]:
        """Get rules linked to a test."""
        return sorted(self._test_rule_map.get(test_id, set()))

    def get_test_gaps(self, test_id: str) -> List[str]:
        """Get gaps linked to a test."""
        return sorted(self._test_gap_map.get(test_id, set()))

    def get_tests_for_rule(self, rule_id: str) -> List[str]:
        """Get all tests that validate a specific rule."""
        return [
            test_id
            for test_id, rules in self._test_rule_map.items()
            if rule_id in rules
        ]

    def get_tests_for_gap(self, gap_id: str) -> List[str]:
        """Get all tests that address a specific gap."""
        return [
            test_id
            for test_id, gaps in self._test_gap_map.items()
            if gap_id in gaps
        ]

    def get_coverage_summary(self) -> Dict[str, int]:
        """Get summary of rule/gap coverage.

        Returns:
            Dictionary with coverage statistics
        """
        all_rules: Set[str] = set()
        all_gaps: Set[str] = set()
        linked_tests = 0

        for rules in self._test_rule_map.values():
            all_rules.update(rules)
        for gaps in self._test_gap_map.values():
            all_gaps.update(gaps)

        # Count tests with at least one link
        for test_id in self._test_rule_map:
            if self._test_rule_map.get(test_id) or self._test_gap_map.get(test_id):
                linked_tests += 1

        return {
            "total_tests": len(self._test_rule_map),
            "linked_tests": linked_tests,
            "unique_rules": len(all_rules),
            "unique_gaps": len(all_gaps),
            "coverage_rate": f"{(linked_tests / len(self._test_rule_map) * 100):.1f}%"
            if self._test_rule_map else "0%",
        }


# Pytest markers for rule/gap linking
def pytest_configure(config):
    """Register custom markers for rule/gap linking."""
    config.addinivalue_line(
        "markers",
        "rules(*rule_ids): Mark test as validating specific governance rules"
    )
    config.addinivalue_line(
        "markers",
        "gaps(*gap_ids): Mark test as addressing specific gaps"
    )
