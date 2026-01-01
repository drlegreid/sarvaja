"""
DSM Tracker - Deep Sleep Mode Cycle Tracking

Implements RULE-012 (Deep Sleep Protocol) cycle tracking with:
- Phase transitions: AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
- Evidence collection per phase
- MCP integration for phase-specific tools
- Cycle metrics and checkpoints
- Session memory integration (P11.4) for claude-mem context persistence

Created: 2024-12-24
Updated: 2024-12-26 (P11.4) - Added session memory integration
Per: RULE-012 (DSP), RULE-017 (Cross-Workspace Patterns), RULE-024 (AMNESIA Protocol)
Source: local-gai/scripts/dsm_tracker.py pattern
"""

import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class DSPPhase(Enum):
    """Deep Sleep Protocol phases per RULE-012."""
    IDLE = "idle"              # Not in a cycle
    AUDIT = "audit"            # Inventory gaps, orphans, loops
    HYPOTHESIZE = "hypothesize"  # Form improvement theories
    MEASURE = "measure"        # Quantify current state
    OPTIMIZE = "optimize"      # Apply improvements
    VALIDATE = "validate"      # Run tests
    DREAM = "dream"            # Autonomous exploration
    REPORT = "report"          # Generate evidence
    COMPLETE = "complete"      # Cycle finished

    @classmethod
    def phase_order(cls) -> List["DSPPhase"]:
        """Return phases in order (excluding IDLE and COMPLETE)."""
        return [
            cls.AUDIT,
            cls.HYPOTHESIZE,
            cls.MEASURE,
            cls.OPTIMIZE,
            cls.VALIDATE,
            cls.DREAM,
            cls.REPORT
        ]

    def next_phase(self) -> Optional["DSPPhase"]:
        """Get next phase in sequence."""
        order = self.phase_order()
        if self == DSPPhase.IDLE:
            return DSPPhase.AUDIT
        if self == DSPPhase.COMPLETE:
            return None
        try:
            idx = order.index(self)
            if idx + 1 < len(order):
                return order[idx + 1]
            return DSPPhase.COMPLETE
        except ValueError:
            return None

    def prev_phase(self) -> Optional["DSPPhase"]:
        """Get previous phase in sequence."""
        order = self.phase_order()
        if self in (DSPPhase.IDLE, DSPPhase.AUDIT):
            return DSPPhase.IDLE
        if self == DSPPhase.COMPLETE:
            return DSPPhase.REPORT
        try:
            idx = order.index(self)
            if idx > 0:
                return order[idx - 1]
            return DSPPhase.IDLE
        except ValueError:
            return None

    @property
    def required_mcps(self) -> List[str]:
        """MCPs required for this phase per RULE-012."""
        mcp_map = {
            DSPPhase.AUDIT: ["claude-mem", "governance"],
            DSPPhase.HYPOTHESIZE: ["sequential-thinking"],
            DSPPhase.MEASURE: ["powershell", "llm-sandbox"],
            DSPPhase.OPTIMIZE: ["filesystem", "git"],
            DSPPhase.VALIDATE: ["pytest", "llm-sandbox"],
            DSPPhase.DREAM: ["claude-mem", "sequential-thinking"],
            DSPPhase.REPORT: ["filesystem", "git"]
        }
        return mcp_map.get(self, [])


@dataclass
class PhaseCheckpoint:
    """Checkpoint within a phase."""
    phase: str
    timestamp: str
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)


@dataclass
class DSMCycle:
    """A single DSM cycle with all phases."""
    cycle_id: str
    batch_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    current_phase: str = "idle"
    phases_completed: List[str] = field(default_factory=list)
    checkpoints: List[PhaseCheckpoint] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cycle_id": self.cycle_id,
            "batch_id": self.batch_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "current_phase": self.current_phase,
            "phases_completed": self.phases_completed,
            "checkpoints": [asdict(c) for c in self.checkpoints],
            "findings": self.findings,
            "metrics": self.metrics
        }


