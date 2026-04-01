"""Task Linking Operations — link/unlink tasks to rules, sessions, documents, workspaces.

Per DOC-SIZE-01-v1: Extracted from tasks_mutations.py.
Per SRVJ-BUG-ERROR-OBS-01: Returns LinkResult instead of bare bool.
"""
import logging

from governance.stores import get_typedb_client, _tasks_store
from governance.stores.audit import record_audit
from .tasks_preload import _monitor
from .link_result import LinkResult
from .task_activity_comments import maybe_add_activity_comment

logger = logging.getLogger(__name__)


def _record_link_audit(
    task_id: str, action: str, entity_type: str, entity_id: str,
    source: str = "rest", session_id: str = None,
):
    """Record audit entry for link/unlink operations.

    Per SRVJ-FEAT-AUDIT-TRAIL-01 P2: DRY helper — all linking ops share
    the same audit recording pattern.
    """
    action_type = "LINK" if action == "link" else "UNLINK"
    metadata = {
        "source": source,
        "linked_entity": {"type": entity_type, "id": entity_id, "action": action},
    }
    if session_id:
        metadata["session_id"] = session_id
    record_audit(action_type, "task", task_id, actor_id="system", metadata=metadata)


def link_task_to_rule(task_id: str, rule_id: str, source: str = "rest") -> LinkResult:
    """Link task to rule via implements-rule relation."""
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        result = client.link_task_to_rule(task_id, rule_id)
        if result:
            _monitor("link_rule", task_id, source=source, rule_id=rule_id)
            _record_link_audit(task_id, "link", "rule", rule_id, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "rule", "id": rule_id, "action": "link"}},
            )
            return LinkResult(success=True, already_existed=False, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link task {task_id} to rule {rule_id}",
                          error_code="LINK_FAILED")
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-007: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to rule {rule_id}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def link_task_to_session(task_id: str, session_id: str, source: str = "rest") -> LinkResult:
    """Link task to session via completed-in relation."""
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        # Pre-check store for idempotency detection
        _pre_existed = (task_id in _tasks_store
                        and session_id in _tasks_store[task_id].get("linked_sessions", []))
        result = client.link_task_to_session(task_id, session_id)
        if result:
            # SRVJ-BUG-002: Keep _tasks_store in sync for DONE gate validation
            if task_id in _tasks_store:
                sessions = _tasks_store[task_id].get("linked_sessions", [])
                if session_id not in sessions:
                    sessions.append(session_id)
                    _tasks_store[task_id]["linked_sessions"] = sessions
            _monitor("link_session", task_id, source=source, session_id=session_id)
            _record_link_audit(task_id, "link", "session", session_id, source=source, session_id=session_id)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "session", "id": session_id, "action": "link"}, "session_id": session_id},
            )
            return LinkResult(success=True, already_existed=_pre_existed, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link task {task_id} to session {session_id}",
                          error_code="LINK_FAILED")
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-008: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to session {session_id}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def link_task_to_document(task_id: str, document_path: str, source: str = "rest") -> LinkResult:
    """Link task to document via document-references-task relation."""
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        # Pre-check store for idempotency detection
        _pre_existed = (task_id in _tasks_store
                        and document_path in _tasks_store[task_id].get("linked_documents", []))
        result = client.link_task_to_document(task_id, document_path)
        if result:
            # SRVJ-BUG-002: Keep _tasks_store in sync for DONE gate validation
            if task_id in _tasks_store:
                docs = _tasks_store[task_id].get("linked_documents", [])
                if document_path not in docs:
                    docs.append(document_path)
                    _tasks_store[task_id]["linked_documents"] = docs
            _monitor("link_document", task_id, source=source, document_path=document_path)
            _record_link_audit(task_id, "link", "document", document_path, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "document", "id": document_path, "action": "link"}},
            )
            return LinkResult(success=True, already_existed=_pre_existed, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link task {task_id} to document {document_path}",
                          error_code="LINK_FAILED")
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-009: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to document {document_path}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def unlink_task_from_document(task_id: str, document_path: str, source: str = "rest") -> LinkResult:
    """Unlink document from task."""
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        result = client.unlink_task_from_document(task_id, document_path)
        if result:
            _monitor("unlink_document", task_id, source=source, document_path=document_path)
            _record_link_audit(task_id, "unlink", "document", document_path, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="UNLINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "document", "id": document_path, "action": "unlink"}},
            )
            return LinkResult(success=True, already_existed=False, reason="unlinked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to unlink document {document_path} from task {task_id}",
                          error_code="LINK_FAILED")
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-010: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to unlink document {document_path} from task {task_id}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def link_task_to_evidence(task_id: str, evidence_path: str, source: str = "rest") -> LinkResult:
    """Link evidence to task via evidence-supports relation.

    Per SRVJ-BUG-LINK-IDEM-01: Service layer for existence check + audit.
    """
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        result = client.link_evidence_to_task(task_id, evidence_path)
        if result:
            _monitor("link_evidence", task_id, source=source, evidence_path=evidence_path)
            _record_link_audit(task_id, "link", "evidence", evidence_path, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "evidence", "id": evidence_path, "action": "link"}},
            )
            return LinkResult(success=True, already_existed=False, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link evidence {evidence_path} to task {task_id}",
                          error_code="LINK_FAILED")
    except Exception as e:
        logger.error(f"Failed to link evidence {evidence_path} to task {task_id}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def link_task_to_commit(task_id: str, commit_sha: str, commit_message: str = None, source: str = "rest") -> LinkResult:
    """Link task to git commit via task-commit relation.

    Per SRVJ-BUG-LINK-IDEM-01: Service layer for existence check + audit.
    """
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        # Pre-check store for idempotency detection
        _pre_existed = (task_id in _tasks_store
                        and commit_sha in _tasks_store[task_id].get("linked_commits", []))
        result = client.link_task_to_commit(task_id, commit_sha, commit_message)
        if result:
            if task_id in _tasks_store:
                commits = _tasks_store[task_id].get("linked_commits", [])
                if commit_sha not in commits:
                    commits.append(commit_sha)
                    _tasks_store[task_id]["linked_commits"] = commits
            _monitor("link_commit", task_id, source=source, commit_sha=commit_sha)
            _record_link_audit(task_id, "link", "commit", commit_sha, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "commit", "id": commit_sha, "action": "link"}},
            )
            return LinkResult(success=True, already_existed=_pre_existed, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link task {task_id} to commit {commit_sha}",
                          error_code="LINK_FAILED")
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to commit {commit_sha}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")


