"""
Session Linking MCP Tools
=========================
Entity linking operations for sessions.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per P11.3: Entity Linkage infrastructure
Per GAP-DATA-002: Entity linkage implementation

Extracted from sessions.py per modularization plan.
Created: 2026-01-03
"""

import json

# Check TypeDB availability
try:
    from governance.client import TypeDBClient
    TYPEDB_AVAILABLE = True
except ImportError:
    TYPEDB_AVAILABLE = False


def register_session_linking_tools(mcp) -> None:
    """Register session linking MCP tools."""

    @mcp.tool()
    def session_get_tasks(session_id: str) -> str:
        """
        Get all tasks linked to a specific session.

        Per GAP-DATA-002: Query tasks by session via completed-in relation.
        Enables referencing session data with tasks as requested.

        Args:
            session_id: Session ID (e.g., "SESSION-2026-01-02-PHASE11")

        Returns:
            JSON array of tasks linked to the session
        """
        if not TYPEDB_AVAILABLE:
            return json.dumps({"error": "TypeDB not available"})

        try:
            client = TypeDBClient()
            if not client.connect():
                return json.dumps({"error": "Could not connect to TypeDB"})

            # Query tasks linked to session via completed-in relation
            # TypeDB 3.x: 'select' replaces 'get'
            query = f'''
                match
                    $s isa work-session, has session-id "{session_id}";
                    (completed-task: $t, hosting-session: $s) isa completed-in;
                    $t has task-id $tid, has task-name $name, has task-status $status;
                select $tid, $name, $status;
            '''
            results = client.execute_query(query)
            client.close()

            tasks = []
            for r in results:
                tasks.append({
                    "task_id": r.get("tid"),
                    "name": r.get("name"),
                    "status": r.get("status")
                })

            return json.dumps({
                "session_id": session_id,
                "tasks": tasks,
                "count": len(tasks)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def session_link_rule(session_id: str, rule_id: str) -> str:
        """
        Link a rule to a session (session-applied-rule relation).

        Per P11.3: Entity Linkage - tracks which rules were applied during a session.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            session_id: Session ID (e.g., "SESSION-2026-01-02-PHASE11")
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            JSON object with link status
        """
        if not TYPEDB_AVAILABLE:
            return json.dumps({"error": "TypeDB not available"})

        try:
            client = TypeDBClient()
            if not client.connect():
                return json.dumps({"error": "Could not connect to TypeDB"})

            success = client.link_rule_to_session(session_id, rule_id)
            client.close()

            if success:
                return json.dumps({
                    "session_id": session_id,
                    "rule_id": rule_id,
                    "relation": "session-applied-rule",
                    "message": f"Successfully linked rule {rule_id} to session {session_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link rule {rule_id} to session {session_id}"
                })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def session_link_decision(session_id: str, decision_id: str) -> str:
        """
        Link a decision to a session (session-decision relation).

        Per P11.3: Entity Linkage - tracks which decisions were made during a session.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            session_id: Session ID (e.g., "SESSION-2026-01-02-PHASE11")
            decision_id: Decision ID (e.g., "DECISION-001")

        Returns:
            JSON object with link status
        """
        if not TYPEDB_AVAILABLE:
            return json.dumps({"error": "TypeDB not available"})

        try:
            client = TypeDBClient()
            if not client.connect():
                return json.dumps({"error": "Could not connect to TypeDB"})

            success = client.link_decision_to_session(session_id, decision_id)
            client.close()

            if success:
                return json.dumps({
                    "session_id": session_id,
                    "decision_id": decision_id,
                    "relation": "session-decision",
                    "message": f"Successfully linked decision {decision_id} to session {session_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link decision {decision_id} to session {session_id}"
                })

        except Exception as e:
            return json.dumps({"error": str(e)})

    @mcp.tool()
    def session_link_evidence(session_id: str, evidence_path: str) -> str:
        """
        Link an evidence file to a session (has-evidence relation).

        Per P11.3: Entity Linkage - tracks evidence files for a session.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            session_id: Session ID (e.g., "SESSION-2026-01-02-PHASE11")
            evidence_path: Path to evidence file (e.g., "evidence/REPORT.md")

        Returns:
            JSON object with link status
        """
        if not TYPEDB_AVAILABLE:
            return json.dumps({"error": "TypeDB not available"})

        try:
            client = TypeDBClient()
            if not client.connect():
                return json.dumps({"error": "Could not connect to TypeDB"})

            success = client.link_evidence_to_session(session_id, evidence_path)
            client.close()

            if success:
                return json.dumps({
                    "session_id": session_id,
                    "evidence_path": evidence_path,
                    "relation": "has-evidence",
                    "message": f"Successfully linked evidence {evidence_path} to session {session_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link evidence {evidence_path} to session {session_id}"
                })

        except Exception as e:
            return json.dumps({"error": str(e)})
