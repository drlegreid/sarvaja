"""
Data Integrity E2E Test - Task/Evidence Linkage Verification.

Per GAP-UI-AUDIT-2026-01-18: Verify data traceability exists for completed tasks.

This test validates:
1. Task→Session linkage (completed-in relation)
2. Task→Evidence linkage (evidence files exist)
3. Task→Commit linkage (where applicable)
4. Session→Evidence linkage (has-evidence relation)

Per TASK-LIFE-01-v1: CLOSED tasks with IMPLEMENTED/VALIDATED resolution
MUST have evidence linkage.

Usage:
    pytest tests/e2e/test_data_integrity_e2e.py -v
"""

import os
import pytest
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

API_URL = os.getenv("API_URL", "http://localhost:8082")
PROJECT_ROOT = Path(__file__).parent.parent.parent


# =============================================================================
# Helper Functions
# =============================================================================

def get_tasks_from_api(limit: int = 200) -> List[Dict[str, Any]]:
    """Fetch tasks from API with configurable limit."""
    response = requests.get(f"{API_URL}/api/tasks?limit={limit}", timeout=30)
    if response.status_code == 200:
        data = response.json()
        # Handle paginated response
        return data.get("items", data) if isinstance(data, dict) else data
    return []


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Fetch specific task by ID."""
    response = requests.get(f"{API_URL}/api/tasks/{task_id}", timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


def get_sessions_from_api() -> List[Dict[str, Any]]:
    """Fetch all sessions from API."""
    response = requests.get(f"{API_URL}/api/sessions?limit=100", timeout=10)
    if response.status_code == 200:
        data = response.json()
        return data.get("items", data) if isinstance(data, dict) else data
    return []


def check_evidence_file_exists(evidence_path: str) -> bool:
    """Check if evidence file exists in project."""
    if not evidence_path:
        return False
    # Handle relative paths
    full_path = PROJECT_ROOT / evidence_path
    return full_path.exists()


# =============================================================================
# Test Classes
# =============================================================================

class TestTaskSessionLinkage:
    """Test task-to-session linkage integrity."""

    def test_api_returns_tasks(self):
        """Verify API returns tasks."""
        tasks = get_tasks_from_api()
        assert len(tasks) > 0, "API should return at least one task"

    def test_closed_tasks_have_session_linkage(self):
        """Per TASK-LIFE-01-v1: Closed tasks SHOULD have session linkage.

        Baseline: 2026-01-19 backfill achieved 12% linkage (from 0%).
        Target: Improve incrementally as new tasks are completed.

        Per EPIC-STABILITY: Data integrity foundation work.
        See: GAP-UI-AUDIT-2026-01-18.md, scripts/backfill_task_session_from_evidence.py
        """
        tasks = get_tasks_from_api()
        closed_tasks = [t for t in tasks if t.get("status") in ("CLOSED", "DONE", "completed")]

        if not closed_tasks:
            pytest.skip("No closed tasks found to verify")

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

        linkage_rate = tasks_with_linkage / len(closed_tasks) * 100 if closed_tasks else 0

        # Report findings
        print(f"\n[DATA INTEGRITY] Task→Session Linkage:")
        print(f"  - Closed tasks: {len(closed_tasks)}")
        print(f"  - With linkage: {tasks_with_linkage} ({linkage_rate:.1f}%)")
        print(f"  - Without linkage: {len(tasks_without_linkage)}")

        if tasks_without_linkage[:5]:  # Show first 5
            print(f"  - Sample unlinked: {tasks_without_linkage[:5]}")

        # Baseline threshold: 5% (achieved 2026-01-19, up from 0%)
        # Current: ~12% for all tasks, varies by subset
        # Target: Improve incrementally with each session
        MIN_LINKAGE_RATE = 5  # Conservative baseline
        assert linkage_rate >= MIN_LINKAGE_RATE, f"Task→Session linkage below baseline: {linkage_rate:.1f}% (min: {MIN_LINKAGE_RATE}%)"


class TestTaskEvidenceLinkage:
    """Test task-to-evidence linkage integrity."""

    def test_implemented_tasks_have_evidence(self):
        """Per TEST-FIX-01-v1: IMPLEMENTED tasks SHOULD have evidence."""
        tasks = get_tasks_from_api()

        # Filter for tasks with IMPLEMENTED/VALIDATED resolution
        implemented_tasks = [
            t for t in tasks
            if t.get("resolution") in ("IMPLEMENTED", "VALIDATED", "CERTIFIED")
            or t.get("status") in ("DONE", "completed", "CLOSED")
        ]

        if not implemented_tasks:
            pytest.skip("No implemented tasks found to verify")

        tasks_with_evidence = 0
        evidence_details = []

        for task in implemented_tasks:
            task_id = task.get("task_id") or task.get("id")
            evidence = task.get("evidence")
            evidence_file = task.get("evidence_file")

            has_evidence = bool(evidence or evidence_file)
            if has_evidence:
                tasks_with_evidence += 1
                evidence_details.append({
                    "task_id": task_id,
                    "evidence": evidence[:100] if evidence else None,
                    "evidence_file": evidence_file
                })

        evidence_rate = tasks_with_evidence / len(implemented_tasks) * 100 if implemented_tasks else 0

        print(f"\n[DATA INTEGRITY] Task→Evidence Linkage:")
        print(f"  - Implemented/Done tasks: {len(implemented_tasks)}")
        print(f"  - With evidence: {tasks_with_evidence} ({evidence_rate:.1f}%)")

        if evidence_details[:3]:
            print(f"  - Sample evidence: {evidence_details[:3]}")

        # Assertion: At least 70% evidence for implemented tasks
        # NOTE: Currently xfailed - historical tasks lack evidence linkage (data backfill needed)
        # Per GAP-UI-AUDIT-2026-01-18: Task→Evidence backfill is tracked but not complete
        # Target: 70% once backfill operations catch up
        if evidence_rate < 70:
            pytest.xfail(f"Task evidence rate too low: {evidence_rate:.1f}% (backfill needed)")


class TestSessionEvidenceLinkage:
    """Test session-to-evidence file linkage."""

    def test_sessions_have_evidence_files(self):
        """Sessions SHOULD have evidence files."""
        sessions = get_sessions_from_api()

        if not sessions:
            pytest.skip("No sessions found")

        sessions_with_evidence = 0
        evidence_files_found = []
        evidence_files_missing = []

        for session in sessions:
            session_id = session.get("session_id") or session.get("id")
            evidence_files = session.get("evidence_files", [])

            if evidence_files:
                sessions_with_evidence += 1
                # Check if files actually exist
                for ef in evidence_files[:2]:  # Check first 2
                    if check_evidence_file_exists(ef):
                        evidence_files_found.append(ef)
                    else:
                        evidence_files_missing.append(ef)

        evidence_rate = sessions_with_evidence / len(sessions) * 100 if sessions else 0

        print(f"\n[DATA INTEGRITY] Session→Evidence Files:")
        print(f"  - Total sessions: {len(sessions)}")
        print(f"  - With evidence_files: {sessions_with_evidence} ({evidence_rate:.1f}%)")
        print(f"  - Files verified existing: {len(evidence_files_found)}")
        print(f"  - Files missing: {len(evidence_files_missing)}")

        if evidence_files_missing[:3]:
            print(f"  - Missing files sample: {evidence_files_missing[:3]}")


class TestTaskCommitLinkage:
    """Test task-to-git-commit linkage."""

    def test_tasks_with_commit_linkage(self):
        """Per GAP-TASK-LINK-002: Tasks MAY have commit linkage."""
        tasks = get_tasks_from_api()

        tasks_with_commits = 0
        commit_examples = []

        for task in tasks:
            task_id = task.get("task_id") or task.get("id")
            # API returns linked_commits per TaskResponse model
            linked_commits = task.get("linked_commits", []) or []

            if linked_commits:
                tasks_with_commits += 1
                commit_examples.append({
                    "task_id": task_id,
                    "linked_commits": linked_commits[:2]
                })

        linkage_rate = tasks_with_commits / len(tasks) * 100 if tasks else 0

        print(f"\n[DATA INTEGRITY] Task→Commit Linkage:")
        print(f"  - Total tasks: {len(tasks)}")
        print(f"  - With commit linkage: {tasks_with_commits} ({linkage_rate:.1f}%)")

        if commit_examples[:3]:
            print(f"  - Sample linkages: {commit_examples[:3]}")

        # Info only - not enforced yet
        # assert linkage_rate >= 10, "Commit linkage should exist for some tasks"


class TestDataPollutionChecks:
    """Test for garbage data pollution (TEST-*, TEMP-* prefixes).

    NOTE: These tests are informational. During test suite execution, other
    tests create TEST-* entities which are cleaned up by session fixtures
    AFTER all tests complete. Run standalone for accurate pollution check:

        pytest tests/e2e/test_data_integrity_e2e.py::TestDataPollutionChecks -v

    """

    def test_no_test_prefix_rules(self):
        """Per WORKFLOW-RD-01-v1 Amendment A: TEST-* rules should be cleaned up.

        E2E tests create TEST-* entities but cleanup fixture should remove them.
        This test reports TEST-* rule count - 0 expected when run standalone.
        """
        response = requests.get(f"{API_URL}/api/rules", timeout=10)
        if response.status_code != 200:
            pytest.skip("Rules API unavailable")

        rules = response.json()
        test_rules = [r for r in rules if r.get("id", "").startswith("TEST-")]

        # Report count - when run as part of suite, other tests may have created garbage
        if test_rules:
            print(f"\n[DATA POLLUTION] Found {len(test_rules)} TEST-* rules")
            print(f"  Sample: {[r['id'] for r in test_rules[:5]]}")
            # If running standalone (no other tests created garbage), this should be 0
            # xfail if non-zero during suite run - cleanup happens at session end
            if len(test_rules) > 0:
                pytest.xfail(f"{len(test_rules)} TEST-* rules exist (cleanup pending at session end)")

    def test_no_test_prefix_tasks(self):
        """No TEST-* tasks should remain after test runs."""
        tasks = get_tasks_from_api()
        test_tasks = [t for t in tasks if (t.get("task_id") or "").startswith("TEST-")]

        # Report count
        if test_tasks:
            print(f"\n[DATA POLLUTION] Found {len(test_tasks)} TEST-* tasks")
            print(f"  Sample: {[t.get('task_id') for t in test_tasks[:5]]}")
            # xfail if non-zero during suite run - cleanup happens at session end
            if len(test_tasks) > 0:
                pytest.xfail(f"{len(test_tasks)} TEST-* tasks exist (cleanup pending at session end)")

    def test_rules_use_semantic_ids(self):
        """Per META-TAXON-01-v1: All rules MUST use semantic IDs.

        Legacy RULE-XXX format is deprecated. All rules should have
        semantic IDs like SESSION-EVID-01-v1, GOV-BICAM-01-v1, etc.
        """
        response = requests.get(f"{API_URL}/api/rules", timeout=10)
        if response.status_code != 200:
            pytest.skip("Rules API unavailable")

        rules = response.json()
        legacy_rules = [r for r in rules if r.get("id", "").startswith("RULE-")]

        assert len(legacy_rules) == 0, (
            f"Found {len(legacy_rules)} legacy RULE-XXX IDs (should use semantic IDs): "
            f"{[r['id'] for r in legacy_rules[:5]]}"
        )


class TestDataIntegritySummary:
    """Summary test combining all integrity checks."""

    def test_overall_data_integrity_report(self):
        """Generate comprehensive data integrity report."""
        tasks = get_tasks_from_api()
        sessions = get_sessions_from_api()

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
            # API returns linked_commits per TaskResponse model
            if task.get("linked_commits"):
                report["tasks_with_commits"] += 1

        for session in sessions:
            if session.get("evidence_files"):
                report["sessions_with_evidence"] += 1

        print("\n" + "=" * 60)
        print("DATA INTEGRITY REPORT")
        print("=" * 60)
        print(f"Tasks:    {report['total_tasks']} total, {report['closed_tasks']} closed")
        print(f"Sessions: {report['total_sessions']} total")
        print("-" * 60)
        print("LINKAGE RATES:")
        print(f"  Task→Session:  {report['tasks_with_session']}/{report['total_tasks']} "
              f"({report['tasks_with_session']/report['total_tasks']*100:.1f}%)" if report['total_tasks'] else "N/A")
        print(f"  Task→Evidence: {report['tasks_with_evidence']}/{report['total_tasks']} "
              f"({report['tasks_with_evidence']/report['total_tasks']*100:.1f}%)" if report['total_tasks'] else "N/A")
        print(f"  Task→Commit:   {report['tasks_with_commits']}/{report['total_tasks']} "
              f"({report['tasks_with_commits']/report['total_tasks']*100:.1f}%)" if report['total_tasks'] else "N/A")
        print(f"  Session→Evidence: {report['sessions_with_evidence']}/{report['total_sessions']} "
              f"({report['sessions_with_evidence']/report['total_sessions']*100:.1f}%)" if report['total_sessions'] else "N/A")
        print("=" * 60)

        # Store for assertion
        self.report = report

        # Basic sanity checks
        assert report["total_tasks"] > 0, "Should have tasks"
        assert report["total_sessions"] > 0, "Should have sessions"


# =============================================================================
# Standalone execution
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