class DSMTracker:
    """
    Tracks Deep Sleep Mode cycles.

    Usage:
        tracker = DSMTracker()
        tracker.start_cycle("1001-1100")

        tracker.advance_phase()  # AUDIT
        tracker.add_finding("gap", "Missing test coverage for X")
        tracker.checkpoint("Audited 5 modules")

        tracker.advance_phase()  # HYPOTHESIZE
        # ... continue through phases

        evidence = tracker.complete_cycle()
    """

    def __init__(
        self,
        evidence_dir: str = None,
        state_file: str = None
    ):
        """
        Initialize DSM Tracker.

        Args:
            evidence_dir: Directory for evidence files (default: ./evidence)
            state_file: Path to state file for persistence (default: .dsm_state.json)
        """
        self.evidence_dir = Path(evidence_dir or "./evidence")
        self.state_file = Path(state_file or ".dsm_state.json")

        self.current_cycle: Optional[DSMCycle] = None
        self.completed_cycles: List[DSMCycle] = []

        # Load state if exists
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file if exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                if state.get("current_cycle"):
                    cycle_data = state["current_cycle"]
                    self.current_cycle = DSMCycle(
                        cycle_id=cycle_data["cycle_id"],
                        batch_id=cycle_data.get("batch_id"),
                        start_time=cycle_data.get("start_time"),
                        end_time=cycle_data.get("end_time"),
                        current_phase=cycle_data.get("current_phase", "idle"),
                        phases_completed=cycle_data.get("phases_completed", []),
                        checkpoints=[
                            PhaseCheckpoint(**cp) for cp in cycle_data.get("checkpoints", [])
                        ],
                        findings=cycle_data.get("findings", []),
                        metrics=cycle_data.get("metrics", {})
                    )
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_state(self) -> None:
        """Save state to file."""
        state = {
            "current_cycle": self.current_cycle.to_dict() if self.current_cycle else None,
            "completed_count": len(self.completed_cycles),
            "last_updated": datetime.now().isoformat()
        }
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def start_cycle(self, batch_id: str = None) -> DSMCycle:
        """
        Start a new DSM cycle.

        Args:
            batch_id: Optional batch identifier (e.g., "1001-1100")

        Returns:
            The new DSMCycle
        """
        if self.current_cycle and self.current_cycle.current_phase != "complete":
            raise ValueError("A cycle is already in progress. Complete or abort it first.")

        cycle_id = f"DSM-{date.today()}-{datetime.now().strftime('%H%M%S')}"

        self.current_cycle = DSMCycle(
            cycle_id=cycle_id,
            batch_id=batch_id,
            start_time=datetime.now().isoformat(),
            current_phase=DSPPhase.IDLE.value
        )

        self._save_state()
        return self.current_cycle

    def get_current_phase(self) -> DSPPhase:
        """Get current phase as enum."""
        if not self.current_cycle:
            return DSPPhase.IDLE
        return DSPPhase(self.current_cycle.current_phase)

    def advance_phase(self, force: bool = False) -> DSPPhase:
        """
        Advance to next phase.

        Per TASK 3.2: Validates that actual work was done before advancing.
        Each phase MUST produce evidence (checkpoints or findings).

        Args:
            force: Skip validation (for testing only, logs warning)

        Returns:
            The new phase

        Raises:
            ValueError: If no cycle in progress, cycle is complete, or
                       validation fails (no evidence for current phase)
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress. Start one with start_cycle()")

        current = self.get_current_phase()
        next_phase = current.next_phase()

        if next_phase is None:
            raise ValueError("Cycle is complete. Cannot advance further.")

        # Validate evidence was produced (skip for IDLE phase)
        if current != DSPPhase.IDLE and not force:
            validation_error = self._validate_phase_evidence(current)
            if validation_error:
                raise ValueError(
                    f"Cannot advance from {current.value}: {validation_error}. "
                    f"Add checkpoint() or add_finding() before advancing."
                )

        # Record completion of current phase
        if current != DSPPhase.IDLE:
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = next_phase.value

        self._save_state()
        return next_phase

    def _validate_phase_evidence(self, phase: DSPPhase) -> Optional[str]:
        """
        Validate that required evidence exists for a phase.

        Per TASK 3.1: Each phase MUST produce evidence.

        Returns:
            Error message if validation fails, None if valid
        """
        # Get checkpoints and findings for this phase
        phase_checkpoints = [
            cp for cp in self.current_cycle.checkpoints
            if cp.phase == phase.value
        ]
        phase_findings = [
            f for f in self.current_cycle.findings
            if f.get("phase") == phase.value
        ]

        # Phase-specific requirements
        requirements = {
            DSPPhase.AUDIT: {
                "need_checkpoint_or_finding": True,
                "finding_types": ["gap", "issue", "improvement", "orphan"],
                "min_checkpoint_chars": 20,
                "description": "Audit must identify at least one gap, issue, or checkpoint"
            },
            DSPPhase.HYPOTHESIZE: {
                "need_checkpoint": True,
                "min_checkpoint_chars": 30,
                "description": "Hypothesis must be documented in checkpoint"
            },
            DSPPhase.MEASURE: {
                "need_checkpoint_with_metrics": True,
                "description": "Measurements must include metrics in checkpoint"
            },
            DSPPhase.OPTIMIZE: {
                "need_checkpoint": True,
                "min_checkpoint_chars": 20,
                "description": "Optimizations must be documented in checkpoint"
            },
            DSPPhase.VALIDATE: {
                "need_checkpoint": True,
                "min_checkpoint_chars": 10,
                "description": "Validation results must be documented"
            },
            DSPPhase.DREAM: {
                "need_checkpoint_or_finding": True,
                "min_checkpoint_chars": 10,
                "description": "Dream phase must produce discoveries or observations"
            },
            DSPPhase.REPORT: {
                # Report phase generates evidence automatically
                "need_checkpoint_or_finding": False,
                "description": "Report auto-generates evidence"
            }
        }

        req = requirements.get(phase)
        if not req:
            return None  # Unknown phase, allow

        # Check requirements
        has_valid_checkpoint = any(
            len(cp.description) >= req.get("min_checkpoint_chars", 0)
            for cp in phase_checkpoints
        )
        has_valid_finding = len(phase_findings) > 0

        if req.get("need_checkpoint_with_metrics"):
            # Must have checkpoint with non-empty metrics
            has_metrics = any(
                cp.metrics and len(cp.metrics) > 0
                for cp in phase_checkpoints
            )
            if not has_metrics:
                return f"{phase.value.upper()}: Requires checkpoint with metrics"
            return None

        if req.get("need_checkpoint"):
            if not has_valid_checkpoint:
                return f"{phase.value.upper()}: Requires checkpoint (min {req.get('min_checkpoint_chars', 0)} chars)"
            return None

        if req.get("need_checkpoint_or_finding"):
            if not has_valid_checkpoint and not has_valid_finding:
                return f"{phase.value.upper()}: Requires checkpoint or finding"
            return None

        return None  # All checks passed

    def go_to_phase(self, phase: DSPPhase) -> DSPPhase:
        """
        Jump to a specific phase (for non-linear workflows).

        Args:
            phase: Target phase

        Returns:
            The new phase
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress. Start one with start_cycle()")

        if phase in (DSPPhase.IDLE, DSPPhase.COMPLETE):
            raise ValueError(f"Cannot jump to {phase.value}")

        current = self.get_current_phase()
        if current != DSPPhase.IDLE:
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = phase.value
        self._save_state()
        return phase

    def checkpoint(
        self,
        description: str,
        metrics: Dict[str, Any] = None,
        evidence: List[str] = None
    ) -> PhaseCheckpoint:
        """
        Create a checkpoint in the current phase.

        Args:
            description: Description of checkpoint
            metrics: Optional metrics
            evidence: Optional list of evidence references

        Returns:
            The created checkpoint
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        cp = PhaseCheckpoint(
            phase=self.current_cycle.current_phase,
            timestamp=datetime.now().isoformat(),
            description=description,
            metrics=metrics or {},
            evidence=evidence or []
        )

        self.current_cycle.checkpoints.append(cp)
        self._save_state()
        return cp

    def add_finding(
        self,
        finding_type: str,
        description: str,
        severity: str = "MEDIUM",
        related_rules: List[str] = None
    ) -> Dict[str, Any]:
        """
        Add a finding during the current phase.

        Args:
            finding_type: Type of finding (gap, orphan, conflict, improvement)
            description: Finding description
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            related_rules: List of related rule IDs

        Returns:
            The created finding
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        finding = {
            "id": f"FINDING-{len(self.current_cycle.findings) + 1:03d}",
            "type": finding_type,
            "description": description,
            "severity": severity,
            "phase": self.current_cycle.current_phase,
            "timestamp": datetime.now().isoformat(),
            "related_rules": related_rules or []
        }

        self.current_cycle.findings.append(finding)
        self._save_state()
        return finding

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update cycle metrics.

        Args:
            metrics: Dictionary of metrics to update
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        self.current_cycle.metrics.update(metrics)
        self._save_state()

    def complete_cycle(self) -> str:
        """
        Complete the current cycle and generate evidence.

        Returns:
            Path to generated evidence file
        """
        if not self.current_cycle:
            raise ValueError("No cycle in progress")

        # Mark complete
        current = self.get_current_phase()
        if current != DSPPhase.IDLE and current not in (DSPPhase.COMPLETE, DSPPhase.REPORT):
            self.current_cycle.phases_completed.append(current.value)

        self.current_cycle.current_phase = DSPPhase.COMPLETE.value
        self.current_cycle.end_time = datetime.now().isoformat()

        # Generate evidence file
        evidence_path = self._generate_evidence()

        # Archive cycle
        self.completed_cycles.append(self.current_cycle)
        self.current_cycle = None
        self._save_state()

        return evidence_path

    def get_session_memory_payload(self) -> Optional[Dict[str, Any]]:
        """
        Get payload for saving cycle context to claude-mem (P11.4).

        Returns dict ready for chroma_add_documents MCP call, or None if no cycle.
        Per RULE-024 (AMNESIA Protocol): Save session context for recovery.
        """
        if not self.current_cycle:
            return None

        try:
            from governance.session_memory import create_dsp_session_context

            # Create session context from cycle data
            ctx = create_dsp_session_context(
                cycle_id=self.current_cycle.cycle_id,
                batch_id=self.current_cycle.batch_id,
                phases_completed=self.current_cycle.phases_completed,
                findings=self.current_cycle.findings,
                checkpoints=[asdict(cp) for cp in self.current_cycle.checkpoints],
                metrics=self.current_cycle.metrics,
            )

            # Return payload for MCP call
            doc_id = f"sim-ai-dsp-{self.current_cycle.cycle_id}"
            return {
                "collection_name": "claude_memories",
                "documents": [ctx.to_document()],
                "ids": [doc_id],
                "metadatas": [ctx.to_metadata()],
            }
        except ImportError:
            return None

    def abort_cycle(self, reason: str = None) -> None:
        """
        Abort the current cycle.

        Args:
            reason: Optional abort reason
        """
        if not self.current_cycle:
            return

        self.current_cycle.metrics["aborted"] = True
        self.current_cycle.metrics["abort_reason"] = reason or "Unknown"
        self.current_cycle.end_time = datetime.now().isoformat()
        self.current_cycle.current_phase = "aborted"

        # Save but don't archive
        self.current_cycle = None
        self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """
        Get current tracker status.

        Returns:
            Status dictionary
        """
        if not self.current_cycle:
            return {
                "active": False,
                "message": "No cycle in progress"
            }

        current_phase = self.get_current_phase()
        phases_order = DSPPhase.phase_order()
        completed_count = len(self.current_cycle.phases_completed)
        total_phases = len(phases_order)

        return {
            "active": True,
            "cycle_id": self.current_cycle.cycle_id,
            "batch_id": self.current_cycle.batch_id,
            "current_phase": current_phase.value,
            "phases_completed": self.current_cycle.phases_completed,
            "progress": f"{completed_count}/{total_phases}",
            "progress_percent": round(completed_count / total_phases * 100, 1),
            "checkpoints_count": len(self.current_cycle.checkpoints),
            "findings_count": len(self.current_cycle.findings),
            "required_mcps": current_phase.required_mcps,
            "start_time": self.current_cycle.start_time
        }

    def _generate_evidence(self) -> str:
        """Generate markdown evidence file."""
        if not self.current_cycle:
            raise ValueError("No cycle to generate evidence for")

        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.current_cycle.cycle_id}.md"
        filepath = self.evidence_dir / filename

        lines = [
            f"# DSM Cycle Evidence: {self.current_cycle.cycle_id}",
            "",
            "## Summary",
            "",
            f"- **Batch:** {self.current_cycle.batch_id or 'N/A'}",
            f"- **Started:** {self.current_cycle.start_time}",
            f"- **Ended:** {self.current_cycle.end_time}",
            f"- **Phases Completed:** {len(self.current_cycle.phases_completed)}",
            f"- **Findings:** {len(self.current_cycle.findings)}",
            f"- **Checkpoints:** {len(self.current_cycle.checkpoints)}",
            "",
            "---",
            "",
        ]

        # Metrics section
        if self.current_cycle.metrics:
            lines.extend([
                "## Metrics",
                "",
                "| Metric | Value |",
                "|--------|-------|",
            ])
            for key, value in self.current_cycle.metrics.items():
                lines.append(f"| {key} | {value} |")
            lines.extend(["", "---", ""])

        # Findings section
        if self.current_cycle.findings:
            lines.extend([
                "## Findings",
                "",
                "| ID | Type | Severity | Description |",
                "|----|------|----------|-------------|",
            ])
            for f in self.current_cycle.findings:
                lines.append(
                    f"| {f['id']} | {f['type']} | {f['severity']} | {f['description'][:50]}... |"
                )
            lines.extend(["", "---", ""])

        # Checkpoints section
        if self.current_cycle.checkpoints:
            lines.extend([
                "## Checkpoints",
                "",
            ])
            for cp in self.current_cycle.checkpoints:
                lines.extend([
                    f"### {cp.phase.upper()} - {cp.timestamp}",
                    "",
                    cp.description,
                    "",
                ])
                if cp.evidence:
                    lines.append("**Evidence:**")
                    for e in cp.evidence:
                        lines.append(f"- {e}")
                    lines.append("")

        lines.extend([
            "---",
            "",
            "*Generated per RULE-012: Deep Sleep Protocol*",
        ])

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(filepath)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tracker state to dictionary."""
        return {
            "current_cycle": self.current_cycle.to_dict() if self.current_cycle else None,
            "completed_cycles_count": len(self.completed_cycles),
            "evidence_dir": str(self.evidence_dir),
            "state_file": str(self.state_file)
        }

    def to_json(self) -> str:
        """Convert tracker state to JSON."""
        return json.dumps(self.to_dict(), indent=2)


# Global tracker instance
_tracker: Optional[DSMTracker] = None


def get_tracker(evidence_dir: str = None) -> DSMTracker:
    """Get or create global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DSMTracker(evidence_dir=evidence_dir)
    return _tracker


def reset_tracker() -> None:
    """Reset global tracker instance (for testing)."""
    global _tracker
    _tracker = None
