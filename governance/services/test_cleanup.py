"""
Post-test cleanup of TEST-* artifacts from in-memory stores.

Per RELIABILITY-PLAN-01-v1 Priority 4:
Removes TEST-* tasks and sessions created during test/CVP runs
to prevent data pollution in production stores.
"""
import logging

from governance.stores.data_stores import _tasks_store, _sessions_store

logger = logging.getLogger(__name__)


def cleanup_test_artifacts() -> dict:
    """
    Remove TEST-* prefixed tasks and test sessions from in-memory stores.

    Returns:
        Summary dict with tasks_removed and sessions_removed counts.
    """
    # Remove TEST-* tasks
    test_task_ids = [k for k in _tasks_store if k.startswith("TEST-")]
    for tid in test_task_ids:
        del _tasks_store[tid]

    # Remove test sessions (session IDs containing -TEST-)
    test_session_ids = [
        k for k in _sessions_store
        if "-TEST-" in k or k.startswith("TEST-")
    ]
    for sid in test_session_ids:
        del _sessions_store[sid]

    removed = {
        "tasks_removed": len(test_task_ids),
        "sessions_removed": len(test_session_ids),
    }

    if test_task_ids or test_session_ids:
        logger.info(
            f"Cleaned up {removed['tasks_removed']} test tasks, "
            f"{removed['sessions_removed']} test sessions"
        )

    return removed
