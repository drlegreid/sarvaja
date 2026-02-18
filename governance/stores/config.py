"""
Governance Stores - TypeDB Configuration.

Per RULE-032: Modularized from stores.py (503 lines).
Contains: TypeDB configuration and client access.
"""

import os
import logging

from governance.client import get_client

logger = logging.getLogger(__name__)

# TypeDB toggle
USE_TYPEDB = os.getenv("USE_TYPEDB", "true").lower() == "true"


def get_typedb_client():
    """Get TypeDB client with connection check."""
    if not USE_TYPEDB:
        return None
    try:
        client = get_client()
        if client and client.is_connected():
            return client
    except Exception as e:
        # BUG-473-CFG-1: Sanitize logger message + add exc_info for stack trace preservation
        logger.warning(f"TypeDB connection failed: {type(e).__name__}", exc_info=True)
    return None
