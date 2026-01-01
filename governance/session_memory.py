"""
Session Memory Integration - P11.4
Auto-save session context to claude-mem at DSP completion.
Load context at session start (RULE-024: AMNESIA Protocol).

Created: 2024-12-26
Per: GAP-ARCH-011, GAP-PROC-001, RULE-024
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# Import claude-mem MCP tools (available via MCP protocol)
# These are called via MCP client, not direct import


@dataclass
class SessionContext:
    """Context to save/load from claude-mem."""
    session_id: str
    project: str = "sim-ai"
    date: str = None
    phase: str = None
    tasks_completed: List[str] = None
    tasks_in_progress: List[str] = None
    gaps_discovered: List[str] = None
    gaps_resolved: List[str] = None
    decisions_made: List[str] = None
    key_files_modified: List[str] = None
    test_results: Dict[str, int] = None
    summary: str = None
    next_steps: List[str] = None

    def __post_init__(self):
        if self.date is None:
            self.date = date.today().isoformat()
        if self.tasks_completed is None:
            self.tasks_completed = []
        if self.tasks_in_progress is None:
            self.tasks_in_progress = []
        if self.gaps_discovered is None:
            self.gaps_discovered = []
        if self.gaps_resolved is None:
            self.gaps_resolved = []
        if self.decisions_made is None:
            self.decisions_made = []
        if self.key_files_modified is None:
            self.key_files_modified = []
        if self.test_results is None:
            self.test_results = {}
        if self.next_steps is None:
            self.next_steps = []

    def to_document(self) -> str:
        """Convert to document string for claude-mem storage."""
        lines = [
            f"sim-ai Session {self.session_id} ({self.date})",
            f"Phase: {self.phase or 'N/A'}",
            "",
        ]

        if self.summary:
            lines.extend([self.summary, ""])

        if self.tasks_completed:
            lines.append(f"Tasks Completed: {', '.join(self.tasks_completed)}")

        if self.tasks_in_progress:
            lines.append(f"Tasks In Progress: {', '.join(self.tasks_in_progress)}")

        if self.gaps_resolved:
            lines.append(f"Gaps Resolved: {', '.join(self.gaps_resolved)}")

        if self.gaps_discovered:
            lines.append(f"Gaps Discovered: {', '.join(self.gaps_discovered)}")

        if self.decisions_made:
            lines.append(f"Decisions: {', '.join(self.decisions_made)}")

        if self.key_files_modified:
            lines.append(f"Files Modified: {', '.join(self.key_files_modified[:10])}")

        if self.test_results:
            lines.append(f"Tests: {self.test_results.get('passed', 0)} passed, {self.test_results.get('failed', 0)} failed")

        if self.next_steps:
            lines.append(f"Next Steps: {'; '.join(self.next_steps[:5])}")

        return "\n".join(lines)

    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for claude-mem."""
        return {
            "project": self.project,
            "session_id": self.session_id,
            "date": self.date,
            "phase": self.phase or "unknown",
            "type": "session-context",
            "tasks_count": len(self.tasks_completed),
            "gaps_resolved_count": len(self.gaps_resolved),
        }


