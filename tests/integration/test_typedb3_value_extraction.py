"""
Integration Tests for TypeDB 3.x Value Extraction.

Per GAP-DATA-INTEGRITY-001: Verifies TypeDB 3.x API returns clean values
instead of Attribute(...) wrapper strings.

Created: 2026-01-17
"""

import pytest
import requests

# API base URL
API_BASE = "http://localhost:8082"


class TestTypeDB3ValueExtraction:
    """Tests for TypeDB 3.x attribute value extraction."""

    def test_tasks_api_returns_clean_values(self):
        """Verify tasks API returns clean string values, not Attribute wrappers."""
        response = requests.get(f"{API_BASE}/api/tasks", timeout=10)
        assert response.status_code == 200

        data = response.json()
        tasks = data.get("items", [])

        # Skip if no tasks (valid state)
        if not tasks:
            pytest.skip("No tasks in database")

        for task in tasks:
            task_id = task.get("task_id")
            # Value should NOT contain Attribute( wrapper
            assert not str(task_id).startswith("Attribute("), \
                f"task_id contains wrapper: {task_id}"

            status = task.get("status")
            if status:
                assert not str(status).startswith("Attribute("), \
                    f"status contains wrapper: {status}"

            phase = task.get("phase")
            if phase:
                assert not str(phase).startswith("Attribute("), \
                    f"phase contains wrapper: {phase}"

    def test_rules_api_returns_clean_values(self):
        """Verify rules API returns clean string values, not Attribute wrappers."""
        response = requests.get(f"{API_BASE}/api/rules?limit=5", timeout=10)
        assert response.status_code == 200

        data = response.json()
        rules = data.get("items", data) if isinstance(data, dict) else data

        # Should have at least some rules
        assert len(rules) > 0, "Expected at least 1 rule"

        for rule in rules:
            rule_id = rule.get("id")
            # Value should NOT contain Attribute( wrapper
            assert not str(rule_id).startswith("Attribute("), \
                f"rule id contains wrapper: {rule_id}"

            name = rule.get("name")
            if name:
                assert not str(name).startswith("Attribute("), \
                    f"name contains wrapper: {name}"

            category = rule.get("category")
            if category:
                assert not str(category).startswith("Attribute("), \
                    f"category contains wrapper: {category}"

    def test_task_values_are_proper_strings(self):
        """Verify task values are proper strings (no type wrappers)."""
        response = requests.get(f"{API_BASE}/api/tasks?limit=1", timeout=10)
        assert response.status_code == 200

        data = response.json()
        tasks = data.get("items", [])

        if not tasks:
            pytest.skip("No tasks in database")

        task = tasks[0]

        # task_id should be a simple string like "P11.3" not "Attribute(task-id: "P11.3")"
        task_id = task.get("task_id")
        if task_id:
            assert isinstance(task_id, str), "task_id should be string"
            assert ":" not in task_id or task_id.count(":") <= 1, \
                f"task_id looks like Attribute format: {task_id}"
            # Simple IDs like P11.3 should be short
            if "." in task_id:
                assert len(task_id) < 20, f"task_id unusually long: {task_id}"

    def test_rule_semantic_id_extraction(self):
        """Verify semantic_id is properly extracted for rules."""
        response = requests.get(f"{API_BASE}/api/rules?limit=10", timeout=10)
        assert response.status_code == 200

        data = response.json()
        rules = data.get("items", data) if isinstance(data, dict) else data

        # Find a rule with semantic_id
        rules_with_semantic = [r for r in rules if r.get("semantic_id")]

        if not rules_with_semantic:
            pytest.skip("No rules with semantic_id found")

        rule = rules_with_semantic[0]
        semantic_id = rule["semantic_id"]

        # Semantic ID should follow pattern like SESSION-EVID-01-v1
        assert isinstance(semantic_id, str), "semantic_id should be string"
        assert not semantic_id.startswith("Attribute("), \
            f"semantic_id contains wrapper: {semantic_id}"
        # Semantic IDs typically have dashes
        assert "-" in semantic_id, f"semantic_id missing dashes: {semantic_id}"


class TestAPIResponseFormat:
    """Tests for API response format consistency."""

    def test_tasks_pagination_metadata(self):
        """Verify tasks API includes proper pagination metadata."""
        response = requests.get(f"{API_BASE}/api/tasks", timeout=10)
        assert response.status_code == 200

        data = response.json()

        # Should have pagination object
        assert "pagination" in data, "Missing pagination metadata"
        pagination = data["pagination"]

        assert "total" in pagination
        assert "offset" in pagination
        assert "limit" in pagination
        assert "has_more" in pagination
        assert "returned" in pagination

        # Values should be integers, not wrapped
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["offset"], int)

    def test_rules_response_is_paginated(self):
        """Verify rules API returns a paginated response with items array."""
        response = requests.get(f"{API_BASE}/api/rules?limit=5", timeout=10)
        assert response.status_code == 200

        data = response.json()

        # Should be a paginated dict with items and pagination
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        assert "items" in data, "Expected 'items' key in paginated response"
        assert "pagination" in data, "Expected 'pagination' key in response"
        assert isinstance(data["items"], list), "items should be a list"
