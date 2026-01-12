"""
DSM Data Models
Created: 2024-12-24
Modularized: 2026-01-02 (RULE-032)

Dataclasses for DSM cycle tracking.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict


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
