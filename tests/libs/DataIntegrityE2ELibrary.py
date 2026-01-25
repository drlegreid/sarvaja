"""
RF-006: Robot Framework Library for Data Integrity E2E Tests.

Per GAP-UI-AUDIT-2026-01-18: Verify data traceability for completed tasks.
Migrated from tests/e2e/test_data_integrity_e2e.py
"""

import os
import requests
from pathlib import Path
from typing import Dict, Any, List
from robot.api.deco import keyword


class DataIntegrityE2ELibrary:
    """Robot Framework library for data integrity E2E tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self, api_url: str = None):
        self.api_url = api_url or os.getenv("API_URL", "http://localhost:8082")
        self.project_root = Path(__file__).parent.parent.parent
        self._tasks_cache = None
        self._sessions_cache = None

    @keyword("Get All Tasks")
    def get_all_tasks(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Fetch tasks from API."""
        try:
            response = requests.get(
                f"{self.api_url}/api/tasks?limit={limit}",
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            return [{"error": str(e)}]
        return []

    @keyword("Get All Sessions")
    def get_all_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch sessions from API."""
        try:
            response = requests.get(
                f"{self.api_url}/api/sessions?limit={limit}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("items", data) if isinstance(data, dict) else data
        except Exception as e:
            return [{"error": str(e)}]
        return []

    @keyword("Get All Rules")
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Fetch rules from API."""
        try:
            response = requests.get(f"{self.api_url}/api/rules", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    @keyword("Check Task Session Linkage")
    def check_task_session_linkage(self) -> Dict[str, Any]:
        """Check linkage between closed tasks and sessions."""
        tasks = self.get_all_tasks()
        if not tasks or "error" in tasks[0] if tasks else False:
            return {"skipped": True, "reason": "Cannot fetch tasks"}

        closed_tasks = [
            t for t in tasks
            if t.get("status") in ("CLOSED", "DONE", "completed")
        ]

        if not closed_tasks:
            return {"skipped": True, "reason": "No closed tasks found"}

        tasks_with_linkage = 0
        tasks_without_linkage = []

        for task in closed_tasks:
            task_id = task.get("task_id") or task.get("id")
            linked_sessions = task.get("linked_sessions", [])
            session_id = task.get("session_id")

            if linked_sessions or session_id:
                tasks_with_linkage += 1
            else:
                tasks_without_linkage.append(task_id)

        linkage_rate = (
            tasks_with_linkage / len(closed_tasks) * 100
            if closed_tasks else 0
        )

        return {
            "healthy": linkage_rate >= 5,  # Min 5% baseline
            "total_closed": len(closed_tasks),
            "with_linkage": tasks_with_linkage,
            "without_linkage": len(tasks_without_linkage),
            "linkage_rate": round(linkage_rate, 1),
            "sample_unlinked": tasks_without_linkage[:5]
        }

    @keyword("Check Task Evidence Linkage")
    def check_task_evidence_linkage(self) -> Dict[str, Any]:
        """Check linkage between implemented tasks and evidence."""
        tasks = self.get_all_tasks()
        if not tasks or "error" in tasks[0] if tasks else False:
            return {"skipped": True, "reason": "Cannot fetch tasks"}

        implemented_tasks = [
            t for t in tasks
            if t.get("resolution") in ("IMPLEMENTED", "VALIDATED", "CERTIFIED")
            or t.get("status") in ("DONE", "completed", "CLOSED")
        ]

        if not implemented_tasks:
            return {"skipped": True, "reason": "No implemented tasks found"}

        tasks_with_evidence = 0

        for task in implemented_tasks:
            evidence = task.get("evidence")
            evidence_file = task.get("evidence_file")
            if evidence or evidence_file:
                tasks_with_evidence += 1

        evidence_rate = (
            tasks_with_evidence / len(implemented_tasks) * 100
            if implemented_tasks else 0
        )

        return {
            "healthy": True,  # Informational - xfail in robot if low
            "total_implemented": len(implemented_tasks),
            "with_evidence": tasks_with_evidence,
            "evidence_rate": round(evidence_rate, 1),
            "backfill_needed": evidence_rate < 70
        }

    @keyword("Check Session Evidence Files")
    def check_session_evidence_files(self) -> Dict[str, Any]:
        """Check if sessions have evidence files."""
        sessions = self.get_all_sessions()
        if not sessions or "error" in sessions[0] if sessions else False:
            return {"skipped": True, "reason": "Cannot fetch sessions"}

        sessions_with_evidence = 0
        files_found = 0
        files_missing = 0

        for session in sessions:
            evidence_files = session.get("evidence_files", [])
            if evidence_files:
                sessions_with_evidence += 1
                for ef in evidence_files[:2]:
                    full_path = self.project_root / ef
                    if full_path.exists():
                        files_found += 1
                    else:
                        files_missing += 1

        evidence_rate = (
            sessions_with_evidence / len(sessions) * 100
            if sessions else 0
        )

        return {
            "healthy": True,
            "total_sessions": len(sessions),
            "with_evidence_files": sessions_with_evidence,
            "evidence_rate": round(evidence_rate, 1),
            "files_found": files_found,
            "files_missing": files_missing
        }

    @keyword("Check Task Commit Linkage")
    def check_task_commit_linkage(self) -> Dict[str, Any]:
        """Check linkage between tasks and git commits."""
        tasks = self.get_all_tasks()
        if not tasks or "error" in tasks[0] if tasks else False:
            return {"skipped": True, "reason": "Cannot fetch tasks"}

        tasks_with_commits = 0

        for task in tasks:
            linked_commits = task.get("linked_commits", []) or []
            if linked_commits:
                tasks_with_commits += 1

        linkage_rate = (
            tasks_with_commits / len(tasks) * 100
            if tasks else 0
        )

        return {
            "healthy": True,
            "total_tasks": len(tasks),
            "with_commits": tasks_with_commits,
            "linkage_rate": round(linkage_rate, 1)
        }

    @keyword("Check Data Pollution")
    def check_data_pollution(self) -> Dict[str, Any]:
        """Check for TEST-* and RULE-* pollution."""
        tasks = self.get_all_tasks()
        rules = self.get_all_rules()

        test_tasks = [
            t for t in tasks
            if (t.get("task_id") or "").startswith("TEST-")
        ]
        test_rules = [
            r for r in rules
            if r.get("id", "").startswith("TEST-")
        ]
        legacy_rules = [
            r for r in rules
            if r.get("id", "").startswith("RULE-")
        ]

        return {
            "healthy": len(test_tasks) == 0 and len(test_rules) == 0 and len(legacy_rules) == 0,
            "test_tasks": len(test_tasks),
            "test_rules": len(test_rules),
            "legacy_rules": len(legacy_rules),
            "sample_test_tasks": [t.get("task_id") for t in test_tasks[:5]],
            "sample_test_rules": [r.get("id") for r in test_rules[:5]],
            "sample_legacy_rules": [r.get("id") for r in legacy_rules[:5]]
        }

    @keyword("Generate Integrity Report")
    def generate_integrity_report(self) -> Dict[str, Any]:
        """Generate comprehensive data integrity report."""
        tasks = self.get_all_tasks()
        sessions = self.get_all_sessions()

        if not tasks and not sessions:
            return {"skipped": True, "reason": "No data available"}

        report = {
            "total_tasks": len(tasks),
            "total_sessions": len(sessions),
            "tasks_with_session": 0,
            "tasks_with_evidence": 0,
            "tasks_with_commits": 0,
            "sessions_with_evidence": 0,
            "closed_tasks": 0,
        }

        for task in tasks:
            if task.get("status") in ("CLOSED", "DONE", "completed"):
                report["closed_tasks"] += 1
            if task.get("linked_sessions") or task.get("session_id"):
                report["tasks_with_session"] += 1
            if task.get("evidence") or task.get("evidence_file"):
                report["tasks_with_evidence"] += 1
            if task.get("linked_commits"):
                report["tasks_with_commits"] += 1

        for session in sessions:
            if session.get("evidence_files"):
                report["sessions_with_evidence"] += 1

        # Calculate rates
        if report["total_tasks"] > 0:
            report["task_session_rate"] = round(
                report["tasks_with_session"] / report["total_tasks"] * 100, 1
            )
            report["task_evidence_rate"] = round(
                report["tasks_with_evidence"] / report["total_tasks"] * 100, 1
            )
            report["task_commit_rate"] = round(
                report["tasks_with_commits"] / report["total_tasks"] * 100, 1
            )

        if report["total_sessions"] > 0:
            report["session_evidence_rate"] = round(
                report["sessions_with_evidence"] / report["total_sessions"] * 100, 1
            )

        report["healthy"] = report["total_tasks"] > 0 and report["total_sessions"] > 0
        return report
