"""
Holographic Test Evidence Store - Multi-resolution test evidence access.
Per EPIC-TEST-COMPRESS-001 + FH-001. Zoom levels: 0=oneline, 1=compact, 2=list, 3=full.
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from threading import Lock

from tests.evidence.summary_compressor import SummaryCompressor, CompressedTestSummary


@dataclass
class EvidenceRecord:
    """Full test evidence record with all detail levels."""

    # Level 0-1: Summary fields
    test_id: str
    name: str
    status: str
    category: str = "unknown"
    duration_ms: float = 0.0

    # Level 2: Extended metadata
    intent: Optional[str] = None
    linked_rules: List[str] = field(default_factory=list)
    linked_gaps: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    # Level 3: Full fixtures (request/response data)
    fixtures: Dict[str, Any] = field(default_factory=dict)
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    evidence_hash: Optional[str] = None

    def __post_init__(self):
        """Compute evidence hash for integrity."""
        if not self.evidence_hash:
            content = f"{self.test_id}:{self.status}:{self.timestamp}"
            self.evidence_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_summary_dict(self) -> Dict[str, Any]:
        """Level 1-2: Return summary fields only."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "status": self.status,
            "category": self.category,
            "duration_ms": self.duration_ms,
            "error": self.error_message,
            "linked_rules": self.linked_rules,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Level 3: Return all fields including fixtures."""
        return asdict(self)


class HolographicTestStore:
    """
    Multi-resolution test evidence store.

    Implements the holographic principle: full detail stored,
    queryable at any zoom level.
    """

    def __init__(self, session_id: Optional[str] = None, persist_path: Optional[Path] = None):
        """Initialize store with optional session ID and persistence path."""
        self.session_id = session_id or f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.persist_path = persist_path
        self._events: List[EvidenceRecord] = []
        self._lock = Lock()
        self._compressor = SummaryCompressor()

    def push_event(self, test_id: str, name: str, status: str, category: str = "unknown",
                   duration_ms: float = 0.0, intent: Optional[str] = None,
                   linked_rules: Optional[List[str]] = None, linked_gaps: Optional[List[str]] = None,
                   error_message: Optional[str] = None, fixtures: Optional[Dict[str, Any]] = None,
                   request_data: Optional[Dict[str, Any]] = None,
                   response_data: Optional[Dict[str, Any]] = None) -> str:
        """Push test event to store (thread-safe). Returns evidence_hash."""
        evidence = EvidenceRecord(
            test_id=test_id, name=name, status=status, category=category, duration_ms=duration_ms,
            intent=intent, linked_rules=linked_rules or [], linked_gaps=linked_gaps or [],
            error_message=error_message, fixtures=fixtures or {},
            request_data=request_data, response_data=response_data, session_id=self.session_id)
        with self._lock:
            self._events.append(evidence)
            if self.persist_path:
                self._persist()
        return evidence.evidence_hash

    def query(self, zoom: int = 1, test_id: Optional[str] = None, category: Optional[str] = None,
               status: Optional[str] = None, format: str = "dict") -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        """Query evidence at zoom level: 0=oneline, 1=compact, 2=list, 3=full."""
        with self._lock:
            events = self._filter_events(test_id, category, status)
        zoom_funcs = {0: self._zoom_0_oneline, 1: self._zoom_1_compact,
                      2: self._zoom_2_list, 3: lambda e, f: self._zoom_3_full(e, test_id, f)}
        if zoom not in zoom_funcs:
            raise ValueError(f"Invalid zoom level: {zoom}. Use 0-3.")
        return zoom_funcs[zoom](events, format)

    def _filter_events(self, test_id: Optional[str], category: Optional[str],
                       status: Optional[str]) -> List[EvidenceRecord]:
        """Filter events by criteria."""
        events = self._events
        if test_id:
            events = [e for e in events if test_id in e.test_id]
        if category:
            events = [e for e in events if e.category == category]
        if status:
            events = [e for e in events if e.status.lower() == status.lower()]
        return events

    def _zoom_0_oneline(self, events: List[EvidenceRecord], format: str) -> Union[str, Dict]:
        """Zoom 0: One-line summary."""
        summary = self._compressor.compress_test_list([e.to_summary_dict() for e in events])
        if format == "text":
            return summary.format_oneline()
        return {"zoom": 0, "summary": summary.format_oneline(),
                "total": summary.total, "passed": summary.passed, "failed": summary.failed}

    def _zoom_1_compact(self, events: List[EvidenceRecord], format: str) -> Union[str, Dict]:
        """Zoom 1: Compact summary with failures."""
        summary = self._compressor.compress_test_list([e.to_summary_dict() for e in events])

        if format == "text":
            return summary.format_compact()
        return {
            "zoom": 1,
            "summary": summary.format_compact(),
            "stats": {
                "total": summary.total,
                "passed": summary.passed,
                "failed": summary.failed,
                "skipped": summary.skipped,
            },
            "failures": summary.failures,
            "compression": summary.compression_ratio,
        }

    def _zoom_2_list(self, events: List[EvidenceRecord], format: str) -> Union[str, List[Dict]]:
        """Zoom 2: Per-test summary list."""
        items = [e.to_summary_dict() for e in events]

        if format == "text":
            lines = [f"{e['status'].upper():8} {e['test_id']} ({e['duration_ms']:.0f}ms)" for e in items]
            return "\n".join(lines)
        return {
            "zoom": 2,
            "count": len(items),
            "tests": items,
        }

    def _zoom_3_full(
        self,
        events: List[EvidenceRecord],
        test_id: Optional[str],
        format: str,
    ) -> Union[str, Dict, List[Dict]]:
        """Zoom 3: Full detail with fixtures."""
        if test_id and len(events) == 1:
            # Single test detail
            full = events[0].to_full_dict()
            if format == "json":
                return json.dumps(full, indent=2, default=str)
            return {"zoom": 3, "evidence": full}

        # Multiple tests
        items = [e.to_full_dict() for e in events]
        if format == "json":
            return json.dumps(items, indent=2, default=str)
        return {
            "zoom": 3,
            "count": len(items),
            "evidence": items,
        }

    def get_by_hash(self, evidence_hash: str) -> Optional[EvidenceRecord]:
        """Get specific evidence by hash."""
        with self._lock:
            for e in self._events:
                if e.evidence_hash == evidence_hash:
                    return e
        return None

    def clear(self) -> int:
        """Clear all events. Returns count cleared."""
        with self._lock:
            count = len(self._events)
            self._events = []
        return count

    def _persist(self) -> None:
        """Persist events to file."""
        if not self.persist_path:
            return

        data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "events": [asdict(e) for e in self._events],
        }

        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.persist_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, path: Path) -> int:
        """Load events from persisted file. Returns count loaded."""
        if not path.exists():
            return 0

        with open(path) as f:
            data = json.load(f)

        count = 0
        for e in data.get("events", []):
            self._events.append(EvidenceRecord(**e))
            count += 1

        return count

    @property
    def count(self) -> int:
        """Total event count."""
        return len(self._events)

    def __len__(self) -> int:
        return self.count


# Global store instance for pytest integration
_global_store: Optional[HolographicTestStore] = None


def get_global_store(session_id: Optional[str] = None) -> HolographicTestStore:
    """Get or create global holographic store."""
    global _global_store
    if _global_store is None:
        _global_store = HolographicTestStore(session_id=session_id)
    return _global_store


def reset_global_store() -> None:
    """Reset global store (for testing)."""
    global _global_store
    _global_store = None
