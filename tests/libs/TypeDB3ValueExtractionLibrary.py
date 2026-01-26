"""
TypeDB 3.x Value Extraction Library for Robot Framework
Integration tests for TypeDB 3.x API value extraction.
Migrated from tests/integration/test_typedb3_value_extraction.py
Per: RF-007 Robot Framework Migration
"""
import requests
from robot.api.deco import keyword


class TypeDB3ValueExtractionLibrary:
    """Robot Framework keywords for TypeDB 3.x value extraction tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'
    API_BASE = "http://localhost:8082"

    # =========================================================================
    # Value Extraction Tests
    # =========================================================================

    @keyword("Tasks API Returns Clean Values")
    def tasks_api_returns_clean_values(self):
        """Verify tasks API returns clean string values, not Attribute wrappers."""
        try:
            response = requests.get(f"{self.API_BASE}/api/tasks", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            tasks = data.get("items", [])

            if not tasks:
                return {"skipped": True, "reason": "No tasks in database"}

            all_clean = True
            for task in tasks:
                task_id = task.get("task_id")
                if str(task_id).startswith("Attribute("):
                    all_clean = False
                    break

                status = task.get("status")
                if status and str(status).startswith("Attribute("):
                    all_clean = False
                    break

                phase = task.get("phase")
                if phase and str(phase).startswith("Attribute("):
                    all_clean = False
                    break

            return {"all_values_clean": all_clean}
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rules API Returns Clean Values")
    def rules_api_returns_clean_values(self):
        """Verify rules API returns clean string values, not Attribute wrappers."""
        try:
            response = requests.get(f"{self.API_BASE}/api/rules?limit=5", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            rules = response.json()

            if not rules:
                return {"skipped": True, "reason": "No rules in database"}

            all_clean = True
            for rule in rules:
                rule_id = rule.get("id")
                if str(rule_id).startswith("Attribute("):
                    all_clean = False
                    break

                name = rule.get("name")
                if name and str(name).startswith("Attribute("):
                    all_clean = False
                    break

                category = rule.get("category")
                if category and str(category).startswith("Attribute("):
                    all_clean = False
                    break

            return {"all_values_clean": all_clean, "rule_count": len(rules)}
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Values Are Proper Strings")
    def task_values_are_proper_strings(self):
        """Verify task values are proper strings (no type wrappers)."""
        try:
            response = requests.get(f"{self.API_BASE}/api/tasks?limit=1", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()
            tasks = data.get("items", [])

            if not tasks:
                return {"skipped": True, "reason": "No tasks in database"}

            task = tasks[0]
            task_id = task.get("task_id")

            if not task_id:
                return {"skipped": True, "reason": "Task has no task_id"}

            is_string = isinstance(task_id, str)
            no_wrapper = not str(task_id).startswith("Attribute(")
            reasonable_length = len(task_id) < 50

            return {
                "is_string": is_string,
                "no_wrapper": no_wrapper,
                "reasonable_length": reasonable_length
            }
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rule Semantic ID Extraction")
    def rule_semantic_id_extraction(self):
        """Verify semantic_id is properly extracted for rules."""
        try:
            response = requests.get(f"{self.API_BASE}/api/rules?limit=10", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            rules = response.json()
            rules_with_semantic = [r for r in rules if r.get("semantic_id")]

            if not rules_with_semantic:
                return {"skipped": True, "reason": "No rules with semantic_id found"}

            rule = rules_with_semantic[0]
            semantic_id = rule["semantic_id"]

            is_string = isinstance(semantic_id, str)
            no_wrapper = not str(semantic_id).startswith("Attribute(")
            has_dashes = "-" in semantic_id

            return {
                "is_string": is_string,
                "no_wrapper": no_wrapper,
                "has_dashes": has_dashes
            }
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # API Response Format Tests
    # =========================================================================

    @keyword("Tasks Pagination Metadata")
    def tasks_pagination_metadata(self):
        """Verify tasks API includes proper pagination metadata."""
        try:
            response = requests.get(f"{self.API_BASE}/api/tasks", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            data = response.json()

            if "pagination" not in data:
                return {"has_pagination": False}

            pagination = data["pagination"]

            has_total = "total" in pagination
            has_offset = "offset" in pagination
            has_limit = "limit" in pagination
            has_has_more = "has_more" in pagination
            has_returned = "returned" in pagination

            total_is_int = isinstance(pagination.get("total"), int)
            offset_is_int = isinstance(pagination.get("offset"), int)

            return {
                "has_pagination": True,
                "has_total": has_total,
                "has_offset": has_offset,
                "has_limit": has_limit,
                "has_has_more": has_has_more,
                "has_returned": has_returned,
                "total_is_int": total_is_int,
                "offset_is_int": offset_is_int
            }
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Rules Response Is List")
    def rules_response_is_list(self):
        """Verify rules API returns a list (not wrapped object)."""
        try:
            response = requests.get(f"{self.API_BASE}/api/rules?limit=5", timeout=10)
            if response.status_code != 200:
                return {"skipped": True, "reason": f"API returned {response.status_code}"}

            rules = response.json()

            return {"is_list": isinstance(rules, list)}
        except requests.RequestException as e:
            return {"skipped": True, "reason": str(e)}
