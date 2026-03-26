"""
Rules Sync Verification Route.

Per EPIC-GOV-RULES-V3 P8: GET /api/rules/sync/verify endpoint.
SRP: Sync verification separate from rule CRUD and compliance routes.

Created: 2026-03-26
"""

import logging
from fastapi import APIRouter

from governance.services.rules_sync import SyncVerifier

router = APIRouter(tags=["Rules Sync"])
logger = logging.getLogger(__name__)


@router.get("/rules/sync/verify")
async def sync_verify():
    """
    Verify sync between TypeDB rules, leaf markdown files, and RULES-*.md indexes.

    Returns a SyncReport with discrepancies:
      - typedb_only: rules in TypeDB but missing leaf file
      - leaf_only: leaf files with no TypeDB entry
      - index_gaps: known rules missing from RULES-*.md indexes
      - synced: True if all 3 sources are fully aligned
    """
    try:
        verifier = SyncVerifier()
        report = verifier.verify()
        return report.to_dict()
    except Exception as e:
        logger.error("sync_verify failed: %s", type(e).__name__, exc_info=True)
        return {"error": f"sync_verify failed: {type(e).__name__}", "synced": False}
