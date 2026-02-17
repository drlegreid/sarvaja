"""Task Linking MCP Tools. Per RULE-012, P11.3, GAP-DATA-002. Created: 2026-01-03."""


from governance.mcp_tools.common import get_typedb_client, format_mcp_result

# Monitoring instrumentation per GAP-MONITOR-INSTRUMENT-001
try:
    from agent.governance_ui.data_access.monitoring import log_monitor_event
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


def register_task_linking_tools(mcp) -> None:
    """Register task linking MCP tools."""

    @mcp.tool()
    def task_link_session(task_id: str, session_id: str) -> str:
        """Link task to session (completed-in relation). Per P11.3, GAP-DATA-002."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_session(task_id, session_id)

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="link_event", source="mcp-task-link-session",
                        details={"task_id": task_id, "session_id": session_id, "action": "link"})
                return format_mcp_result({
                    "task_id": task_id,
                    "session_id": session_id,
                    "relation": "completed-in",
                    "message": f"Successfully linked task {task_id} to session {session_id}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to link task {task_id} to session {session_id}"
                })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_link_session failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_link_rule(task_id: str, rule_id: str) -> str:
        """Link task to rule (implements-rule relation). Per P11.3, GAP-DATA-002."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_rule(task_id, rule_id)

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="link_event", source="mcp-task-link-rule",
                        details={"task_id": task_id, "rule_id": rule_id, "action": "link"})
                return format_mcp_result({
                    "task_id": task_id,
                    "rule_id": rule_id,
                    "relation": "implements-rule",
                    "message": f"Successfully linked task {task_id} to rule {rule_id}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to link task {task_id} to rule {rule_id}"
                })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_link_rule failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_link_evidence(task_id: str, evidence_path: str) -> str:
        """Link evidence to task (evidence-supports relation). Per P11.3, GAP-DATA-002."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.link_evidence_to_task(task_id, evidence_path)

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="link_event", source="mcp-task-link-evidence",
                        details={"task_id": task_id, "evidence_path": evidence_path, "action": "link"})
                return format_mcp_result({
                    "task_id": task_id,
                    "evidence_path": evidence_path,
                    "relation": "evidence-supports",
                    "message": f"Successfully linked evidence {evidence_path} to task {task_id}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to link evidence {evidence_path} to task {task_id}"
                })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_link_evidence failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_get_evidence(task_id: str) -> str:
        """Get all evidence files linked to a task. Per P11.3."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # BUG-271-TASKSLINK-001: Guard against None return from get_task_evidence
            evidence_files = client.get_task_evidence(task_id) or []

            if MONITORING_AVAILABLE:
                log_monitor_event(event_type="link_event", source="mcp-task-get-evidence",
                    details={"task_id": task_id, "action": "query_evidence", "count": len(evidence_files)})
            return format_mcp_result({
                "task_id": task_id,
                "evidence_files": evidence_files,
                "count": len(evidence_files)
            })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_get_evidence failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_link_commit(task_id: str, commit_sha: str, commit_message: str = None) -> str:
        """Link task to git commit (task-commit relation). Per GAP-TASK-LINK-002."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_commit(task_id, commit_sha, commit_message)

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="link_event", source="mcp-task-link-commit",
                        details={"task_id": task_id, "commit_sha": commit_sha, "action": "link"})
                return format_mcp_result({
                    "task_id": task_id,
                    "commit_sha": commit_sha,
                    "relation": "task-commit",
                    "message": f"Successfully linked task {task_id} to commit {commit_sha}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to link task {task_id} to commit {commit_sha}"
                })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_link_commit failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_get_commits(task_id: str) -> str:
        """Get all git commits linked to a task. Per GAP-TASK-LINK-002."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # BUG-271-TASKSLINK-001: Guard against None return from get_task_commits
            commits = client.get_task_commits(task_id) or []

            if MONITORING_AVAILABLE:
                log_monitor_event(event_type="link_event", source="mcp-task-get-commits",
                    details={"task_id": task_id, "action": "query_commits", "count": len(commits)})
            return format_mcp_result({
                "task_id": task_id,
                "commits": commits,
                "count": len(commits)
            })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_get_commits failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_link_document(task_id: str, document_path: str) -> str:
        """Link a document to a task (document-references-task relation). Task document management."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.link_task_to_document(task_id, document_path)

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="link_event", source="mcp-task-link-document",
                        details={"task_id": task_id, "document_path": document_path, "action": "link"})
                return format_mcp_result({
                    "task_id": task_id,
                    "document_path": document_path,
                    "relation": "document-references-task",
                    "message": f"Successfully linked document {document_path} to task {task_id}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to link document {document_path} to task {task_id}"
                })
        except Exception as e:
            return format_mcp_result({"error": str(e)})
        finally:
            client.close()

    @mcp.tool()
    def task_get_documents(task_id: str) -> str:
        """Get all documents linked to a task. Task document management."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            # BUG-271-TASKSLINK-001: Guard against None return from get_task_documents
            documents = client.get_task_documents(task_id) or []

            if MONITORING_AVAILABLE:
                log_monitor_event(event_type="link_event", source="mcp-task-get-documents",
                    details={"task_id": task_id, "action": "query_documents", "count": len(documents)})
            return format_mcp_result({
                "task_id": task_id,
                "documents": documents,
                "count": len(documents)
            })
        except Exception as e:
            return format_mcp_result({"error": str(e)})
        finally:
            client.close()

    @mcp.tool()
    def task_update_details(task_id: str, business: str = None, design: str = None,
                            architecture: str = None, test_section: str = None) -> str:
        """Update task detail sections. Per GAP-TASK-LINK-004, TASK-TECH-01-v1."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            success = client.update_task_details(
                task_id=task_id,
                business=business,
                design=design,
                architecture=architecture,
                test_section=test_section
            )

            if success:
                if MONITORING_AVAILABLE:
                    log_monitor_event(event_type="task_event", source="mcp-task-update-details",
                        details={"task_id": task_id, "action": "update_details"})
                # BUG-344-LNK-001: locals() inside a list comprehension sees the
                # comprehension's own scope in Python 3, NOT the enclosing function's
                # variables — so locals().get(s) always returns None. Build explicitly.
                updated_sections = [
                    s for s, v in [
                        ("business", business), ("design", design),
                        ("architecture", architecture), ("test_section", test_section)
                    ] if v is not None
                ]
                return format_mcp_result({
                    "task_id": task_id,
                    "updated_sections": updated_sections,
                    "message": f"Successfully updated details for task {task_id}"
                })
            else:
                return format_mcp_result({
                    "error": f"Failed to update details for task {task_id}"
                })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_update_details failed: {e}"})
        finally:
            client.close()

    @mcp.tool()
    def task_get_details(task_id: str) -> str:
        """Get all detail sections for a task. Per GAP-TASK-LINK-004."""
        client = get_typedb_client()
        try:
            if not client.connect():
                return format_mcp_result({"error": "Failed to connect to TypeDB"})

            details = client.get_task_details(task_id)

            if details is None:
                return format_mcp_result({
                    "error": f"Task {task_id} not found"
                })

            if MONITORING_AVAILABLE:
                log_monitor_event(event_type="task_event", source="mcp-task-get-details",
                    details={"task_id": task_id, "action": "query_details"})
            return format_mcp_result({
                "task_id": task_id,
                **details
            })
        # BUG-B185-007: Add except to match task_link_document pattern
        except Exception as e:
            return format_mcp_result({"error": f"task_get_details failed: {e}"})
        finally:
            client.close()
