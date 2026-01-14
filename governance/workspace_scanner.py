"""
Workspace Task Scanner - Capture tasks from workspace files to TypeDB.

Per P10.10: Workspace Task Capture.
Per DECISION-003: TypeDB-First Strategy.
Per RULE-012: DSP Semantic Code Structure.

Scans workspace markdown files for tasks and syncs to TypeDB.

Sources:
- TODO.md: Current sprint tasks
- docs/backlog/phases/PHASE-*.md: Phase task lists
- docs/backlog/rd/*.md: R&D task lists

Created: 2024-12-28
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from governance.task_parsers import (
    normalize_status,
    parse_markdown_table,
    extract_task_id,
    extract_gap_id,
    extract_linked_rules,
)

logger = logging.getLogger(__name__)

# Workspace root (relative to this file)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class ParsedTask:
    """Parsed task from workspace file."""
    task_id: str
    name: str
    status: str
    phase: Optional[str] = None
    description: Optional[str] = None
    gap_id: Optional[str] = None
    source_file: Optional[str] = None
    linked_rules: Optional[List[str]] = None


def parse_todo_md(filepath: str) -> List[ParsedTask]:
    """Parse TODO.md for tasks."""
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"Failed to read {filepath}: {e}")
        return tasks

    rows = parse_markdown_table(content)
    rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)

    for row in rows:
        task_id = extract_task_id(row)
        if not task_id:
            continue

        # Get task name from 'task' or 'description' column
        name = row.get("task", row.get("description", ""))
        status = normalize_status(row.get("status", "TODO"))
        phase = row.get("phase", "")
        description = row.get("description", name)
        gap_id = extract_gap_id(row)

        tasks.append(ParsedTask(
            task_id=task_id,
            name=name,
            status=status,
            phase=phase if phase else None,
            description=description,
            gap_id=gap_id,
            source_file=rel_path,
            linked_rules=extract_linked_rules(row)
        ))

    return tasks


def parse_phase_md(filepath: str) -> List[ParsedTask]:
    """Parse PHASE-*.md for tasks."""
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"Failed to read {filepath}: {e}")
        return tasks

    # Extract phase from filename (e.g., PHASE-10.md -> P10)
    filename = os.path.basename(filepath)
    phase_match = re.search(r'PHASE-(\d+)', filename)
    phase = f"P{phase_match.group(1)}" if phase_match else None

    rows = parse_markdown_table(content)
    rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)

    for row in rows:
        task_id = extract_task_id(row)
        if not task_id:
            continue

        # Get task name from 'description' column (phase docs use this format)
        name = row.get("description", row.get("task", ""))
        # Clean markdown formatting
        name = re.sub(r'\*\*([^*]+)\*\*', r'\1', name)  # Remove bold
        name = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', name)  # Remove links

        status = normalize_status(row.get("status", "TODO"))
        gap_id = extract_gap_id(row)

        tasks.append(ParsedTask(
            task_id=task_id,
            name=name[:200] if name else task_id,  # Limit name length
            status=status,
            phase=phase,
            description=name,
            gap_id=gap_id,
            source_file=rel_path,
            linked_rules=extract_linked_rules(row)
        ))

    return tasks


def parse_rd_md(filepath: str) -> List[ParsedTask]:
    """Parse RD-*.md for R&D tasks."""
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.warning(f"Failed to read {filepath}: {e}")
        return tasks

    rows = parse_markdown_table(content)
    rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)

    for row in rows:
        # R&D docs use 'id' column
        task_id = row.get("id", extract_task_id(row))
        if not task_id:
            continue

        name = row.get("task", row.get("description", ""))
        status = normalize_status(row.get("status", "TODO"))
        priority = row.get("priority", "")
        notes = row.get("notes", "")

        tasks.append(ParsedTask(
            task_id=task_id,
            name=name,
            status=status,
            phase="R&D",
            description=f"{name}. {notes}".strip() if notes else name,
            gap_id=extract_gap_id(row),
            source_file=rel_path,
            linked_rules=extract_linked_rules(row)
        ))

    return tasks


def scan_workspace() -> List[ParsedTask]:
    """Scan all workspace files for tasks."""
    all_tasks = []

    # 1. TODO.md
    todo_path = os.path.join(WORKSPACE_ROOT, "TODO.md")
    if os.path.exists(todo_path):
        all_tasks.extend(parse_todo_md(todo_path))
        logger.info(f"Parsed {len(all_tasks)} tasks from TODO.md")

    # 2. Phase docs
    phases_dir = os.path.join(WORKSPACE_ROOT, "docs", "backlog", "phases")
    if os.path.exists(phases_dir):
        for filename in os.listdir(phases_dir):
            if filename.startswith("PHASE-") and filename.endswith(".md"):
                filepath = os.path.join(phases_dir, filename)
                phase_tasks = parse_phase_md(filepath)
                all_tasks.extend(phase_tasks)
                logger.info(f"Parsed {len(phase_tasks)} tasks from {filename}")

    # 3. R&D docs
    rd_dir = os.path.join(WORKSPACE_ROOT, "docs", "backlog", "rd")
    if os.path.exists(rd_dir):
        for filename in os.listdir(rd_dir):
            if filename.startswith("RD-") and filename.endswith(".md"):
                filepath = os.path.join(rd_dir, filename)
                rd_tasks = parse_rd_md(filepath)
                all_tasks.extend(rd_tasks)
                logger.info(f"Parsed {len(rd_tasks)} tasks from {filename}")

    logger.info(f"Total tasks scanned: {len(all_tasks)}")
    return all_tasks


def sync_tasks_to_typedb(tasks: List[ParsedTask]) -> Dict[str, int]:
    """
    Sync parsed tasks to TypeDB.

    Returns dict with counts: inserted, updated, skipped, errors.
    """
    from governance.client import get_client

    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        client = get_client()
        if not client or not client.is_connected():
            logger.error("TypeDB client not available")
            return stats
    except Exception as e:
        logger.error(f"Failed to connect to TypeDB: {e}")
        return stats

    for task in tasks:
        try:
            existing = client.get_task(task.task_id)

            if existing:
                # Check if status changed
                if existing.status != task.status:
                    client.update_task_status(task.task_id, task.status)
                    stats["updated"] += 1
                    logger.debug(f"Updated {task.task_id}: {existing.status} -> {task.status}")
                else:
                    stats["skipped"] += 1
            else:
                # Insert new task
                result = client.insert_task(
                    task_id=task.task_id,
                    name=task.name,
                    status=task.status,
                    phase=task.phase,
                    body=task.description,
                    gap_id=task.gap_id,
                    linked_rules=task.linked_rules
                )
                if result:
                    stats["inserted"] += 1
                    logger.debug(f"Inserted {task.task_id}")
                else:
                    stats["errors"] += 1

        except Exception as e:
            logger.warning(f"Failed to sync task {task.task_id}: {e}")
            stats["errors"] += 1

    return stats


def capture_workspace_tasks() -> Dict[str, Any]:
    """
    Main entry point: Scan workspace and sync to TypeDB.

    Per P10.10: Workspace Task Capture.
    """
    tasks = scan_workspace()
    stats = sync_tasks_to_typedb(tasks)

    result = {
        "scanned": len(tasks),
        "inserted": stats["inserted"],
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "errors": stats["errors"],
        "sources": [
            "TODO.md",
            "docs/backlog/phases/PHASE-*.md",
            "docs/backlog/rd/RD-*.md"
        ]
    }

    logger.info(f"Workspace capture complete: {result}")
    return result


# CLI for testing
if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Workspace Task Scanner Test")
    print("=" * 60)

    # Test scanning
    tasks = scan_workspace()
    print(f"\nScanned {len(tasks)} tasks:")

    # Group by source
    by_source: Dict[str, List[ParsedTask]] = {}
    for t in tasks:
        src = t.source_file or "unknown"
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(t)

    for src, src_tasks in by_source.items():
        print(f"\n  {src}: {len(src_tasks)} tasks")
        for t in src_tasks[:3]:
            print(f"    - {t.task_id}: {t.name[:50]}... [{t.status}]")
        if len(src_tasks) > 3:
            print(f"    ... and {len(src_tasks) - 3} more")

    # Test sync (if TypeDB available)
    print("\n--- Syncing to TypeDB ---")
    result = capture_workspace_tasks()
    print(json.dumps(result, indent=2))
