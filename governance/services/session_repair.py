"""
Session Data Repair Service.

Fixes data quality issues in backfilled sessions:
- GAP-GOVSESS-TIMESTAMP-001: Identical artificial timestamps
- GAP-GOVSESS-AGENT-001: Missing agent_id on backfilled sessions
- GAP-GOVSESS-DURATION-001: Unrealistic session durations

Created: 2026-02-11
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from collections import Counter

logger = logging.getLogger(__name__)

# Default session duration for backfilled sessions (hours)
_DEFAULT_DURATION_HOURS = 4
_MAX_DURATION_HOURS = 24
_SESSION_DATE_PATTERN = re.compile(r"SESSION-(\d{4}-\d{2}-\d{2})")


def parse_session_date(session_id: str) -> Optional[str]:
    """Extract YYYY-MM-DD date from session ID.

    Supports formats:
    - SESSION-2026-01-15-TOPIC
    - SESSION-2024-12-26-001
    """
    match = _SESSION_DATE_PATTERN.search(session_id)
    return match.group(1) if match else None


def generate_timestamps(date_str: str) -> Tuple[str, str]:
    """Generate reasonable start/end timestamps from a date string.

    Assumes a working session: starts at 09:00, duration = _DEFAULT_DURATION_HOURS.

    Returns:
        (start_iso, end_iso)
    """
    base = datetime.fromisoformat(f"{date_str}T09:00:00")
    end = base + timedelta(hours=_DEFAULT_DURATION_HOURS)
    return base.isoformat(), end.isoformat()


def detect_identical_timestamps(sessions: List[Dict]) -> List[str]:
    """Find sessions that share identical start+end timestamp pairs.

    Sessions with the same (start, end) pair indicate bulk backfill artifacts.

    Returns:
        List of session_ids with duplicated timestamp pairs.
    """
    pairs = Counter()
    session_pairs = {}
    for s in sessions:
        start = s.get("start_time", "")
        end = s.get("end_time", "")
        if start and end:
            pair = (start, end)
            pairs[pair] += 1
            session_pairs.setdefault(pair, []).append(s["session_id"])

    flagged = []
    for pair, count in pairs.items():
        if count > 1:
            flagged.extend(session_pairs[pair])
    return flagged


def detect_missing_agent(sessions: List[Dict]) -> List[str]:
    """Find sessions without a valid agent_id.

    Returns:
        List of session_ids missing agent_id.
    """
    return [
        s["session_id"] for s in sessions
        if not s.get("agent_id")
    ]


def assign_default_agent(session: Dict) -> Dict:
    """Assign default agent_id to a session if missing.

    Only assigns if agent_id is None or empty string.
    """
    if not session.get("agent_id"):
        session = dict(session)
        session["agent_id"] = "code-agent"
    return session


def detect_negative_durations(sessions: List[Dict]) -> List[str]:
    """Find sessions where end_time is before start_time.

    Returns:
        List of session_ids with negative durations.
    """
    flagged = []
    for s in sessions:
        start = s.get("start_time", "")
        end = s.get("end_time", "")
        if start and end:
            try:
                st = datetime.fromisoformat(start[:19])
                et = datetime.fromisoformat(end[:19])
                if (et - st).total_seconds() < 0:
                    flagged.append(s["session_id"])
            except (ValueError, TypeError):
                pass
    return flagged


def detect_unrealistic_durations(
    sessions: List[Dict], max_hours: float = _MAX_DURATION_HOURS
) -> List[str]:
    """Find sessions with durations exceeding max_hours.

    Returns:
        List of session_ids with unrealistic durations.
    """
    flagged = []
    for s in sessions:
        start = s.get("start_time", "")
        end = s.get("end_time", "")
        if start and end:
            try:
                st = datetime.fromisoformat(start[:19])
                et = datetime.fromisoformat(end[:19])
                hours = (et - st).total_seconds() / 3600
                if hours > max_hours:
                    flagged.append(s["session_id"])
            except (ValueError, TypeError):
                pass
    return flagged


def cap_duration(session: Dict, max_hours: float = 8) -> Dict:
    """Cap session duration to max_hours from start_time.

    If duration <= max_hours, returns session unchanged.
    """
    start = session.get("start_time", "")
    end = session.get("end_time", "")
    if not start or not end:
        return session
    try:
        st = datetime.fromisoformat(start[:19])
        et = datetime.fromisoformat(end[:19])
        hours = (et - st).total_seconds() / 3600
        if hours > max_hours:
            session = dict(session)
            session["end_time"] = (st + timedelta(hours=max_hours)).isoformat()
    except (ValueError, TypeError):
        pass
    return session


def is_backfilled_session(session: Dict) -> bool:
    """Detect if a session is a backfill artifact.

    Indicators:
    - description contains "Backfilled from evidence"
    - agent_id ends with "-test"
    """
    desc = (session.get("description") or "").lower()
    agent = session.get("agent_id") or ""

    if "backfilled from evidence" in desc:
        return True
    if agent.endswith("-test"):
        return True
    return False


def build_repair_plan(sessions: List[Dict]) -> List[Dict]:
    """Build a repair plan for sessions with data quality issues.

    Analyzes each session and produces a list of repair items with
    specific fixes to apply.

    Returns:
        List of dicts with session_id and fixes to apply.
    """
    identical = set(detect_identical_timestamps(sessions))
    negative = set(detect_negative_durations(sessions))
    plan = []

    for s in sessions:
        sid = s["session_id"]
        fixes = {}

        # Check timestamps
        if sid in identical or is_backfilled_session(s):
            parsed_date = parse_session_date(sid)
            if parsed_date:
                start, end = generate_timestamps(parsed_date)
                fixes["timestamp"] = {"start": start, "end": end}

        # Check negative duration (end before start)
        if sid in negative and "timestamp" not in fixes:
            # Try swapping start/end
            start_t = s.get("start_time", "")
            end_t = s.get("end_time", "")
            try:
                st = datetime.fromisoformat(start_t[:19])
                et = datetime.fromisoformat(end_t[:19])
                swapped_hours = (st - et).total_seconds() / 3600
                if 0 < swapped_hours <= _MAX_DURATION_HOURS:
                    # Swap produces reasonable duration
                    fixes["timestamp"] = {"start": end_t, "end": start_t}
                else:
                    # Swap still unreasonable, regenerate from ID date
                    parsed_date = parse_session_date(sid)
                    if parsed_date:
                        start, end = generate_timestamps(parsed_date)
                        fixes["timestamp"] = {"start": start, "end": end}
            except (ValueError, TypeError):
                pass

        # Check agent_id
        if not s.get("agent_id"):
            fixes["agent_id"] = "code-agent"

        # Check duration (>24h)
        start_t = s.get("start_time", "")
        end_t = s.get("end_time", "")
        if start_t and end_t and "timestamp" not in fixes:
            try:
                st = datetime.fromisoformat(start_t[:19])
                et = datetime.fromisoformat(end_t[:19])
                hours = (et - st).total_seconds() / 3600
                if hours > _MAX_DURATION_HOURS:
                    capped = cap_duration(s)
                    fixes["duration"] = {"end_time": capped["end_time"]}
            except (ValueError, TypeError):
                pass

        if fixes:
            plan.append({"session_id": sid, "fixes": fixes})

    return plan


def apply_repair(plan_item: Dict, dry_run: bool = True) -> Dict[str, Any]:
    """Apply a single repair plan item.

    Args:
        plan_item: Dict with session_id and fixes
        dry_run: If True, don't actually update

    Returns:
        Dict with applied status and details.
    """
    from governance.services.sessions import update_session

    sid = plan_item["session_id"]
    fixes = plan_item["fixes"]

    if dry_run:
        return {"session_id": sid, "applied": False, "dry_run": True, "fixes": fixes}

    kwargs = {}
    if "agent_id" in fixes:
        kwargs["agent_id"] = fixes["agent_id"]

    update_session(sid, **kwargs)

    return {"session_id": sid, "applied": True, "fixes": fixes}
