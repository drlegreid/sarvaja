"""
Task-related Compliance Checks.

Per DOC-SIZE-01-v1: Extracted from workflow_compliance.py.
Per TEST-FIX-01-v1, SESSION-EVID-01-v1, TASK-LIFE-01-v1: Task compliance rules.

Created: 2026-01-20
"""

import logging
from ..models import ComplianceCheck
from ..api_client import fetch_tasks

logger = logging.getLogger(__name__)


def check_task_evidence_compliance() -> ComplianceCheck:
    """
    Check TEST-FIX-01-v1: Completed tasks should have evidence.
    """
    try:
        tasks = fetch_tasks()

        if not tasks:
            return ComplianceCheck(
                rule_id="TEST-FIX-01-v1",
                check_name="task_evidence",
                status="SKIP",
                message="No tasks available (API unreachable or empty)",
                count=0
            )

        completed_tasks = [
            t for t in tasks
            if t.get("status") in ("DONE", "CLOSED", "completed")
        ]
        tasks_without_evidence = [
            t for t in completed_tasks
            if not t.get("evidence")
        ]

        total_completed = len(completed_tasks)
        without_evidence = len(tasks_without_evidence)
        with_evidence = total_completed - without_evidence

        if total_completed == 0:
            return ComplianceCheck(
                rule_id="TEST-FIX-01-v1",
                check_name="task_evidence",
                status="SKIP",
                message="No completed tasks to validate",
                count=0
            )

        pct = (with_evidence / total_completed) * 100

        if pct >= 90:
            return ComplianceCheck(
                rule_id="TEST-FIX-01-v1",
                check_name="task_evidence",
                status="PASS",
                message=f"{with_evidence}/{total_completed} ({pct:.0f}%) completed tasks have evidence",
                count=total_completed
            )
        elif pct >= 50:
            return ComplianceCheck(
                rule_id="TEST-FIX-01-v1",
                check_name="task_evidence",
                status="WARNING",
                message=f"{with_evidence}/{total_completed} ({pct:.0f}%) completed tasks have evidence",
                count=total_completed,
                violations=[t.get("id", t.get("task_id")) for t in tasks_without_evidence[:5]]
            )
        else:
            return ComplianceCheck(
                rule_id="TEST-FIX-01-v1",
                check_name="task_evidence",
                status="FAIL",
                message=f"Only {with_evidence}/{total_completed} ({pct:.0f}%) completed tasks have evidence",
                count=total_completed,
                violations=[t.get("id", t.get("task_id")) for t in tasks_without_evidence[:10]]
            )

    except Exception as e:
        logger.error(f"task_evidence check failed: {e}")
        return ComplianceCheck(
            rule_id="TEST-FIX-01-v1",
            check_name="task_evidence",
            status="SKIP",
            message=f"Check failed: {e}"
        )


def check_task_session_linkage() -> ComplianceCheck:
    """
    Check SESSION-EVID-01-v1: Completed tasks should be linked to sessions.
    """
    try:
        tasks = fetch_tasks()

        if not tasks:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="task_session_linkage",
                status="SKIP",
                message="No tasks available",
                count=0
            )

        completed_tasks = [
            t for t in tasks
            if t.get("status") in ("DONE", "CLOSED", "completed")
        ]
        tasks_without_session = [
            t for t in completed_tasks
            if not t.get("linked_sessions") or len(t.get("linked_sessions", [])) == 0
        ]

        total_completed = len(completed_tasks)
        without_session = len(tasks_without_session)
        with_session = total_completed - without_session

        if total_completed == 0:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="task_session_linkage",
                status="SKIP",
                message="No completed tasks to validate",
                count=0
            )

        pct = (with_session / total_completed) * 100

        if pct >= 10:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="task_session_linkage",
                status="PASS",
                message=f"{with_session}/{total_completed} ({pct:.0f}%) tasks linked to sessions",
                count=total_completed
            )
        elif pct > 0:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="task_session_linkage",
                status="WARNING",
                message=f"Only {with_session}/{total_completed} ({pct:.0f}%) tasks linked to sessions",
                count=total_completed,
                violations=[t.get("id", t.get("task_id")) for t in tasks_without_session[:5]]
            )
        else:
            return ComplianceCheck(
                rule_id="SESSION-EVID-01-v1",
                check_name="task_session_linkage",
                status="FAIL",
                message=f"No completed tasks linked to sessions (0/{total_completed})",
                count=total_completed,
                violations=[t.get("id", t.get("task_id")) for t in tasks_without_session[:10]]
            )

    except Exception as e:
        logger.error(f"task_session_linkage check failed: {e}")
        return ComplianceCheck(
            rule_id="SESSION-EVID-01-v1",
            check_name="task_session_linkage",
            status="SKIP",
            message=f"Check failed: {e}"
        )


def check_task_rule_linkage() -> ComplianceCheck:
    """
    Check TASK-LIFE-01-v1: Tasks should implement rules.
    """
    try:
        tasks = fetch_tasks()

        if not tasks:
            return ComplianceCheck(
                rule_id="TASK-LIFE-01-v1",
                check_name="task_rule_linkage",
                status="SKIP",
                message="No tasks available",
                count=0
            )

        tasks_with_rules = [
            t for t in tasks
            if t.get("linked_rules") and len(t.get("linked_rules", [])) > 0
        ]

        total_tasks = len(tasks)
        with_rules = len(tasks_with_rules)

        if total_tasks == 0:
            return ComplianceCheck(
                rule_id="TASK-LIFE-01-v1",
                check_name="task_rule_linkage",
                status="SKIP",
                message="No tasks to validate",
                count=0
            )

        pct = (with_rules / total_tasks) * 100

        if pct >= 20:
            return ComplianceCheck(
                rule_id="TASK-LIFE-01-v1",
                check_name="task_rule_linkage",
                status="PASS",
                message=f"{with_rules}/{total_tasks} ({pct:.0f}%) tasks linked to rules",
                count=total_tasks
            )
        elif pct > 0:
            return ComplianceCheck(
                rule_id="TASK-LIFE-01-v1",
                check_name="task_rule_linkage",
                status="WARNING",
                message=f"Only {with_rules}/{total_tasks} ({pct:.0f}%) tasks linked to rules",
                count=total_tasks
            )
        else:
            return ComplianceCheck(
                rule_id="TASK-LIFE-01-v1",
                check_name="task_rule_linkage",
                status="WARNING",
                message=f"No tasks linked to rules (0/{total_tasks})",
                count=total_tasks
            )

    except Exception as e:
        logger.error(f"task_rule_linkage check failed: {e}")
        return ComplianceCheck(
            rule_id="TASK-LIFE-01-v1",
            check_name="task_rule_linkage",
            status="SKIP",
            message=f"Check failed: {e}"
        )
