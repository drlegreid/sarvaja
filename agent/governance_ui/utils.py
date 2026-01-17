"""
Governance UI Utilities.

Per EPIC-DR-003: Pagination handling utilities.
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