class SessionMemoryManager:
    """
    Manages session context save/load with claude-mem.

    Usage:
        manager = SessionMemoryManager()

        # At session start (RULE-024 AMNESIA recovery)
        context = await manager.recover_context()

        # During session - track progress
        manager.track_task_completed("P11.3")
        manager.track_gap_resolved("GAP-DATA-002")

        # At DSP cycle end - save context
        await manager.save_context()
    """

    COLLECTION = "claude_memories"

    def __init__(self, project: str = "sim-ai"):
        self.project = project
        self.current_context: Optional[SessionContext] = None
        self._init_context()

    def _init_context(self) -> None:
        """Initialize a new session context."""
        session_id = f"SESSION-{date.today().isoformat()}-{datetime.now().strftime('%H%M%S')}"
        self.current_context = SessionContext(
            session_id=session_id,
            project=self.project,
        )

    def set_phase(self, phase: str) -> None:
        """Set current phase."""
        if self.current_context:
            self.current_context.phase = phase

    def track_task_completed(self, task_id: str) -> None:
        """Track a completed task."""
        if self.current_context and task_id not in self.current_context.tasks_completed:
            self.current_context.tasks_completed.append(task_id)

    def track_task_in_progress(self, task_id: str) -> None:
        """Track a task in progress."""
        if self.current_context and task_id not in self.current_context.tasks_in_progress:
            self.current_context.tasks_in_progress.append(task_id)

    def track_gap_resolved(self, gap_id: str) -> None:
        """Track a resolved gap."""
        if self.current_context and gap_id not in self.current_context.gaps_resolved:
            self.current_context.gaps_resolved.append(gap_id)

    def track_gap_discovered(self, gap_id: str) -> None:
        """Track a discovered gap."""
        if self.current_context and gap_id not in self.current_context.gaps_discovered:
            self.current_context.gaps_discovered.append(gap_id)

    def track_decision(self, decision: str) -> None:
        """Track a decision made."""
        if self.current_context and decision not in self.current_context.decisions_made:
            self.current_context.decisions_made.append(decision)

    def track_file_modified(self, file_path: str) -> None:
        """Track a modified file."""
        if self.current_context and file_path not in self.current_context.key_files_modified:
            self.current_context.key_files_modified.append(file_path)

    def set_test_results(self, passed: int, failed: int, skipped: int = 0) -> None:
        """Set test results."""
        if self.current_context:
            self.current_context.test_results = {
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
            }

    def set_summary(self, summary: str) -> None:
        """Set session summary."""
        if self.current_context:
            self.current_context.summary = summary

    def add_next_step(self, step: str) -> None:
        """Add a next step."""
        if self.current_context and step not in self.current_context.next_steps:
            self.current_context.next_steps.append(step)

    def get_save_payload(self) -> Dict[str, Any]:
        """
        Get payload for saving to claude-mem.

        Returns dict ready for chroma_add_documents MCP call.
        """
        if not self.current_context:
            self._init_context()

        doc_id = f"{self.project}-session-{self.current_context.session_id}"

        return {
            "collection_name": self.COLLECTION,
            "documents": [self.current_context.to_document()],
            "ids": [doc_id],
            "metadatas": [self.current_context.to_metadata()],
        }

    def get_recovery_query(self) -> Dict[str, Any]:
        """
        Get query for context recovery from claude-mem.

        Returns dict ready for chroma_query_documents MCP call.
        Per RULE-024: Always include project name in query.
        """
        today = date.today().isoformat()

        return {
            "collection_name": self.COLLECTION,
            "query_texts": [f"{self.project} session {today} phase work tasks"],
            "n_results": 5,
        }

    def parse_recovery_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse claude-mem query results into recovered context.

        Args:
            results: Raw results from chroma_query_documents

        Returns:
            Parsed context dict for session resumption
        """
        recovered = {
            "found": False,
            "sessions": [],
            "recent_tasks": [],
            "recent_gaps": [],
            "last_phase": None,
            "summary": None,
        }

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return recovered

        recovered["found"] = True

        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}

            session_info = {
                "content": doc[:500],  # First 500 chars
                "date": metadata.get("date"),
                "phase": metadata.get("phase"),
                "type": metadata.get("type"),
            }
            recovered["sessions"].append(session_info)

            # Extract last phase from most recent
            if i == 0 and metadata.get("phase"):
                recovered["last_phase"] = metadata.get("phase")

            # Extract summary from first doc
            if i == 0:
                recovered["summary"] = doc[:1000]

        return recovered

    def generate_amnesia_report(self, recovered: Dict[str, Any]) -> str:
        """
        Generate AMNESIA recovery report per RULE-024.

        Args:
            recovered: Parsed recovery results

        Returns:
            Human-readable recovery report
        """
        lines = [
            "## AMNESIA Recovery Report (RULE-024)",
            "",
        ]

        if not recovered.get("found"):
            lines.extend([
                "**Status:** No recent session context found in claude-mem.",
                "",
                "**Recommended Recovery:**",
                "1. Read TODO.md for active tasks",
                "2. Read R&D-BACKLOG.md for phase status",
                "3. Check GAP-INDEX.md for open gaps",
                "",
            ])
        else:
            lines.extend([
                f"**Status:** Found {len(recovered.get('sessions', []))} recent sessions.",
                "",
            ])

            if recovered.get("last_phase"):
                lines.append(f"**Last Phase:** {recovered['last_phase']}")

            if recovered.get("summary"):
                lines.extend([
                    "",
                    "**Most Recent Context:**",
                    "```",
                    recovered["summary"][:500],
                    "```",
                    "",
                ])

            lines.extend([
                "**Next Steps:**",
                "1. Review recovered context above",
                "2. Continue from last task",
                "3. Check TODO.md for updates",
                "",
            ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dict."""
        return {
            "project": self.project,
            "current_context": asdict(self.current_context) if self.current_context else None,
            "collection": self.COLLECTION,
        }


# Integration with DSM Tracker
def create_dsp_session_context(
    cycle_id: str,
    batch_id: str,
    phases_completed: List[str],
    findings: List[Dict[str, Any]],
    checkpoints: List[Dict[str, Any]],
    metrics: Dict[str, Any],
) -> SessionContext:
    """
    Create SessionContext from DSM cycle data.

    Called at DSP cycle completion to save context to claude-mem.
    """
    context = SessionContext(
        session_id=cycle_id,
        project="sim-ai",
        phase=f"DSP-{batch_id}" if batch_id else "DSP",
    )

    # Extract tasks from findings
    for finding in findings:
        if finding.get("type") == "task_completed":
            context.tasks_completed.append(finding.get("description", "")[:50])
        elif finding.get("type") == "gap":
            context.gaps_discovered.append(finding.get("id", ""))

    # Extract from metrics
    if metrics.get("gaps_resolved"):
        context.gaps_resolved = metrics["gaps_resolved"]
    if metrics.get("tests_passed") is not None:
        context.test_results = {
            "passed": metrics.get("tests_passed", 0),
            "failed": metrics.get("tests_failed", 0),
            "skipped": metrics.get("tests_skipped", 0),
        }

    # Generate summary from checkpoints
    if checkpoints:
        checkpoint_summaries = [cp.get("description", "") for cp in checkpoints[-3:]]
        context.summary = "; ".join(checkpoint_summaries)

    return context


# Global manager instance
_manager: Optional[SessionMemoryManager] = None


def get_session_memory() -> SessionMemoryManager:
    """Get or create global session memory manager."""
    global _manager
    if _manager is None:
        _manager = SessionMemoryManager()
    return _manager


def reset_session_memory() -> None:
    """Reset global manager (for testing)."""
    global _manager
    _manager = None
