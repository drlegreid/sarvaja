"""Composite Traceability MCP Tools. Per A3: Full governance chain tracing.

Enables: test → GAP → evidence → session → task → rule backtracking.
Created: 2026-01-28 | Per SESSION-EVID-01-v1, GOV-TRANSP-01-v1.
"""

from typing import Optional
from governance.mcp_tools.common import get_typedb_client, format_mcp_result

try:
    from agent.governance_ui.data_access.monitoring import log_monitor_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


def _trace_task(client, task_id: str) -> dict:
    """Build trace node for a single task with all linked entities."""
    task = client.get_task(task_id)
    if not task:
        return {"task_id": task_id, "error": "not found"}

    evidence_files = client.get_task_evidence(task_id)
    commits = client.get_task_commits(task_id)

    return {
        "task_id": task_id,
        "description": getattr(task, "description", None),
        "status": getattr(task, "status", None),
        "phase": getattr(task, "phase", None),
        "gap_id": getattr(task, "gap_id", None),
        "linked_rules": getattr(task, "linked_rules", []) or [],
        "linked_sessions": getattr(task, "linked_sessions", []) or [],
        "evidence_files": evidence_files or [],
        "commits": commits or [],
    }


def _trace_session(client, session_id: str) -> dict:
    """Build trace node for a single session with all linked entities."""
    session = client.get_session(session_id)
    if not session:
        return {"session_id": session_id, "error": "not found"}

    evidence = client.get_session_evidence(session_id)
    rules = client.get_session_rules(session_id)
    decisions = client.get_session_decisions(session_id)
    tasks_data = client.get_tasks_for_session(session_id)

    task_ids = []
    if tasks_data:
        for t in tasks_data:
            tid = t.get("task_id") if isinstance(t, dict) else getattr(t, "task_id", None)
            if tid:
                task_ids.append(tid)

    return {
        "session_id": session_id,
        "status": getattr(session, "status", None),
        "evidence_files": evidence or [],
        "rules_applied": rules or [],
        "decisions": decisions or [],
        "task_ids": task_ids,
    }


def _trace_rule(client, rule_id: str) -> dict:
    """Build trace node for a single rule."""
    rule = client.get_rule_by_id(rule_id)
    if not rule:
        return {"rule_id": rule_id, "error": "not found"}

    deps = client.get_rule_dependencies(rule_id)
    dependents = client.get_rules_depending_on(rule_id)

    return {
        "rule_id": rule_id,
        "name": getattr(rule, "name", None),
        "category": getattr(rule, "category", None),
        "priority": getattr(rule, "priority", None),
        "status": getattr(rule, "status", None),
        "dependencies": deps or [],
        "depended_by": dependents or [],
    }


