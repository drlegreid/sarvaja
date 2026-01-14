"""
DSM Session Memory Integration.

Per GAP-FILE-024: Extracted from dsm/tracker.py
Per DOC-SIZE-01-v1: Files under 400 lines

Provides session memory integration for DSM cycles.
Per RULE-024 (AMNESIA Protocol): Save session context for recovery.

Created: 2024-12-24
Refactored: 2026-01-14
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import asdict

if TYPE_CHECKING:
    from governance.dsm.models import DSMCycle


def get_session_memory_payload(cycle: "DSMCycle") -> Optional[Dict[str, Any]]:
    """
    Get payload for saving cycle context to claude-mem (P11.4).

    Returns dict ready for chroma_add_documents MCP call, or None if error.
    Per RULE-024 (AMNESIA Protocol): Save session context for recovery.

    Args:
        cycle: The DSM cycle to create payload for

    Returns:
        Dict with collection_name, documents, ids, metadatas - or None
    """
    if not cycle:
        return None

    try:
        from governance.session_memory import create_dsp_session_context

        # Create session context from cycle data
        ctx = create_dsp_session_context(
            cycle_id=cycle.cycle_id,
            batch_id=cycle.batch_id,
            phases_completed=cycle.phases_completed,
            findings=cycle.findings,
            checkpoints=[asdict(cp) for cp in cycle.checkpoints],
            metrics=cycle.metrics,
        )

        # Return payload for MCP call
        doc_id = f"sim-ai-dsp-{cycle.cycle_id}"
        return {
            "collection_name": "claude_memories",
            "documents": [ctx.to_document()],
            "ids": [doc_id],
            "metadatas": [ctx.to_metadata()],
        }
    except ImportError:
        return None
    except Exception:
        return None


__all__ = ["get_session_memory_payload"]
