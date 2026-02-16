"""
Governance UI Utilities.

Per EPIC-DR-003: Pagination handling utilities.
Per GAP-UI-TIMESTAMP: Timestamp formatting.
Per GAP-SESSION-STATS-001: Session metrics computation.
"""

from datetime import datetime


def extract_items_from_response(data):
    """
    Extract items array from API response.

    Handles both paginated (EPIC-DR-003) and legacy array responses.

    Args:
        data: Response data (dict with items/pagination or list)

    Returns:
        list: Items array
    """
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data if isinstance(data, list) else []


def extract_pagination_from_response(data):
    """
    Extract pagination metadata from API response.

    Args:
        data: Response data (dict with items/pagination)

    Returns:
        dict: Pagination metadata or empty dict
    """
    if isinstance(data, dict) and "pagination" in data:
        return data["pagination"]
    return {}


def compute_session_metrics(sessions: list) -> dict:
    """
    Compute session summary metrics from raw session data.

    Per GAP-SESSION-STATS-001: Must be called BEFORE format_timestamps_in_list
    because formatting strips the T separator and seconds needed for parsing.

    Args:
        sessions: List of session dicts with raw ISO timestamps

    Returns:
        dict with 'duration' (str like '312h' or '45m') and 'avg_tasks' (float)
    """
    total_hours = 0
    total_tasks = 0

    for s in sessions:
        start = s.get("start_time", "")
        end = s.get("end_time", "")
        if start and end:
            try:
                st = start[:19].replace("Z", "")
                et = end[:19].replace("Z", "")
                if _is_estimated_duration(st, et):
                    continue  # Skip repair-generated artificial timestamps
                delta = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S") - datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
                hours = delta.total_seconds() / 3600
                if 0 < hours <= 24:
                    total_hours += hours
            except Exception:
                pass
        tasks = s.get("tasks_completed", 0)
        if isinstance(tasks, (int, float)):
            total_tasks += tasks

    if total_hours >= 1:
        duration = f"{total_hours:.0f}h"
    elif total_hours > 0:
        duration = f"{total_hours * 60:.0f}m"
    else:
        duration = "0h"

    session_count = len(sessions) or 1
    avg_tasks = round(total_tasks / session_count, 1)

    return {"duration": duration, "avg_tasks": avg_tasks}


def _is_estimated_duration(start: str, end: str) -> bool:
    """Detect repair-generated artificial timestamps.

    Sessions repaired by session_repair.generate_timestamps() always have
    start at T09:00:00 and end at T13:00:00 (4h default duration).
    These are estimates, not real session durations.
    """
    try:
        return "T09:00:00" in start and "T13:00:00" in end
    except (TypeError, AttributeError):
        return False


def compute_session_duration(start: str, end: str) -> str:
    """Compute human-readable duration between two ISO timestamps.

    Per F.2: Duration column in hours for session list view.

    Returns:
        "Xh Ym" format, "ongoing" for ACTIVE sessions, or "" if invalid.
        Repair artifacts show "~4h (est)" suffix.
    """
    if not start:
        return ""
    if not end:
        return "ongoing"
    try:
        st = start[:19].replace("Z", "")
        et = end[:19].replace("Z", "")
        delta = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S") - datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
        total_seconds = delta.total_seconds()
        if total_seconds < 0:
            total_seconds = abs(total_seconds)
        total_minutes = int(total_seconds / 60)
        if total_minutes > 1440:  # >24h — likely repair artifact
            return ">24h"
        # Detect repair-generated artificial timestamps
        if _is_estimated_duration(st, et):
            return "~4h (est)"
        if total_minutes < 1:
            return "<1m"
        hours, mins = divmod(total_minutes, 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    except Exception:
        return ""


def compute_timeline_data(sessions: list) -> tuple:
    """Compute daily session counts for timeline histogram.

    Per F.3: Timeline histogram grouped by date.

    Returns:
        (values, labels) - lists of counts and date labels for last 14 days.
    """
    from collections import Counter
    date_counts = Counter()
    for s in sessions:
        start = s.get("start_time", "")
        if start:
            try:
                date_str = start[:10]
                date_counts[date_str] += 1
            except Exception:
                pass
    # Get last 14 days
    today = datetime.now()
    labels = []
    values = []
    for i in range(13, -1, -1):
        from datetime import timedelta
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(d[5:])  # MM-DD format
        values.append(date_counts.get(d, 0))
    return values, labels


def compute_pivot_data(sessions: list, group_by: str = "agent_id") -> list:
    """Compute pivot aggregations from sessions.

    Per F.4: Pivot table view grouped by agent or status.

    Returns:
        List of dicts with group_key, count, avg_duration_mins, completed, active.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for s in sessions:
        key = s.get(group_by) or "(none)"
        groups[key].append(s)

    result = []
    for key, items in sorted(groups.items()):
        completed = sum(1 for s in items if s.get("status") == "COMPLETED")
        active = sum(1 for s in items if s.get("status") == "ACTIVE")
        durations = []
        for s in items:
            start = s.get("start_time", "")
            end = s.get("end_time", "")
            if start and end:
                try:
                    st = start[:19].replace("Z", "")
                    et = end[:19].replace("Z", "")
                    if _is_estimated_duration(st, et):
                        continue  # Skip repair-generated artificial timestamps
                    delta = datetime.strptime(et, "%Y-%m-%dT%H:%M:%S") - datetime.strptime(st, "%Y-%m-%dT%H:%M:%S")
                    mins = delta.total_seconds() / 60
                    if 0 < mins <= 1440:  # skip negative + >24h
                        durations.append(mins)
                except Exception:
                    pass
        avg_dur = round(sum(durations) / len(durations), 1) if durations else 0
        result.append({
            "group": key,
            "count": len(items),
            "completed": completed,
            "active": active,
            "avg_duration": f"{int(avg_dur // 60)}h {int(avg_dur % 60)}m" if avg_dur >= 60 else f"{int(avg_dur)}m",
        })
    return result


def format_timestamp(iso_str: str) -> str:
    """
    Format an ISO timestamp to human-readable format.

    Per GAP-UI-TIMESTAMP: Converts '2026-01-19T04:06:50.000000000' to '2026-01-19 04:06'.

    Args:
        iso_str: ISO format timestamp string

    Returns:
        Formatted string or original if parsing fails
    """
    # BUG-UI-FORMAT-001: Ensure return type is always string
    if not iso_str or not isinstance(iso_str, str):
        return ""
    try:
        # Strip nanoseconds TypeDB adds (beyond microseconds)
        clean = iso_str.split(".")[0] if "." in iso_str else iso_str.replace("Z", "")
        # Return YYYY-MM-DD HH:MM format
        if "T" in clean:
            return clean.replace("T", " ")[:16]
        return clean[:16]
    except Exception:
        return iso_str


def format_timestamps_in_list(items: list, fields: list) -> list:
    """
    Format timestamp fields in a list of dicts.

    Args:
        items: List of dicts
        fields: Field names to format

    Returns:
        Same list with formatted timestamp fields
    """
    for item in items:
        for field in fields:
            if field in item and item[field]:
                item[field] = format_timestamp(item[field])
    return items
