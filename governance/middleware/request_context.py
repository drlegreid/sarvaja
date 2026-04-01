"""Thread-local request context for correlating HTTP requests to TypeDB queries.

Middleware sets the request ID on entry; TypeDB base reads it in slow-query logs.
This enables end-to-end tracing: HTTP request → rid in access log → rid in TypeDB log.

Created: 2026-03-26  EPIC-PERF-TELEM-V1 Phase 6
"""
import threading
from typing import Optional

_local = threading.local()


def set_request_id(rid: Optional[str]) -> None:
    """Store request ID in thread-local context."""
    _local.request_id = rid


def get_request_id() -> Optional[str]:
    """Retrieve request ID from thread-local context, or None."""
    return getattr(_local, "request_id", None)
