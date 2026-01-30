"""
Task Verification Routes.

Per RULE-032: File Size Limit (< 300 lines)
Per WORKFLOW-SEQ-01-v1: Verification hierarchy (L1→L2→L3).
Per Directive 2: Verification subtasks based on testing strategy.

Created: 2026-01-17
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging

from governance.models import TaskResponse
from governance.stores import (
    get_typedb_client,
    _tasks_store,
    task_to_response
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/tasks/{task_id}/create-verification-subtasks", response_model=List[TaskResponse])
async def create_verification_subtasks(
    task_id: str,
    include_l3: bool = Query(False, description="Include L3 user flow verification subtask")
):
    """
    Create verification subtasks for a task per WORKFLOW-SEQ-01-v1.

    Per Directive 2: Verification levels as explicit subtasks.
    Per WORKFLOW-SEQ-01-v1: 3-level validation hierarchy.

    Creates child tasks:
    - {task_id}-L1-VERIFY: Technical fix verification
    - {task_id}-L2-VERIFY: E2E functionality verification
    - {task_id}-L3-VERIFY: User flow verification (optional)

    Subtask completion promotes parent task resolution:
    - L1 complete → parent stays IMPLEMENTED
    - L2 complete → parent promoted to VALIDATED
    - L3 complete → parent promoted to CERTIFIED
    """
    client = get_typedb_client()

    # Get parent task to inherit phase
    parent_task = None
    if client:
        try:
            parent_task = client.get_task(task_id)
        except Exception as e:
            logger.debug(f"Failed to get parent task from TypeDB: {e}")

    if not parent_task:
        if task_id not in _tasks_store:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        parent_data = _tasks_store[task_id]
        parent_task = type('Task', (), parent_data)()

    created_subtasks = []
    verification_levels = [
        ("L1", "Technical fix verification", "Verify the technical fix resolves the issue"),
        ("L2", "E2E functionality verification", "Verify feature works end-to-end in browser"),
    ]
    if include_l3:
        verification_levels.append(
            ("L3", "User flow verification", "Verify full user journey with stakeholder acceptance")
        )

    for level, name, description in verification_levels:
        subtask_id = f"{task_id}-{level}-VERIFY"

        # Check if subtask already exists
        existing = None
        if client:
            try:
                existing = client.get_task(subtask_id)
            except Exception as e:
                logger.debug(f"Failed to check subtask existence: {e}")

        if existing:
            created_subtasks.append(task_to_response(existing))
            continue

        # Determine target resolution for this verification level
        if level == "L3":
            target_res = "CERTIFIED"
        elif level == "L2":
            target_res = "VALIDATED"
        else:
            target_res = "IMPLEMENTED"

        # Create subtask data
        subtask_data = {
            "task_id": subtask_id,
            "description": f"[{level}] {name}",
            "phase": getattr(parent_task, 'phase', 'VERIFICATION'),
            "status": "TODO",
            "body": f"""## Verification Task

**Parent:** {task_id}
**Level:** {level}
**Type:** {name}

### Checklist
- [ ] Verification performed
- [ ] Evidence documented
- [ ] Ready for promotion

### Evidence Required
Document verification results and call:
```
PUT /api/tasks/{task_id}/promote-resolution
?target_resolution={target_res}
&evidence=<your evidence>
&verification_level={level}
```
"""
        }

        if client:
            try:
                # Create task in TypeDB
                from governance.typedb.entities import Task as TaskEntity
                new_task = TaskEntity(
                    id=subtask_id,
                    name=f"[{level}] {name}",
                    status="TODO",
                    phase=subtask_data["phase"],
                    description=description,
                    body=subtask_data["body"]
                )
                created = client.create_task(new_task)
                if created:
                    # Link as child of parent task
                    client.link_parent_task(subtask_id, task_id)
                    created_subtasks.append(task_to_response(created))
                    logger.info(f"Created verification subtask {subtask_id} for {task_id}")
            except Exception as e:
                logger.warning(f"Failed to create subtask in TypeDB: {e}")
                # Fallback to in-memory
                _tasks_store[subtask_id] = subtask_data
                created_subtasks.append(TaskResponse(**subtask_data))
        else:
            _tasks_store[subtask_id] = subtask_data
            created_subtasks.append(TaskResponse(**subtask_data))

    return created_subtasks


@router.get("/tasks/{task_id}/verification-status")
async def get_verification_status(task_id: str):
    """
    Get the verification status of a task and its subtasks.

    Returns which verification levels have been completed and
    the current resolution status.
    """
    client = get_typedb_client()

    # Get parent task
    parent_task = None
    if client:
        try:
            parent_task = client.get_task(task_id)
        except Exception as e:
            logger.debug(f"Failed to get task for verification status: {e}")

    if not parent_task and task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Check verification subtasks
    verification_status = {
        "task_id": task_id,
        "resolution": getattr(parent_task, 'resolution', None) or _tasks_store.get(task_id, {}).get("resolution", "NONE"),
        "verification_levels": {
            "L1": {"exists": False, "status": None, "completed": False},
            "L2": {"exists": False, "status": None, "completed": False},
            "L3": {"exists": False, "status": None, "completed": False},
        }
    }

    for level in ["L1", "L2", "L3"]:
        subtask_id = f"{task_id}-{level}-VERIFY"
        subtask = None

        if client:
            try:
                subtask = client.get_task(subtask_id)
            except Exception as e:
                logger.debug(f"Failed to get verification subtask: {e}")

        if not subtask and subtask_id in _tasks_store:
            subtask = type('Task', (), _tasks_store[subtask_id])()

        if subtask:
            status = getattr(subtask, 'status', None)
            verification_status["verification_levels"][level] = {
                "exists": True,
                "status": status,
                "completed": status in ("DONE", "CLOSED", "completed")
            }

    # Determine highest completed level
    if verification_status["verification_levels"]["L3"]["completed"]:
        verification_status["highest_completed"] = "L3"
        verification_status["expected_resolution"] = "CERTIFIED"
    elif verification_status["verification_levels"]["L2"]["completed"]:
        verification_status["highest_completed"] = "L2"
        verification_status["expected_resolution"] = "VALIDATED"
    elif verification_status["verification_levels"]["L1"]["completed"]:
        verification_status["highest_completed"] = "L1"
        verification_status["expected_resolution"] = "IMPLEMENTED"
    else:
        verification_status["highest_completed"] = None
        verification_status["expected_resolution"] = "NONE"

    # Check for resolution mismatch
    actual_res = verification_status["resolution"]
    expected_res = verification_status["expected_resolution"]
    if actual_res != expected_res and expected_res != "NONE":
        verification_status["resolution_mismatch"] = True
        verification_status["recommendation"] = f"Resolution should be promoted to {expected_res}"
    else:
        verification_status["resolution_mismatch"] = False

    return verification_status
