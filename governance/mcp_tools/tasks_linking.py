"""
Task Linking MCP Tools
======================
Entity linking operations for tasks.

Per RULE-012: DSP Semantic Code Structure
Per RULE-032: File size <300 lines
Per P11.3: Entity Linkage infrastructure
Per GAP-DATA-002: Entity linkage implementation

Extracted from tasks.py per modularization plan.
Created: 2026-01-03
"""

import json

from governance.mcp_tools.common import get_typedb_client


def register_task_linking_tools(mcp) -> None:
    """Register task linking MCP tools."""

    @mcp.tool()
    def governance_task_link_session(task_id: str, session_id: str) -> str:
        """
        Link a task to a session (completed-in relation).

        Per P11.3: Entity Linkage - tracks which session a task was completed in.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            session_id: Session ID (e.g., "SESSION-2026-01-02-PHASE11")

        Returns:
            JSON object with link status
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_session(task_id, session_id)

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "session_id": session_id,
                    "relation": "completed-in",
                    "message": f"Successfully linked task {task_id} to session {session_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link task {task_id} to session {session_id}"
                })
        finally:
            client.close()

    @mcp.tool()
    def governance_task_link_rule(task_id: str, rule_id: str) -> str:
        """
        Link a task to a rule (implements-rule relation).

        Per P11.3: Entity Linkage - tracks which rules a task implements.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            JSON object with link status
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_rule(task_id, rule_id)

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "rule_id": rule_id,
                    "relation": "implements-rule",
                    "message": f"Successfully linked task {task_id} to rule {rule_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link task {task_id} to rule {rule_id}"
                })
        finally:
            client.close()

    @mcp.tool()
    def governance_task_link_evidence(task_id: str, evidence_path: str) -> str:
        """
        Link evidence to a task (evidence-supports relation).

        Per P11.3: Entity Linkage - tracks evidence supporting task completion.
        Per GAP-DATA-002: Entity linkage implementation.

        Args:
            task_id: Task ID (e.g., "P10.1")
            evidence_path: Path to evidence file (e.g., "evidence/REPORT.md")

        Returns:
            JSON object with link status
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.link_evidence_to_task(task_id, evidence_path)

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "evidence_path": evidence_path,
                    "relation": "evidence-supports",
                    "message": f"Successfully linked evidence {evidence_path} to task {task_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link evidence {evidence_path} to task {task_id}"
                })
        finally:
            client.close()

    @mcp.tool()
    def governance_task_get_evidence(task_id: str) -> str:
        """
        Get all evidence files linked to a task.

        Per P11.3: Entity Linkage - query evidence supporting task.

        Args:
            task_id: Task ID (e.g., "P10.1")

        Returns:
            JSON object with list of evidence files
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            evidence_files = client.get_task_evidence(task_id)

            return json.dumps({
                "task_id": task_id,
                "evidence_files": evidence_files,
                "count": len(evidence_files)
            }, indent=2)
        finally:
            client.close()

    @mcp.tool()
    def governance_task_link_commit(task_id: str, commit_sha: str, commit_message: str = None) -> str:
        """
        Link a task to a git commit (task-commit relation).

        Per GAP-TASK-LINK-002: Task-to-commit traceability.
        Enables code-to-task audit trail.

        Args:
            task_id: Task ID (e.g., "P10.1", "GAP-TASK-LINK-002")
            commit_sha: Git commit SHA (short 7-char or full 40-char)
            commit_message: Optional commit message for reference

        Returns:
            JSON object with link status
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_commit(task_id, commit_sha, commit_message)

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "commit_sha": commit_sha,
                    "relation": "task-commit",
                    "message": f"Successfully linked task {task_id} to commit {commit_sha}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to link task {task_id} to commit {commit_sha}"
                })
        finally:
            client.close()

    @mcp.tool()
    def governance_task_get_commits(task_id: str) -> str:
        """
        Get all git commits linked to a task.

        Per GAP-TASK-LINK-002: Task-to-commit traceability.

        Args:
            task_id: Task ID (e.g., "P10.1")

        Returns:
            JSON object with list of commit SHAs
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            commits = client.get_task_commits(task_id)

            return json.dumps({
                "task_id": task_id,
                "commits": commits,
                "count": len(commits)
            }, indent=2)
        finally:
            client.close()

    @mcp.tool()
    def governance_task_update_details(
        task_id: str,
        business: str = None,
        design: str = None,
        architecture: str = None,
        test_section: str = None
    ) -> str:
        """
        Update task detail sections (business, design, architecture, test).

        Per GAP-TASK-LINK-004: Task detail sections.
        Per TASK-TECH-01-v1: Technology Solution Documentation.

        Args:
            task_id: Task ID (e.g., "P10.1", "GAP-TASK-LINK-004")
            business: Business section - Why (User problem, business value)
            design: Design section - What (Functional requirements)
            architecture: Architecture section - How (Technical approach)
            test_section: Test section - Verification (Test plan, evidence)

        Returns:
            JSON object with update status
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            success = client.update_task_details(
                task_id=task_id,
                business=business,
                design=design,
                architecture=architecture,
                test_section=test_section
            )

            if success:
                return json.dumps({
                    "task_id": task_id,
                    "updated_sections": [
                        s for s in ["business", "design", "architecture", "test_section"]
                        if locals().get(s) is not None
                    ],
                    "message": f"Successfully updated details for task {task_id}"
                }, indent=2)
            else:
                return json.dumps({
                    "error": f"Failed to update details for task {task_id}"
                })
        finally:
            client.close()

    @mcp.tool()
    def governance_task_get_details(task_id: str) -> str:
        """
        Get all detail sections for a task.

        Per GAP-TASK-LINK-004: Task detail sections.

        Args:
            task_id: Task ID (e.g., "P10.1")

        Returns:
            JSON object with business, design, architecture, test_section
        """
        client = get_typedb_client()
        try:
            if not client.connect():
                return json.dumps({"error": "Failed to connect to TypeDB"})

            details = client.get_task_details(task_id)

            if details is None:
                return json.dumps({
                    "error": f"Task {task_id} not found"
                })

            return json.dumps({
                "task_id": task_id,
                **details
            }, indent=2)
        finally:
            client.close()
