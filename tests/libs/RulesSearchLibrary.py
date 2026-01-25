"""
RF-004: Robot Framework Library for Rules Search.

Wraps governance/routes/rules/search.py for Robot Framework tests.
Per GAP-UI-SEARCH-001: Server-side rule search testing.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class MockRule:
    """Mock rule for testing."""
    id: str
    name: str
    category: str
    priority: str
    status: str
    directive: str
    created_date: datetime = None


class RulesSearchLibrary:
    """Robot Framework library for Rules Search functions."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self._mock_rules = None

    def create_mock_rules(self) -> List[Dict]:
        """Create standard mock rules for testing."""
        self._mock_rules = [
            MockRule(
                id="RULE-001",
                name="Session Evidence Protocol",
                category="GOVERNANCE",
                priority="CRITICAL",
                status="ACTIVE",
                directive="All sessions MUST produce evidence artifacts"
            ),
            MockRule(
                id="CONTAINER-LIFECYCLE-01-v1",
                name="Container Lifecycle Management",
                category="TECHNICAL",
                priority="HIGH",
                status="ACTIVE",
                directive="Containers must use podman compose"
            ),
            MockRule(
                id="TEST-GUARD-01-v1",
                name="Test Guard Protocol",
                category="OPERATIONAL",
                priority="CRITICAL",
                status="ACTIVE",
                directive="Tests MUST pass before merge"
            ),
            MockRule(
                id="DOC-SIZE-01-v1",
                name="File Size Limit",
                category="OPERATIONAL",
                priority="HIGH",
                status="ACTIVE",
                directive="Files should not exceed 300 lines"
            ),
        ]
        return [{"id": r.id, "name": r.name, "category": r.category,
                 "priority": r.priority, "directive": r.directive}
                for r in self._mock_rules]

    def filter_rules_by_search(self, query: str) -> List[Dict]:
        """Filter mock rules by search query."""
        from governance.routes.rules.search import filter_rules_by_search
        if self._mock_rules is None:
            self.create_mock_rules()
        results = filter_rules_by_search(self._mock_rules, query)
        return [{"id": r.id, "name": r.name, "directive": r.directive} for r in results]

    def get_result_count(self, results: List) -> int:
        """Get count of results."""
        return len(results)

    def get_result_ids(self, results: List[Dict]) -> List[str]:
        """Get list of IDs from results."""
        return [r["id"] for r in results]
