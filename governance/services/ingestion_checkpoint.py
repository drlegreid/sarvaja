"""Checkpoint engine for resumable session ingestion (SESSION-METRICS-01-v1).

Tracks ingestion progress so processing can resume after crash or interruption.
Storage: .ingestion_checkpoints/{session_id}.json (atomic writes).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Default checkpoint directory (relative to project root)
_DEFAULT_CHECKPOINT_DIR = Path(".ingestion_checkpoints")


@dataclass
class IngestionCheckpoint:
    """Tracks incremental ingestion progress for a single session."""

    session_id: str
    jsonl_path: str
    lines_processed: int = 0
    chunks_indexed: int = 0
    links_created: int = 0
    phase: str = "pending"  # pending | content | linking | complete
    started_at: str = ""
    updated_at: str = ""
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.started_at:
            self.started_at = _now_iso()
        if not self.updated_at:
            self.updated_at = self.started_at

    def touch(self) -> None:
        """Update the timestamp."""
        self.updated_at = _now_iso()

    def add_error(self, msg: str, *, max_errors: int = 200) -> None:
        """Record an error, capping list size."""
        if len(self.errors) < max_errors:
            self.errors.append(f"[{_now_iso()}] {msg}")
        self.touch()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> IngestionCheckpoint:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checkpoint_path(checkpoint_dir: Path, session_id: str) -> Path:
    safe_name = session_id.replace("/", "_").replace("\\", "_")
    return checkpoint_dir / f"{safe_name}.json"


def load_checkpoint(
    session_id: str, checkpoint_dir: Optional[Path] = None
) -> Optional[IngestionCheckpoint]:
    """Load a checkpoint from disk.

    Returns None if no checkpoint exists or file is corrupt.
    """
    cdir = checkpoint_dir or _DEFAULT_CHECKPOINT_DIR
    path = _checkpoint_path(cdir, session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return IngestionCheckpoint.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_checkpoint(
    checkpoint: IngestionCheckpoint,
    checkpoint_dir: Optional[Path] = None,
) -> Path:
    """Save checkpoint atomically (temp file + os.replace).

    Returns the path written to.
    """
    cdir = checkpoint_dir or _DEFAULT_CHECKPOINT_DIR
    cdir.mkdir(parents=True, exist_ok=True)
    checkpoint.touch()

    target = _checkpoint_path(cdir, checkpoint.session_id)
    fd, temp_path = tempfile.mkstemp(
        suffix=".tmp", prefix=".ckpt_", dir=str(cdir)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)
        os.replace(temp_path, target)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
    return target


def get_resume_offset(
    session_id: str, checkpoint_dir: Optional[Path] = None
) -> int:
    """Get the line offset to resume from. Returns 0 for fresh start."""
    ckpt = load_checkpoint(session_id, checkpoint_dir)
    if ckpt is None:
        return 0
    return ckpt.lines_processed


def delete_checkpoint(
    session_id: str, checkpoint_dir: Optional[Path] = None
) -> bool:
    """Remove a checkpoint file. Returns True if deleted."""
    cdir = checkpoint_dir or _DEFAULT_CHECKPOINT_DIR
    path = _checkpoint_path(cdir, session_id)
    if path.exists():
        path.unlink()
        return True
    return False
