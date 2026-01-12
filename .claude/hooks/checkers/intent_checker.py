"""
Intent Checker Module for Healthcheck Integration.

Per RD-INTENT Phase 3: Provides intent continuity tracking for session start.
Per RULE-032: Modularized from healthcheck.py

Reads previous session evidence files to extract:
- Previous session intent (what was planned)
- Previous session outcome (what was achieved)
- Handoff items for current session

This enables context recovery and continuity tracking per RULE-024.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List


def find_latest_evidence_file(evidence_dir: Path, max_age_hours: int = 24) -> Optional[Path]:
    """
    Find the most recent session evidence file.

    Args:
        evidence_dir: Path to evidence directory
        max_age_hours: Only consider files from last N hours

    Returns:
        Path to most recent evidence file, or None
    """
    try:
        if not evidence_dir.exists():
            return None

        # Look for SESSION-* files (standard format)
        session_files = list(evidence_dir.glob("SESSION-*.md"))

        if not session_files:
            return None

        # Filter by age
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        recent_files = []
        for f in session_files:
            try:
                # Parse date from filename: SESSION-2026-01-10-TOPIC.md
                parts = f.stem.split("-")
                if len(parts) >= 4:
                    date_str = "-".join(parts[1:4])  # 2026-01-10
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if file_date.date() >= cutoff.date():
                        recent_files.append((f, f.stat().st_mtime))
            except Exception:
                continue

        if not recent_files:
            return None

        # Return most recently modified
        recent_files.sort(key=lambda x: x[1], reverse=True)
        return recent_files[0][0]

    except Exception:
        return None


def extract_intent_from_evidence(filepath: Path) -> Dict[str, Any]:
    """
    Extract intent and outcome information from evidence file.

    Parses markdown evidence file for:
    - Session Intent section (goal, source, planned tasks)
    - Session Outcome section (status, achieved, deferred, handoffs)

    Args:
        filepath: Path to evidence markdown file

    Returns:
        Dict with intent, outcome, and handoff data
    """
    result = {
        "session_id": "",
        "intent": None,
        "outcome": None,
        "handoff_items": [],
        "discoveries": []
    }

    try:
        content = filepath.read_text(encoding="utf-8")

        # Extract session ID from first line
        match = re.search(r"Session ID:\*\*\s*(\S+)", content)
        if match:
            result["session_id"] = match.group(1)
        else:
            # Try filename
            result["session_id"] = filepath.stem

        # Extract Intent section
        intent_match = re.search(
            r"## Session Intent\s*\n\n"
            r"\*\*Goal:\*\*\s*(.+?)\n"
            r"\*\*Source:\*\*\s*(.+?)\n",
            content,
            re.DOTALL
        )
        if intent_match:
            result["intent"] = {
                "goal": intent_match.group(1).strip(),
                "source": intent_match.group(2).strip()
            }

            # Extract planned tasks
            planned_match = re.search(
                r"### Planned Tasks\s*\n\n((?:- \[[ x]\] .+\n)+)",
                content
            )
            if planned_match:
                tasks = re.findall(r"- \[[ x]\] (\S+)", planned_match.group(1))
                result["intent"]["planned_tasks"] = tasks

        # Extract Outcome section
        outcome_match = re.search(
            r"## Session Outcome\s*\n\n"
            r"\*\*Status:\*\*\s*(\S+)",
            content
        )
        if outcome_match:
            result["outcome"] = {
                "status": outcome_match.group(1).strip()
            }

            # Extract achieved tasks
            achieved_match = re.search(
                r"### Achieved Tasks\s*\n\n((?:- \[x\] .+\n)+)",
                content
            )
            if achieved_match:
                tasks = re.findall(r"- \[x\] (\S+)", achieved_match.group(1))
                result["outcome"]["achieved_tasks"] = tasks

            # Extract deferred tasks
            deferred_match = re.search(
                r"### Deferred Tasks\s*\n\n((?:- \[ \] .+\n)+)",
                content
            )
            if deferred_match:
                tasks = re.findall(r"- \[ \] (\S+)", deferred_match.group(1))
                result["outcome"]["deferred_tasks"] = tasks

            # Extract handoff items
            handoff_match = re.search(
                r"### Handoff Items \(for next session\)\s*\n\n((?:- .+\n)+)",
                content
            )
            if handoff_match:
                items = re.findall(r"- (.+)", handoff_match.group(1))
                result["handoff_items"] = items

            # Extract discoveries
            discoveries_match = re.search(
                r"### Discoveries\s*\n\n((?:- .+\n)+)",
                content
            )
            if discoveries_match:
                items = re.findall(r"- (.+)", discoveries_match.group(1))
                result["discoveries"] = items

    except Exception:
        pass

    return result


def check_intent_continuity(evidence_dir: Path = None) -> Dict[str, Any]:
    """
    Check session intent continuity for healthcheck integration.

    Returns summary of previous session for context recovery:
    - Previous session ID and goal
    - Completion status
    - Handoff items for current session
    - Continuity recommendations

    Args:
        evidence_dir: Path to evidence directory (default: PROJECT_ROOT/evidence)

    Returns:
        Dict with continuity information for healthcheck display
    """
    result = {
        "has_previous": False,
        "previous_session": None,
        "handoff_count": 0,
        "discovery_count": 0,
        "recommendations": []
    }

    # Default evidence directory
    if evidence_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        evidence_dir = project_root / "evidence"

    # Find latest evidence file
    latest_file = find_latest_evidence_file(evidence_dir)
    if not latest_file:
        result["recommendations"].append("No recent session evidence found")
        return result

    # Extract intent data
    intent_data = extract_intent_from_evidence(latest_file)

    if not intent_data.get("intent") and not intent_data.get("outcome"):
        result["recommendations"].append(f"Previous session {intent_data['session_id']} has no intent data")
        return result

    result["has_previous"] = True
    result["previous_session"] = {
        "id": intent_data["session_id"],
        "goal": intent_data.get("intent", {}).get("goal", "Unknown"),
        "status": intent_data.get("outcome", {}).get("status", "Unknown"),
        "file": latest_file.name
    }

    result["handoff_count"] = len(intent_data.get("handoff_items", []))
    result["discovery_count"] = len(intent_data.get("discoveries", []))

    # Generate recommendations
    if result["handoff_count"] > 0:
        result["recommendations"].append(
            f"Continue {result['handoff_count']} handoff items from {intent_data['session_id']}"
        )
        # Include first handoff item as hint
        if intent_data.get("handoff_items"):
            result["first_handoff"] = intent_data["handoff_items"][0]

    if result["discovery_count"] > 0:
        result["recommendations"].append(
            f"Review {result['discovery_count']} discoveries"
        )

    # Check for incomplete work
    outcome_status = intent_data.get("outcome", {}).get("status", "")
    if outcome_status == "PARTIAL":
        result["recommendations"].append("Previous session was PARTIAL - check deferred tasks")
    elif outcome_status == "DEFERRED":
        result["recommendations"].append("Previous session was DEFERRED - work needs continuation")

    return result


def format_intent_for_healthcheck(intent_data: Dict) -> List[str]:
    """
    Format intent data for healthcheck output display.

    Args:
        intent_data: Result from check_intent_continuity()

    Returns:
        List of lines to add to healthcheck output
    """
    lines = []

    if not intent_data.get("has_previous"):
        return lines  # No previous session, skip section

    prev = intent_data.get("previous_session", {})

    lines.append("")
    lines.append("Session Continuity:")
    lines.append(f"  Previous: {prev.get('id', 'Unknown')}")
    lines.append(f"  Goal: {prev.get('goal', 'Unknown')[:60]}...")
    lines.append(f"  Status: {prev.get('status', 'Unknown')}")

    if intent_data.get("handoff_count", 0) > 0:
        lines.append(f"  Handoffs: {intent_data['handoff_count']} items pending")
        if intent_data.get("first_handoff"):
            lines.append(f"  Next: {intent_data['first_handoff'][:50]}...")

    if intent_data.get("recommendations"):
        lines.append("")
        lines.append("Continuity Actions:")
        for rec in intent_data["recommendations"][:3]:  # Max 3 recommendations
            lines.append(f"  - {rec}")

    return lines


# Convenience function for healthcheck.py import
def get_intent_status(evidence_dir: Path = None) -> Dict[str, Any]:
    """
    Quick intent status check for healthcheck integration.

    Returns minimal dict with:
    - has_continuity: bool
    - summary: str (one-liner for compact output)
    - lines: List[str] (for detailed output)
    """
    intent_data = check_intent_continuity(evidence_dir)

    # Build summary line
    if not intent_data.get("has_previous"):
        summary = "No previous session"
    else:
        prev = intent_data.get("previous_session", {})
        status = prev.get("status", "?")
        handoffs = intent_data.get("handoff_count", 0)
        summary = f"Prev: {status}, {handoffs} handoffs"

    return {
        "has_continuity": intent_data.get("has_previous", False),
        "summary": summary,
        "lines": format_intent_for_healthcheck(intent_data),
        "raw": intent_data
    }


def reconcile_intent(
    current_tasks: List[str],
    previous_handoffs: List[str],
    backlog_items: List[str] = None
) -> Dict[str, Any]:
    """
    Compare current session intent against previous handoffs to detect AMNESIA.

    Per RD-INTENT Phase 4: AMNESIA Detection Algorithm

    Args:
        current_tasks: Tasks planned for current session (from todo list)
        previous_handoffs: Handoff items from previous session
        backlog_items: Known backlog items (optional, for alignment check)

    Returns:
        Dict with:
            status: "ALIGNED" | "DRIFT" | "AMNESIA"
            alignment_score: 0.0 - 1.0
            missing_handoffs: List of forgotten handoff items
            unexpected_work: List of work not from handoffs or backlog
    """
    if backlog_items is None:
        backlog_items = []

    # Normalize for comparison (lowercase, strip)
    def normalize(items):
        return [str(i).lower().strip() for i in items if i]

    current_normalized = normalize(current_tasks)
    handoffs_normalized = normalize(previous_handoffs)
    backlog_normalized = normalize(backlog_items)

    # Check which handoffs are missing from current plan
    missing_handoffs = []
    for i, handoff in enumerate(handoffs_normalized):
        # Check if any current task contains the handoff reference
        found = any(handoff in task or task in handoff for task in current_normalized)
        if not found:
            missing_handoffs.append(previous_handoffs[i])  # Original format

    # Check for unexpected work (not from handoff or backlog)
    unexpected_work = []
    valid_sources = set(handoffs_normalized + backlog_normalized)
    for i, task in enumerate(current_normalized):
        # Check if task relates to any valid source
        found = any(source in task or task in source for source in valid_sources)
        if not found and current_tasks[i]:
            unexpected_work.append(current_tasks[i])

    # Calculate alignment score
    total_expected = len(previous_handoffs)
    if total_expected == 0:
        # No handoffs = no expectations = aligned
        alignment_score = 1.0
        status = "ALIGNED"
    else:
        picked_up = total_expected - len(missing_handoffs)
        alignment_score = picked_up / total_expected

        # Determine status
        if len(missing_handoffs) > 0 and alignment_score < 0.5:
            status = "AMNESIA"  # Forgot more than half of previous work
        elif len(unexpected_work) > len(missing_handoffs):
            status = "DRIFT"  # Doing mostly unplanned work
        else:
            status = "ALIGNED"

    return {
        "status": status,
        "alignment_score": alignment_score,
        "missing_handoffs": missing_handoffs,
        "unexpected_work": unexpected_work[:5],  # Limit to avoid noise
        "handoff_count": len(previous_handoffs),
        "picked_up_count": len(previous_handoffs) - len(missing_handoffs)
    }


def detect_amnesia(evidence_dir: Path = None) -> Dict[str, Any]:
    """
    Run AMNESIA detection for current session.

    Checks if previous session had handoffs that weren't picked up.
    This is a lighter check than full reconcile_intent() since we
    don't know current session's tasks at healthcheck time.

    Returns:
        Dict with AMNESIA detection status and alert info
    """
    result = {
        "detected": False,
        "severity": "NONE",  # NONE | WARNING | ALERT
        "missing_handoffs": [],
        "previous_session": None,
        "alert_lines": []
    }

    # Get previous session data
    if evidence_dir is None:
        project_root = Path(__file__).parent.parent.parent.parent
        evidence_dir = project_root / "evidence"

    latest_file = find_latest_evidence_file(evidence_dir)
    if not latest_file:
        return result

    intent_data = extract_intent_from_evidence(latest_file)

    # Check if previous session had handoffs
    handoffs = intent_data.get("handoff_items", [])
    if not handoffs:
        return result  # No handoffs = no AMNESIA risk

    # If we have handoffs, flag as potential AMNESIA
    # The actual check requires current session tasks, which we may not have
    # So we return a WARNING level to prompt the user

    result["previous_session"] = intent_data.get("session_id", latest_file.stem)
    result["missing_handoffs"] = handoffs

    # Determine severity based on handoff count and outcome status
    outcome_status = intent_data.get("outcome", {}).get("status", "")

    if outcome_status in ["PARTIAL", "ABANDONED", "DEFERRED"]:
        result["detected"] = True
        result["severity"] = "ALERT"
    elif len(handoffs) >= 3:
        result["detected"] = True
        result["severity"] = "ALERT"
    elif len(handoffs) >= 1:
        result["detected"] = True
        result["severity"] = "WARNING"

    # Build alert lines
    if result["detected"]:
        result["alert_lines"] = format_amnesia_alert(result, intent_data)

    return result


def format_amnesia_alert(amnesia_data: Dict, intent_data: Dict) -> List[str]:
    """
    Format AMNESIA detection alert for healthcheck output.

    Per RD-INTENT Phase 4: Alert formatting
    """
    lines = []

    severity = amnesia_data.get("severity", "WARNING")
    session_id = amnesia_data.get("previous_session", "Unknown")
    handoffs = amnesia_data.get("missing_handoffs", [])

    if severity == "ALERT":
        lines.append("")
        lines.append("⚠️ INTENT CONTINUITY ALERT")
        lines.append(f"  Previous: {session_id}")
        lines.append(f"  Pending handoffs: {len(handoffs)}")
        for i, handoff in enumerate(handoffs[:3]):  # Show max 3
            truncated = handoff[:50] + "..." if len(handoff) > 50 else handoff
            lines.append(f"    {i+1}. {truncated}")
        if len(handoffs) > 3:
            lines.append(f"    ... and {len(handoffs) - 3} more")
        lines.append("")
        lines.append("  Action: Continue handoff items or mark as deferred")

    elif severity == "WARNING":
        lines.append("")
        lines.append(f"📋 Pending handoffs from {session_id}: {len(handoffs)}")
        if handoffs:
            lines.append(f"  First: {handoffs[0][:45]}...")

    return lines
