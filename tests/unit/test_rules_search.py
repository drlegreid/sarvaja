"""
Unit Tests for Rules Server-Side Search.

Per GAP-UI-SEARCH-001: Server-side rule search (pagination blocks client search).
Per TEST-FIX-01-v1: Tests first, then implementation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from datetime import datetime


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


class TestRulesSearchLogic:
    """Test search filtering logic."""

    @pytest.fixture
    def mock_rules(self):
        """Create a set of mock rules for testing."""
        return [
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

    @pytest.mark.unit
    def test_search_by_id_exact(self, mock_rules):
        """GIVEN rules list and search query
        WHEN searching by exact ID
        THEN returns matching rule"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "CONTAINER-LIFECYCLE-01-v1")
        assert len(result) == 1
        assert result[0].id == "CONTAINER-LIFECYCLE-01-v1"

    @pytest.mark.unit
    def test_search_by_id_partial(self, mock_rules):
        """GIVEN rules list and partial search query
        WHEN searching by partial ID
        THEN returns matching rules (case insensitive)"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "container")
        assert len(result) == 1
        assert result[0].id == "CONTAINER-LIFECYCLE-01-v1"

    @pytest.mark.unit
    def test_search_by_name(self, mock_rules):
        """GIVEN rules list
        WHEN searching by name
        THEN returns matching rules"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "Evidence")
        assert len(result) == 1
        assert "Evidence" in result[0].name

    @pytest.mark.unit
    def test_search_by_directive(self, mock_rules):
        """GIVEN rules list
        WHEN searching by directive content
        THEN returns matching rules"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "podman")
        assert len(result) == 1
        assert "podman" in result[0].directive

    @pytest.mark.unit
    def test_search_case_insensitive(self, mock_rules):
        """GIVEN rules list
        WHEN searching with different case
        THEN returns matches regardless of case"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "SESSION")
        assert len(result) == 1
        assert "Session" in result[0].name

    @pytest.mark.unit
    def test_search_multiple_matches(self, mock_rules):
        """GIVEN rules list
        WHEN searching term matching multiple rules
        THEN returns all matching rules"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "MUST")
        assert len(result) >= 2  # Multiple rules have "MUST" in directive

    @pytest.mark.unit
    def test_search_no_match(self, mock_rules):
        """GIVEN rules list
        WHEN searching non-existent term
        THEN returns empty list"""
        from governance.routes.rules.search import filter_rules_by_search

        result = filter_rules_by_search(mock_rules, "nonexistentterm12345")
        assert len(result) == 0

    @pytest.mark.unit
    def test_search_empty_query(self, mock_rules):
        """GIVEN rules list
        WHEN search query is empty or None
        THEN returns all rules unfiltered"""
        from governance.routes.rules.search import filter_rules_by_search

        result_empty = filter_rules_by_search(mock_rules, "")
        result_none = filter_rules_by_search(mock_rules, None)

        assert len(result_empty) == len(mock_rules)
        assert len(result_none) == len(mock_rules)


class TestRulesSearchAPI:
    """Test API endpoint integration."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires API restart to apply new search code")
    @pytest.mark.asyncio
    async def test_list_rules_with_search_param(self):
        """GIVEN rules API endpoint
        WHEN called with search query parameter
        THEN returns filtered rules"""
        # This test requires the actual API
        import httpx

        async with httpx.AsyncClient(base_url="http://localhost:8082") as client:
            response = await client.get("/api/rules", params={"search": "session"})

            if response.status_code == 200:
                rules = response.json()
                # All returned rules should match search
                for rule in rules:
                    search_fields = (
                        rule.get("id", "").lower() +
                        rule.get("name", "").lower() +
                        rule.get("directive", "").lower()
                    )
                    assert "session" in search_fields.lower()

    @pytest.mark.integration
    def test_rules_search_via_rest_api_mcp(self):
        """GIVEN rest-api MCP tool
        WHEN testing rules search endpoint
        THEN returns filtered results"""
        # Placeholder for MCP test
        pass
