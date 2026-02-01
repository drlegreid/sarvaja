"""
RF-006: Robot Framework Library for Governance CRUD E2E Tests.

Per GAP-UI-028: Tests must verify actual functionality, not just imports.
Migrated from tests/e2e/test_governance_crud_e2e.py
"""

import os
import uuid
import httpx
from typing import Dict, Any, List, Optional
from robot.api.deco import keyword


class GovernanceCRUDE2ELibrary:
    """Robot Framework library for governance CRUD E2E tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self, api_url: str = None):
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8082")
        self._client = None
        self._typedb_available = None
        self._cleanup_ids = {"tasks": [], "rules": [], "sessions": []}

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(base_url=self.api_url, timeout=30.0)
        return self._client

    @keyword("Generate Unique ID")
    def generate_unique_id(self, prefix: str = "TEST") -> str:
        """Generate unique ID for test entities."""
        return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

    @keyword("Check TypeDB Available")
    def check_typedb_available(self) -> bool:
        """Check if TypeDB is connected via health endpoint."""
        if self._typedb_available is not None:
            return self._typedb_available
        try:
            client = self._get_client()
            response = client.get("/api/health")
            if response.status_code == 200:
                data = response.json()
                self._typedb_available = data.get("typedb_connected", False)
                return self._typedb_available
        except Exception:
            pass
        self._typedb_available = False
        return False

    # =========================================================================
    # Health Check
    # =========================================================================

    @keyword("API Health Check")
    def api_health_check(self) -> Dict[str, Any]:
        """Check API health endpoint."""
        try:
            client = self._get_client()
            response = client.get("/api/health")
            data = response.json() if response.status_code in (200, 503) else {}
            return {
                "healthy": response.status_code == 200,
                "status_code": response.status_code,
                "status": data.get("status"),
                "typedb_connected": data.get("typedb_connected", False),
                "version": data.get("version")
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    # =========================================================================
    # Rules CRUD
    # =========================================================================

    @keyword("Create Rule")
    def create_rule(self, rule_id: str, name: str, category: str = "technical",
                    priority: str = "HIGH", directive: str = None,
                    status: str = "DRAFT") -> Dict[str, Any]:
        """Create a new rule via API."""
        if not self.check_typedb_available():
            return {"skipped": True, "reason": "TypeDB not connected"}

        rule_data = {
            "rule_id": rule_id,
            "name": name,
            "category": category,
            "priority": priority,
            "directive": directive or f"Test rule: {name}",
            "status": status
        }
        try:
            client = self._get_client()
            response = client.post("/api/rules", json=rule_data)
            if response.status_code == 201:
                self._cleanup_ids["rules"].append(rule_id)
                return {"success": True, "rule": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("List Rules")
    def list_rules(self) -> Dict[str, Any]:
        """List all rules via API."""
        if not self.check_typedb_available():
            return {"skipped": True, "reason": "TypeDB not connected"}

        try:
            client = self._get_client()
            response = client.get("/api/rules")
            if response.status_code == 200:
                data = response.json()
                rules = data.get("items", data) if isinstance(data, dict) else data
                return {"success": True, "rules": rules, "count": len(rules)}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Update Rule")
    def update_rule(self, rule_id: str, name: str = None,
                    status: str = None) -> Dict[str, Any]:
        """Update an existing rule via API."""
        if not self.check_typedb_available():
            return {"skipped": True, "reason": "TypeDB not connected"}

        update_data = {}
        if name:
            update_data["name"] = name
        if status:
            update_data["status"] = status

        try:
            client = self._get_client()
            response = client.put(f"/api/rules/{rule_id}", json=update_data)
            if response.status_code == 200:
                return {"success": True, "rule": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Delete Rule")
    def delete_rule(self, rule_id: str) -> Dict[str, Any]:
        """Delete a rule via API."""
        if not self.check_typedb_available():
            return {"skipped": True, "reason": "TypeDB not connected"}

        try:
            client = self._get_client()
            response = client.delete(f"/api/rules/{rule_id}")
            if response.status_code == 204:
                if rule_id in self._cleanup_ids["rules"]:
                    self._cleanup_ids["rules"].remove(rule_id)
                return {"success": True}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Get Rule")
    def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Get a specific rule by ID."""
        if not self.check_typedb_available():
            return {"skipped": True, "reason": "TypeDB not connected"}

        try:
            client = self._get_client()
            response = client.get(f"/api/rules/{rule_id}")
            if response.status_code == 200:
                return {"success": True, "rule": response.json()}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Tasks CRUD
    # =========================================================================

    @keyword("Create Task")
    def create_task(self, task_id: str, description: str, phase: str = "P10",
                    status: str = "TODO", agent_id: str = None) -> Dict[str, Any]:
        """Create a new task via API."""
        task_data = {
            "task_id": task_id,
            "description": description,
            "phase": phase,
            "status": status
        }
        if agent_id:
            task_data["agent_id"] = agent_id

        try:
            client = self._get_client()
            response = client.post("/api/tasks", json=task_data)
            if response.status_code == 201:
                self._cleanup_ids["tasks"].append(task_id)
                return {"success": True, "task": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("List Tasks")
    def list_tasks(self, status: str = None) -> Dict[str, Any]:
        """List tasks via API."""
        try:
            client = self._get_client()
            params = {"status": status} if status else {}
            response = client.get("/api/tasks", params=params)
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                return {"success": True, "tasks": tasks, "count": len(tasks)}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Update Task")
    def update_task(self, task_id: str, status: str = None,
                    agent_id: str = None) -> Dict[str, Any]:
        """Update a task via API."""
        update_data = {}
        if status:
            update_data["status"] = status
        if agent_id:
            update_data["agent_id"] = agent_id

        try:
            client = self._get_client()
            response = client.put(f"/api/tasks/{task_id}", json=update_data)
            if response.status_code == 200:
                return {"success": True, "task": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Delete Task")
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task via API."""
        try:
            client = self._get_client()
            response = client.delete(f"/api/tasks/{task_id}")
            if response.status_code == 204:
                if task_id in self._cleanup_ids["tasks"]:
                    self._cleanup_ids["tasks"].remove(task_id)
                return {"success": True}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Get Available Tasks")
    def get_available_tasks(self) -> Dict[str, Any]:
        """Get tasks available for agent pickup."""
        try:
            client = self._get_client()
            response = client.get("/api/tasks/available")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                return {"success": True, "tasks": tasks, "count": len(tasks)}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Claim Task")
    def claim_task(self, task_id: str, agent_id: str) -> Dict[str, Any]:
        """Claim a task for an agent."""
        try:
            client = self._get_client()
            response = client.put(
                f"/api/tasks/{task_id}/claim",
                params={"agent_id": agent_id}
            )
            if response.status_code == 200:
                return {"success": True, "task": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Complete Task")
    def complete_task(self, task_id: str, evidence: str = None) -> Dict[str, Any]:
        """Complete a claimed task."""
        try:
            client = self._get_client()
            params = {"evidence": evidence} if evidence else {}
            response = client.put(f"/api/tasks/{task_id}/complete", params=params)
            if response.status_code == 200:
                return {"success": True, "task": response.json()}
            return {"success": False, "status_code": response.status_code, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Agents API
    # =========================================================================

    @keyword("List Agents")
    def list_agents(self) -> Dict[str, Any]:
        """List registered agents."""
        try:
            client = self._get_client()
            response = client.get("/api/agents")
            if response.status_code == 200:
                data = response.json()
                agents = data.get("items", data) if isinstance(data, dict) else data
                return {"success": True, "agents": agents, "count": len(agents)}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Get Agent")
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get a specific agent by ID."""
        try:
            client = self._get_client()
            response = client.get(f"/api/agents/{agent_id}")
            if response.status_code == 200:
                return {"success": True, "agent": response.json()}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @keyword("Record Agent Task")
    def record_agent_task(self, agent_id: str) -> Dict[str, Any]:
        """Record an agent task execution."""
        try:
            client = self._get_client()
            response = client.put(f"/api/agents/{agent_id}/task")
            if response.status_code == 200:
                return {"success": True, "agent": response.json()}
            return {"success": False, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # Negative / Validation Tests
    # =========================================================================

    @keyword("Post Rule Raw")
    def post_rule_raw(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST a rule and return raw status code + response."""
        try:
            client = self._get_client()
            response = client.post("/api/rules", json=rule_data)
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            return {"status_code": response.status_code, "body": body}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @keyword("Post Task Raw")
    def post_task_raw(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST a task and return raw status code + response."""
        try:
            client = self._get_client()
            response = client.post("/api/tasks", json=task_data)
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            return {"status_code": response.status_code, "body": body}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @keyword("Post Decision Raw")
    def post_decision_raw(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """POST a decision and return raw status code + response."""
        try:
            client = self._get_client()
            response = client.post("/api/decisions", json=decision_data)
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            return {"status_code": response.status_code, "body": body}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @keyword("Get Resource Raw")
    def get_resource_raw(self, path: str) -> Dict[str, Any]:
        """GET a resource and return raw status code."""
        try:
            client = self._get_client()
            response = client.get(f"/api/{path}")
            return {"status_code": response.status_code}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    @keyword("Delete Resource Raw")
    def delete_resource_raw(self, path: str) -> Dict[str, Any]:
        """DELETE a resource and return raw status code."""
        try:
            client = self._get_client()
            response = client.delete(f"/api/{path}")
            return {"status_code": response.status_code}
        except Exception as e:
            return {"status_code": 0, "error": str(e)}

    # =========================================================================
    # Cleanup
    # =========================================================================

    @keyword("Cleanup Test Data")
    def cleanup_test_data(self) -> Dict[str, Any]:
        """
        Clean up ALL TEST-* entities from the system.

        Performs a full sweep (not just session-tracked IDs) to handle
        residuals from interrupted test runs or other test frameworks.
        """
        cleaned = {"tasks": 0, "rules": 0, "sessions": 0}
        client = self._get_client()

        # Sweep ALL TEST-* tasks from the system
        try:
            response = client.get("/api/tasks?limit=1000")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("items", data) if isinstance(data, dict) else data
                for task in tasks:
                    task_id = task.get("task_id", "")
                    if task_id.startswith("TEST-"):
                        try:
                            if client.delete(f"/api/tasks/{task_id}").status_code == 204:
                                cleaned["tasks"] += 1
                        except Exception:
                            pass
        except Exception:
            pass

        # Sweep ALL TEST-* sessions (end active ones, delete completed)
        try:
            response = client.get("/api/sessions?limit=200")
            if response.status_code == 200:
                data = response.json()
                sessions = data.get("items", data) if isinstance(data, dict) else data
                for session in sessions:
                    sid = session.get("session_id", "")
                    if sid.startswith("TEST-SESSION-") or sid.startswith("TEST-"):
                        try:
                            status = session.get("status", "")
                            if status == "ACTIVE":
                                client.put(f"/api/sessions/{sid}/end")
                            client.delete(f"/api/sessions/{sid}")
                            cleaned["sessions"] += 1
                        except Exception:
                            pass
        except Exception:
            pass

        # Sweep ALL TEST-* rules (requires TypeDB)
        if self.check_typedb_available():
            try:
                response = client.get("/api/rules")
                if response.status_code == 200:
                    data = response.json()
                    rules = data.get("items", data) if isinstance(data, dict) else data
                    for rule in rules:
                        rule_id = rule.get("id", "")
                        if rule_id.startswith("TEST-"):
                            try:
                                if client.delete(f"/api/rules/{rule_id}", params={"archive": "false"}).status_code == 204:
                                    cleaned["rules"] += 1
                            except Exception:
                                pass
            except Exception:
                pass

        # Also clear session-tracked IDs
        self._cleanup_ids = {"tasks": [], "rules": [], "sessions": []}
        return cleaned

    def __del__(self):
        """Close HTTP client on destruction."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
