"""Task Duplicate Detection — similarity matching for issue triage.

Per DOC-SIZE-01-v1: Extracted from tasks.py.
Per EPIC-TASK-QUALITY-V3 P16: Issue Triage Workflow.
"""
import logging
from typing import List

from governance.stores import get_all_tasks_from_typedb

logger = logging.getLogger(__name__)


def _jaccard_word_similarity(a: str, b: str) -> float:
    """Compute Jaccard word similarity between two strings.

    Returns a float in [0, 1]. Used for duplicate task detection (P16).
    """
    if not a or not b:
        return 0.0
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


# Threshold for duplicate warning (Jaccard word similarity)
DUPLICATE_SIMILARITY_THRESHOLD = 0.8


def _find_duplicate_tasks(
    summary: str,
    description: str,
    exclude_task_id: str,
) -> List[str]:
    """Find existing tasks with similar summaries for duplicate detection (P16).

    Returns list of warning strings for any matches above threshold.
    Non-blocking — used to warn, not block creation.
    """
    search_text = summary or description
    if not search_text or len(search_text.strip()) < 5:
        return []

    try:
        all_tasks = get_all_tasks_from_typedb(allow_fallback=True)
    except Exception:
        return []

    warnings = []
    for t in all_tasks:
        tid = t.get("task_id", "")
        if tid == exclude_task_id:
            continue
        # Skip test artifacts and terminal tasks
        if tid.startswith("TEST-"):
            continue
        if t.get("status") in ("CLOSED", "CANCELLED"):
            continue

        candidate = t.get("summary") or t.get("description") or ""
        if not candidate:
            continue

        sim = _jaccard_word_similarity(search_text, candidate)
        if sim >= DUPLICATE_SIMILARITY_THRESHOLD:
            warnings.append(
                f"Possible duplicate of {tid} "
                f"(similarity {sim:.0%}): {candidate[:80]}"
            )
            if len(warnings) >= 3:
                break  # Cap at 3 warnings
    return warnings


def _attach_duplicate_warnings(response, summary, description, task_id):
    """Attach duplicate warnings to a create_task response (P16).

    Works with both TaskResponse (Pydantic) and dict responses.
    Non-blocking — warnings are informational only.
    """
    try:
        warnings = _find_duplicate_tasks(summary, description, task_id)
    except Exception as e:
        logger.debug(f"Duplicate detection failed: {type(e).__name__}")
        warnings = []

    if not warnings:
        return response

    # Attach warnings to response
    if hasattr(response, "warnings"):
        # Pydantic TaskResponse
        response.warnings = warnings
    elif isinstance(response, dict):
        response["warnings"] = warnings

    logger.info(
        f"[P16-DUPLICATE] Task {task_id}: {len(warnings)} duplicate warnings"
    )
    return response
