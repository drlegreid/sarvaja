"""Cross-entity link miner: JSONL -> TypeDB relations.

Scans Claude Code session JSONL for references to tasks, rules, gaps,
and decisions, then creates TypeDB linkage relations. Reuses existing
extractors from evidence_scanner.

Per SESSION-METRICS-01-v1.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from governance.evidence_scanner.extractors import (
    extract_gap_refs,
    extract_rule_refs,
    extract_task_refs,
)
from governance.services.ingestion_checkpoint import (
    IngestionCheckpoint,
    load_checkpoint,
    save_checkpoint,
)

logger = logging.getLogger(__name__)

# Decision reference pattern (not in evidence_scanner)
_DECISION_PATTERN = re.compile(r"\b(DECISION-\d{3,})\b", re.IGNORECASE)


def _extract_decision_refs(content: str) -> set[str]:
    """Extract DECISION-NNN references from content."""
    return {m.upper() for m in _DECISION_PATTERN.findall(content)}


def _get_typedb_client() -> Any:
    """Get TypeDB client via stores config.

    Returns a TypeDB client instance (typed as Any to avoid import dependency).
    """
    from governance.stores.config import get_typedb_client
    return get_typedb_client()


def _validate_entity_exists(
    client, entity_type: str, entity_id: str, cache: dict[str, bool]
) -> bool:
    """Check if entity exists in TypeDB, with per-run cache."""
    key = f"{entity_type}:{entity_id}"
    if key in cache:
        return cache[key]

    exists = False
    try:
        if entity_type == "task":
            exists = client.get_task(entity_id) is not None
        elif entity_type == "rule":
            # BUG-LINKMINER-001: TypeDB method is get_rule_by_id, not get_rule
            exists = client.get_rule_by_id(entity_id) is not None
        elif entity_type == "decision":
            # BUG-LINKMINER-001: No get_decision() method; use get_all_decisions filter
            # BUG-236-LNK-001: Cache decision ID set to avoid O(N*M) re-fetch
            _dkey = "_all_decision_ids"
            if _dkey not in cache:
                # BUG-257-LNK-001: Guard against None return from get_all_decisions
                all_decisions = client.get_all_decisions() or []
                cache[_dkey] = {d.decision_id for d in all_decisions}
            exists = entity_id in cache[_dkey]
    except Exception as e:
        # BUG-257-LNK-002: Log TypeDB failures instead of silently swallowing
        logger.warning(f"TypeDB validation failed for {entity_type}:{entity_id}: {e}")
        exists = False

    cache[key] = exists
    return exists


def mine_session_links(
    jsonl_path: Path,
    session_id: str,
    *,
    batch_size: int = 20,
    validate: bool = True,
    dry_run: bool = False,
    start_line: int = 0,
    checkpoint_dir: Path | None = None,
) -> dict[str, Any]:
    """Mine JSONL for entity references and create TypeDB relations.

    Args:
        jsonl_path: Path to the .jsonl file.
        session_id: Session to link entities to.
        batch_size: TypeDB writes per batch before checkpoint.
        validate: Check entity existence before linking.
        dry_run: Report refs found without creating links.
        start_line: Resume from this line offset.
        checkpoint_dir: Override checkpoint storage location.

    Returns:
        Dict with tasks_linked, rules_linked, decisions_linked, refs_found, errors.
    """
    from governance.session_metrics.parser import parse_log_file_extended

    result: dict[str, Any] = {
        "tasks_linked": 0,
        "rules_linked": 0,
        "decisions_linked": 0,
        "gaps_linked": 0,
        "refs_found": {"tasks": [], "rules": [], "decisions": [], "gaps": []},
        "status": "success",
        "errors": [],
    }

    # Collect all unique refs across the file
    task_refs: set[str] = set()
    rule_refs: set[str] = set()
    decision_refs: set[str] = set()
    gap_refs: set[str] = set()

    # BUG-286-MINE-001: Guard against missing JSONL file before streaming
    if not Path(jsonl_path).exists():
        result["status"] = "error"
        result["errors"] = [f"JSONL file not found: {jsonl_path}"]
        return result

    entries = parse_log_file_extended(
        jsonl_path, include_thinking=False, start_line=start_line
    )

    # BUG-346-LNK-001: Truncate per-entry text before regex extraction to prevent
    # DoS via megabyte-scale assistant messages triggering regex backtracking
    _MAX_REF_TEXT = 50_000

    for entry in entries:
        text = entry.text_content or ""
        if not text:
            continue

        text = text[:_MAX_REF_TEXT]
        task_refs.update(extract_task_refs(text))
        rule_refs.update(extract_rule_refs(text))
        decision_refs.update(_extract_decision_refs(text))
        gap_refs.update(extract_gap_refs(text))

    result["refs_found"] = {
        "tasks": sorted(task_refs),
        "rules": sorted(rule_refs),
        "decisions": sorted(decision_refs),
        "gaps": sorted(gap_refs),
    }

    total_refs = len(task_refs) + len(rule_refs) + len(decision_refs) + len(gap_refs)
    logger.info(
        f"Found {total_refs} unique refs: "
        f"{len(task_refs)} tasks, {len(rule_refs)} rules, "
        f"{len(decision_refs)} decisions, {len(gap_refs)} gaps"
    )

    if dry_run:
        result["status"] = "dry_run"
        return result

    # Get TypeDB client
    client = _get_typedb_client()
    if not client:
        result["status"] = "error"
        result["errors"].append("TypeDB client unavailable")
        return result

    entity_cache: dict[str, bool] = {}

    # Link tasks
    for task_id in sorted(task_refs):
        if validate and not _validate_entity_exists(client, "task", task_id, entity_cache):
            continue
        try:
            from governance.services.tasks_mutations import link_task_to_session
            if link_task_to_session(task_id, session_id, source="ingestion"):
                result["tasks_linked"] += 1
        except Exception as e:
            result["errors"].append(f"Task link {task_id}: {e}")

    # Link gaps (gaps are tasks with item_type=gap)
    for gap_id in sorted(gap_refs):
        if validate and not _validate_entity_exists(client, "task", gap_id, entity_cache):
            continue
        try:
            from governance.services.tasks_mutations import link_task_to_session
            if link_task_to_session(gap_id, session_id, source="ingestion"):
                result["gaps_linked"] += 1
        except Exception as e:
            result["errors"].append(f"Gap link {gap_id}: {e}")

    # Link rules
    for rule_id in sorted(rule_refs):
        if validate and not _validate_entity_exists(client, "rule", rule_id, entity_cache):
            continue
        try:
            ok = client.link_rule_to_session(session_id, rule_id)
            if ok:
                result["rules_linked"] += 1
        except Exception as e:
            result["errors"].append(f"Rule link {rule_id}: {e}")

    # Link decisions
    for decision_id in sorted(decision_refs):
        if validate and not _validate_entity_exists(client, "decision", decision_id, entity_cache):
            continue
        try:
            ok = client.link_decision_to_session(session_id, decision_id)
            if ok:
                result["decisions_linked"] += 1
        except Exception as e:
            result["errors"].append(f"Decision link {decision_id}: {e}")

    # Update checkpoint
    ckpt = load_checkpoint(session_id, checkpoint_dir)
    if ckpt is None:
        ckpt = IngestionCheckpoint(
            session_id=session_id, jsonl_path=str(jsonl_path)
        )
    ckpt.phase = "linking_complete"
    ckpt.links_created = (
        result["tasks_linked"] + result["rules_linked"]
        + result["decisions_linked"] + result["gaps_linked"]
    )
    for err in result["errors"]:
        ckpt.add_error(err)
    save_checkpoint(ckpt, checkpoint_dir)

    if result["errors"]:
        result["status"] = "partial"

    return result
