"""Task Linking Operations — link/unlink tasks to rules, sessions, documents, workspaces.

Per DOC-SIZE-01-v1: Extracted from tasks_mutations.py.
"""
import logging

from governance.stores import get_typedb_client, _tasks_store
from .tasks_preload import _monitor

logger = logging.getLogger(__name__)


def link_task_to_rule(task_id: str, rule_id: str, source: str = "rest") -> bool:
    """Link task to rule via implements-rule relation."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_rule(task_id, rule_id)
        if result:
            _monitor("link_rule", task_id, source=source, rule_id=rule_id)
        return bool(result)
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-007: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to rule {rule_id}: {type(e).__name__}", exc_info=True)
        return False


def link_task_to_session(task_id: str, session_id: str, source: str = "rest") -> bool:
    """Link task to session via completed-in relation."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_session(task_id, session_id)
        if result:
            # SRVJ-BUG-002: Keep _tasks_store in sync for DONE gate validation
            if task_id in _tasks_store:
                sessions = _tasks_store[task_id].get("linked_sessions", [])
                if session_id not in sessions:
                    sessions.append(session_id)
                    _tasks_store[task_id]["linked_sessions"] = sessions
            _monitor("link_session", task_id, source=source, session_id=session_id)
        return bool(result)
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-008: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to session {session_id}: {type(e).__name__}", exc_info=True)
        return False


def link_task_to_document(task_id: str, document_path: str, source: str = "rest") -> bool:
    """Link task to document via document-references-task relation."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_document(task_id, document_path)
        if result:
            # SRVJ-BUG-002: Keep _tasks_store in sync for DONE gate validation
            if task_id in _tasks_store:
                docs = _tasks_store[task_id].get("linked_documents", [])
                if document_path not in docs:
                    docs.append(document_path)
                    _tasks_store[task_id]["linked_documents"] = docs
            _monitor("link_document", task_id, source=source, document_path=document_path)
        return bool(result)
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-009: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to link task {task_id} to document {document_path}: {type(e).__name__}", exc_info=True)
        return False


def unlink_task_from_document(task_id: str, document_path: str, source: str = "rest") -> bool:
    """Unlink document from task."""
    client = get_typedb_client()
    if not client:
        return False
    try:
        result = client.unlink_task_from_document(task_id, document_path)
        if result:
            _monitor("unlink_document", task_id, source=source, document_path=document_path)
        return bool(result)
    except Exception as e:
        # BUG-404-TM-006: Add exc_info for stack trace preservation
        # BUG-464-TM-010: Sanitize logger message — exc_info=True already captures full stack
        logger.error(f"Failed to unlink document {document_path} from task {task_id}: {type(e).__name__}", exc_info=True)
        return False


def link_task_to_workspace(task_id: str, workspace_id: str, source: str = "rest") -> bool:
    """Link task to workspace via workspace-has-task relation.

    Per EPIC-GOV-TASKS-V2 Phase 4: Task-Workspace Bidirectional Linking.
    """
    client = get_typedb_client()
    if not client:
        return False
    try:
        if not client.get_task(task_id):
            return False
        result = client.link_task_to_workspace(workspace_id, task_id)  # BUG-WS-CREATE-001: fix arg order
        if result:
            _monitor("link_workspace", task_id, source=source, workspace_id=workspace_id)
        return bool(result)
    except Exception as e:
        logger.error(f"Failed to link task {task_id} to workspace {workspace_id}: {type(e).__name__}", exc_info=True)
        return False
