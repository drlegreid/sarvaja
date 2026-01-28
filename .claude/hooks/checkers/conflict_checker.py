"""
Merge Conflict Checker - Multi-Agent Observability
===================================================
Per MULTI-007: Detect git merge conflicts in multi-agent workflows.

Detects:
- Unmerged paths (UU status in git)
- Merge conflict markers in files (<<<<<<, ======, >>>>>>)
- Conflicting branch states

Created: 2026-01-19
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def run_git_command(args: List[str], cwd: Path = PROJECT_ROOT) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Git command timed out"
    except FileNotFoundError:
        return -1, "", "Git not found"


def check_merge_conflicts() -> Dict[str, Any]:
    """
    Check for git merge conflicts.

    Returns:
        Dict with conflict status, files, and details
    """
    conflicts = []

    # Check git status for unmerged paths (UU, AA, DD, AU, UA, DU, UD)
    returncode, stdout, stderr = run_git_command(["status", "--porcelain"])

    if returncode != 0:
        return {
            "error": f"Git status failed: {stderr}",
            "has_conflicts": False,
            "conflicts": []
        }

    # Parse status output for conflict indicators
    unmerged_statuses = {"UU", "AA", "DD", "AU", "UA", "DU", "UD"}

    for line in stdout.strip().split("\n"):
        if not line:
            continue

        # First two characters are the status
        status = line[:2]
        filename = line[3:].strip()

        if status in unmerged_statuses:
            conflicts.append({
                "file": filename,
                "status": status,
                "status_meaning": _get_status_meaning(status),
                "severity": "CRITICAL"
            })

    # Also check if we're in a merge state
    merge_state = _check_merge_state()

    return {
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "merge_state": merge_state,
        "status": "CONFLICT" if conflicts else "OK"
    }


def _get_status_meaning(status: str) -> str:
    """Get human-readable meaning of git status code."""
    meanings = {
        "UU": "both modified",
        "AA": "both added",
        "DD": "both deleted",
        "AU": "added by us",
        "UA": "added by them",
        "DU": "deleted by us",
        "UD": "deleted by them"
    }
    return meanings.get(status, "unmerged")


def _check_merge_state() -> Dict[str, Any]:
    """Check if we're in the middle of a merge/rebase/cherry-pick."""
    git_dir = PROJECT_ROOT / ".git"

    state = {
        "in_merge": (git_dir / "MERGE_HEAD").exists(),
        "in_rebase": (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists(),
        "in_cherry_pick": (git_dir / "CHERRY_PICK_HEAD").exists(),
        "in_revert": (git_dir / "REVERT_HEAD").exists()
    }

    state["in_conflicted_state"] = any(state.values())

    return state


def scan_for_conflict_markers() -> List[Dict[str, Any]]:
    """
    Scan tracked files for conflict markers (<<<<<<, ======, >>>>>>).

    This catches conflicts that may have been marked as resolved but
    still contain markers.

    Returns:
        List of files containing conflict markers
    """
    markers_found = []

    # Get list of tracked files
    returncode, stdout, _ = run_git_command(["ls-files"])
    if returncode != 0:
        return []

    tracked_files = [f for f in stdout.strip().split("\n") if f]

    # Search for conflict markers using git grep (faster than reading files)
    # Use precise patterns to avoid false positives from decorative separators:
    # - <<<<<<< must be followed by space or content (branch name)
    # - ======= must be exactly 7 equals (end of line or followed by space)
    # - >>>>>>> must be followed by space or content (branch name)
    returncode, stdout, _ = run_git_command([
        "grep", "-l", "-E", "^<<<<<<< |^=======$|^>>>>>>> "
    ])

    if returncode == 0 and stdout.strip():
        for filename in stdout.strip().split("\n"):
            if filename:
                markers_found.append({
                    "file": filename,
                    "issue": "Contains conflict markers",
                    "severity": "WARNING"
                })

    return markers_found


def get_conflict_summary() -> Dict[str, Any]:
    """
    Get comprehensive conflict status summary for dashboard.

    Returns:
        Dict with conflict status, merge state, and alerts
    """
    conflict_status = check_merge_conflicts()
    marker_files = scan_for_conflict_markers()

    # Build alerts
    alerts = []

    for conflict in conflict_status.get("conflicts", []):
        alerts.append({
            "type": "MERGE_CONFLICT",
            "severity": "CRITICAL",
            "message": f"Merge conflict in {conflict['file']} ({conflict['status_meaning']})",
            "details": conflict
        })

    for marker in marker_files:
        # Don't duplicate if already in conflicts list
        conflict_files = [c["file"] for c in conflict_status.get("conflicts", [])]
        if marker["file"] not in conflict_files:
            alerts.append({
                "type": "CONFLICT_MARKERS",
                "severity": "WARNING",
                "message": f"Conflict markers found in {marker['file']}",
                "details": marker
            })

    merge_state = conflict_status.get("merge_state", {})
    if merge_state.get("in_merge"):
        alerts.append({
            "type": "MERGE_IN_PROGRESS",
            "severity": "WARNING",
            "message": "Merge in progress - requires resolution",
            "details": merge_state
        })
    if merge_state.get("in_rebase"):
        alerts.append({
            "type": "REBASE_IN_PROGRESS",
            "severity": "WARNING",
            "message": "Rebase in progress - requires resolution",
            "details": merge_state
        })

    return {
        "has_conflicts": conflict_status.get("has_conflicts", False),
        "conflict_count": conflict_status.get("conflict_count", 0),
        "conflicts": conflict_status.get("conflicts", []),
        "marker_files": marker_files,
        "marker_count": len(marker_files),
        "merge_state": merge_state,
        "alerts": alerts,
        "alert_count": len(alerts),
        "status": "CRITICAL" if conflict_status.get("has_conflicts") else (
            "WARNING" if alerts else "OK"
        )
    }


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check":
            result = check_merge_conflicts()
            print(json.dumps(result, indent=2))

        elif cmd == "markers":
            result = scan_for_conflict_markers()
            print(json.dumps(result, indent=2))

        elif cmd == "summary":
            result = get_conflict_summary()
            print(json.dumps(result, indent=2))

        else:
            print("Usage: python conflict_checker.py [check | markers | summary]")
    else:
        # Default: show summary
        result = get_conflict_summary()
        print(json.dumps(result, indent=2))
