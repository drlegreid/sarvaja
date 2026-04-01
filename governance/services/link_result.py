"""LinkResult — structured return type for all linking operations.

Per SRVJ-BUG-ERROR-OBS-01 / EPIC-TASK-WORKFLOW-HEAL-01 P3:
Replaces bare bool returns with rich context: success, reason,
already_existed, and error_code. Defined ONCE, imported everywhere (DRY).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=False)
class LinkResult:
    """Structured result from a link/unlink operation.

    Attributes:
        success: Whether the operation succeeded.
        already_existed: True if the relation already existed (idempotent).
        reason: Human-readable explanation of the outcome.
        error_code: Machine-readable code for programmatic handling.
            Known codes: NO_CLIENT, ENTITY_NOT_FOUND, EXCEPTION, LINK_FAILED.
    """

    success: bool
    already_existed: bool
    reason: str
    error_code: Optional[str] = None

    def __bool__(self) -> bool:
        """Allow `if result:` backward compatibility."""
        return self.success

    def to_mcp_response(self) -> dict:
        """Format for MCP tool return — SRP: dataclass owns its own formatting."""
        d = {
            "success": self.success,
            "already_existed": self.already_existed,
            "reason": self.reason,
        }
        if self.error_code is not None:
            d["error_code"] = self.error_code
        return d