def link_task_to_workspace(task_id: str, workspace_id: str, source: str = "rest") -> LinkResult:
    """Link task to workspace via workspace-has-task relation.

    Per EPIC-GOV-TASKS-V2 Phase 4: Task-Workspace Bidirectional Linking.
    """
    client = get_typedb_client()
    if not client:
        return LinkResult(success=False, already_existed=False,
                          reason="TypeDB client unavailable", error_code="NO_CLIENT")
    try:
        if not client.get_task(task_id):
            return LinkResult(success=False, already_existed=False,
                              reason=f"task {task_id} not found", error_code="ENTITY_NOT_FOUND")
        result = client.link_task_to_workspace(workspace_id, task_id)  # BUG-WS-CREATE-001: fix arg order
        if result:
            _monitor("link_workspace", task_id, source=source, workspace_id=workspace_id)
            _record_link_audit(task_id, "link", "workspace", workspace_id, source=source)
            maybe_add_activity_comment(
                task_id=task_id, action_type="LINK", actor_id="system", source=source,
                metadata={"linked_entity": {"type": "workspace", "id": workspace_id, "action": "link"}},
            )
            return LinkResult(success=True, already_existed=False, reason="linked")
        return LinkResult(success=False, already_existed=False,
                          reason=f"Failed to link task {task_id} to workspace {workspace_id}",
                          error_code="LINK_FAILED")
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to workspace {workspace_id}: {type(e).__name__}", exc_info=True)
        return LinkResult(success=False, already_existed=False,
                          reason=f"{type(e).__name__}: {e}", error_code="EXCEPTION")
