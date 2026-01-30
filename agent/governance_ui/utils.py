"""
Governance UI Utilities.

Per EPIC-DR-003: Pagination handling utilities.
Per GAP-UI-TIMESTAMP: Timestamp formatting.
"""


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


def format_timestamp(iso_str: str) -> str:
    """
    Format an ISO timestamp to human-readable format.

    Per GAP-UI-TIMESTAMP: Converts '2026-01-19T04:06:50.000000000' to '2026-01-19 04:06'.

    Args:
        iso_str: ISO format timestamp string

    Returns:
        Formatted string or original if parsing fails
    """
    if not iso_str or not isinstance(iso_str, str):
        return iso_str or ""
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
