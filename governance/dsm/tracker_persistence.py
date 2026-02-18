"""DSM Tracker Persistence - State file I/O operations.

Per DOC-SIZE-01-v1: Split from tracker.py (411 lines → under 300).
Per WORKFLOW-DSP-01-v1:
- Atomic file writes (temp + rename)
- Abandoned cycle detection (>24h auto-abort)
- Corrupted state file backup + graceful recovery

Created: 2026-02-09 (split from tracker.py)
"""
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from governance.dsm.models import DSMCycle, PhaseCheckpoint

logger = logging.getLogger(__name__)

# Per WORKFLOW-DSP-01-v1: Auto-abort threshold for abandoned cycles
ABANDONED_CYCLE_HOURS = 24


def load_state(state_file: Path) -> Optional[DSMCycle]:
    """Load cycle state from JSON file.

    Per WORKFLOW-DSP-01-v1:
    - Backs up corrupted state files
    - Gracefully handles load failures
    - Returns the current_cycle or None

    Returns:
        DSMCycle if a current cycle was found, None otherwise.
    """
    if not state_file.exists():
        return None

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        if state.get("current_cycle"):
            cycle_data = state["current_cycle"]
            return DSMCycle(
                cycle_id=cycle_data["cycle_id"],
                batch_id=cycle_data.get("batch_id"),
                start_time=cycle_data.get("start_time"),
                end_time=cycle_data.get("end_time"),
                current_phase=cycle_data.get("current_phase", "idle"),
                phases_completed=cycle_data.get("phases_completed", []),
                checkpoints=[
                    PhaseCheckpoint(**cp) for cp in cycle_data.get("checkpoints", [])
                ],
                findings=cycle_data.get("findings", []),
                metrics=cycle_data.get("metrics", {})
            )
        return None

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # BUG-473-DTP-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"Failed to load DSM state: {type(e).__name__}. Backing up corrupted file.", exc_info=True)
        backup_path = state_file.with_suffix(
            f".backup-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        )
        try:
            shutil.copy2(state_file, backup_path)
            logger.info(f"Corrupted state backed up to {backup_path}")
        # BUG-280-PERSIST-002: Log backup failure instead of silently swallowing
        except Exception as backup_err:
            logger.error(f"Failed to back up corrupted state file {state_file}: {backup_err}")
        return None


def save_state(state_file: Path, current_cycle: Optional[DSMCycle],
               completed_count: int) -> None:
    """Save cycle state to JSON file using atomic write.

    Per WORKFLOW-DSP-01-v1: Uses temp file + atomic rename to prevent
    corruption on crash during write.
    """
    state = {
        "current_cycle": current_cycle.to_dict() if current_cycle else None,
        "completed_count": completed_count,
        "last_updated": datetime.now().isoformat()
    }

    dir_path = state_file.parent
    dir_path.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=".dsm_state_",
        dir=str(dir_path)
    )
    # BUG-280-PERSIST-001: Guard against FD leak if os.fdopen itself raises
    try:
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
            fd = -1  # fdopen took ownership; mark as closed
        except Exception:
            if fd != -1:
                os.close(fd)
                fd = -1
            raise
        os.replace(temp_path, state_file)
    except Exception as e:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        # BUG-473-DTP-2: Sanitize logger message + add exc_info for stack trace preservation
        logger.error(f"Failed to save DSM state: {type(e).__name__}", exc_info=True)
        raise


def check_abandoned_cycle(cycle: DSMCycle) -> bool:
    """Check if a cycle has been abandoned for >24h.

    Per WORKFLOW-DSP-01-v1: Stale cycles indicate forgotten cleanup.

    Returns:
        True if the cycle was auto-aborted, False otherwise.
    """
    if not cycle or cycle.current_phase == "complete":
        return False

    start_time_str = cycle.start_time
    if not start_time_str:
        return False

    try:
        if "+" in start_time_str or start_time_str.endswith("Z"):
            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        else:
            start_time = datetime.fromisoformat(start_time_str)
            start_time = start_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_hours = (now - start_time).total_seconds() / 3600

        if age_hours > ABANDONED_CYCLE_HOURS:
            logger.warning(
                f"Auto-aborting abandoned cycle {cycle.cycle_id} "
                f"(age: {age_hours:.1f}h > {ABANDONED_CYCLE_HOURS}h threshold)"
            )
            cycle.metrics["auto_aborted"] = True
            cycle.metrics["abort_reason"] = f"Abandoned for {age_hours:.1f}h"
            cycle.end_time = now.isoformat()
            cycle.current_phase = "aborted"
            return True
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse cycle start time for age check: {e}")

    return False