def register_traceability_tools(mcp) -> None:
    """Register composite traceability MCP tools."""

    @mcp.tool()
    def trace_task_chain(task_id: str, depth: int = 1) -> str:
        """Trace full governance chain from a task: task → sessions → evidence → rules → commits.

        Args:
            task_id: Task ID to trace (e.g. 'P12.1', 'GAP-UI-001')
            depth: Expansion depth for linked entities (0=task only, 1=expand links, 2=full)

        Returns:
            Complete trace chain with all linked governance entities.
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            result = _trace_task(client, task_id)
            if "error" in result:
                return format_mcp_result(result)

            if depth >= 1:
                # Expand sessions
                sessions = []
                for sid in result["linked_sessions"]:
                    sessions.append(_trace_session(client, sid))
                result["sessions_detail"] = sessions

                # Expand rules
                rules = []
                for rid in result["linked_rules"]:
                    rules.append(_trace_rule(client, rid))
                result["rules_detail"] = rules

            if depth >= 2:
                # Expand session→rules for cross-referencing
                for s in result.get("sessions_detail", []):
                    s_rules = []
                    for rid in s.get("rules_applied", []):
                        if not any(r.get("rule_id") == rid for r in result.get("rules_detail", [])):
                            s_rules.append(_trace_rule(client, rid))
                    s["rules_detail"] = s_rules

            if MONITORING_AVAILABLE:
                log_monitor_event(
                    event_type="trace_event", source="mcp-trace-task-chain",
                    details={"task_id": task_id, "depth": depth})

            return format_mcp_result(result)
        finally:
            client.close()

    @mcp.tool()
    def trace_session_chain(session_id: str, depth: int = 1) -> str:
        """Trace full governance chain from a session: session → tasks → evidence → rules.

        Args:
            session_id: Session ID to trace (e.g. 'SESSION-2026-01-28-TOPIC')
            depth: Expansion depth (0=session only, 1=expand tasks+rules)

        Returns:
            Complete trace chain with all linked governance entities.
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            result = _trace_session(client, session_id)
            if "error" in result:
                return format_mcp_result(result)

            if depth >= 1:
                tasks = []
                for tid in result["task_ids"]:
                    tasks.append(_trace_task(client, tid))
                result["tasks_detail"] = tasks

                rules = []
                for rid in result["rules_applied"]:
                    rules.append(_trace_rule(client, rid))
                result["rules_detail"] = rules

            if MONITORING_AVAILABLE:
                log_monitor_event(
                    event_type="trace_event", source="mcp-trace-session-chain",
                    details={"session_id": session_id, "depth": depth})

            return format_mcp_result(result)
        finally:
            client.close()

    @mcp.tool()
    def trace_rule_chain(rule_id: str, depth: int = 1) -> str:
        """Trace governance chain from a rule: rule → tasks implementing → sessions → evidence.

        Args:
            rule_id: Rule ID or semantic ID (e.g. 'RULE-001' or 'SESSION-EVID-01-v1')
            depth: Expansion depth (0=rule only, 1=expand tasks)

        Returns:
            Complete trace chain showing what implements this rule.
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            result = _trace_rule(client, rule_id)
            if "error" in result:
                return format_mcp_result(result)

            if depth >= 1:
                # Find tasks implementing this rule via TypeQL
                query = (
                    f'match $t isa task, has task-id $tid; '
                    f'$r isa governance-rule, has rule-id "{rule_id}"; '
                    f'(implementing-task: $t, implemented-rule: $r) isa implements-rule; '
                    f'get $tid;'
                )
                try:
                    rows = client.execute_query(query)
                    task_ids = [r.get("tid", r.get("task-id", "")) for r in rows if r]
                except Exception:
                    task_ids = []

                tasks = []
                for tid in task_ids:
                    if tid:
                        tasks.append(_trace_task(client, tid))
                result["implementing_tasks"] = tasks
                result["implementing_count"] = len(tasks)

            if MONITORING_AVAILABLE:
                log_monitor_event(
                    event_type="trace_event", source="mcp-trace-rule-chain",
                    details={"rule_id": rule_id, "depth": depth})

            return format_mcp_result(result)
        finally:
            client.close()

    @mcp.tool()
    def trace_gap_chain(gap_id: str) -> str:
        """Trace governance chain from a GAP: gap → task → sessions → evidence → rules.

        Args:
            gap_id: Gap ID (e.g. 'GAP-UI-001', 'GAP-MCP-PAGING-001')

        Returns:
            Complete trace chain showing gap resolution path.
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # Find tasks with this gap_id
            query = (
                f'match $t isa task, has task-id $tid, has gap-id "{gap_id}"; '
                f'get $tid;'
            )
            try:
                rows = client.execute_query(query)
                task_ids = [r.get("tid", r.get("task-id", "")) for r in rows if r]
            except Exception:
                task_ids = []

            if not task_ids:
                return format_mcp_result({
                    "gap_id": gap_id,
                    "error": "No tasks found for this gap",
                    "tasks": []
                })

            tasks = []
            all_sessions = set()
            all_rules = set()
            all_evidence = set()

            for tid in task_ids:
                if not tid:
                    continue
                task_trace = _trace_task(client, tid)
                tasks.append(task_trace)
                all_sessions.update(task_trace.get("linked_sessions", []))
                all_rules.update(task_trace.get("linked_rules", []))
                all_evidence.update(task_trace.get("evidence_files", []))

            result = {
                "gap_id": gap_id,
                "tasks": tasks,
                "task_count": len(tasks),
                "unique_sessions": sorted(all_sessions),
                "unique_rules": sorted(all_rules),
                "unique_evidence": sorted(all_evidence),
                "session_count": len(all_sessions),
                "rule_count": len(all_rules),
                "evidence_count": len(all_evidence),
            }

            if MONITORING_AVAILABLE:
                log_monitor_event(
                    event_type="trace_event", source="mcp-trace-gap-chain",
                    details={"gap_id": gap_id, "task_count": len(tasks)})

            return format_mcp_result(result)
        finally:
            client.close()

    @mcp.tool()
    def trace_evidence_chain(evidence_path: str) -> str:
        """Trace governance chain from evidence: evidence → tasks → sessions → rules.

        Args:
            evidence_path: Evidence file path (e.g. 'evidence/SESSION-2026-01-28.md')

        Returns:
            Which tasks, sessions, and rules this evidence supports.
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # Find tasks linked to this evidence
            query = (
                f'match $t isa task, has task-id $tid; '
                f'$e isa evidence, has evidence-source "{evidence_path}"; '
                f'(supporting-evidence: $e, supported-task: $t) isa evidence-supports; '
                f'get $tid;'
            )
            try:
                rows = client.execute_query(query)
                task_ids = [r.get("tid", r.get("task-id", "")) for r in rows if r]
            except Exception:
                task_ids = []

            # Find sessions linked to this evidence
            query_sessions = (
                f'match $s isa work-session, has session-id $sid; '
                f'$e isa evidence, has evidence-source "{evidence_path}"; '
                f'(session-with-evidence: $s, session-evidence: $e) isa has-evidence; '
                f'get $sid;'
            )
            try:
                rows_s = client.execute_query(query_sessions)
                session_ids = [r.get("sid", r.get("session-id", "")) for r in rows_s if r]
            except Exception:
                session_ids = []

            tasks = []
            all_rules = set()
            for tid in task_ids:
                if not tid:
                    continue
                task_trace = _trace_task(client, tid)
                tasks.append(task_trace)
                all_rules.update(task_trace.get("linked_rules", []))

            result = {
                "evidence_path": evidence_path,
                "linked_tasks": tasks,
                "linked_sessions": session_ids,
                "linked_rules": sorted(all_rules),
                "task_count": len(tasks),
                "session_count": len(session_ids),
                "rule_count": len(all_rules),
            }

            if MONITORING_AVAILABLE:
                log_monitor_event(
                    event_type="trace_event", source="mcp-trace-evidence-chain",
                    details={"evidence_path": evidence_path})

            return format_mcp_result(result)
        finally:
            client.close()
