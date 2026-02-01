"""
Test Result Storage & Persistence (DOC-SIZE-01-v1 split from runner.py)

Handles in-memory result store, disk persistence, and test root resolution.
Per D.2: Test results survive container restarts via JSON persistence.

Created: 2026-02-01
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _resolve_test_root() -> str:
    """Resolve the project root directory containing tests/.

    Checks /app (container), then walks up from this file to find tests/ dir.
    Returns absolute path string.
    """
    if Path("/app/tests").is_dir():
        return "/app"
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "tests").is_dir() and (parent / "tests" / "unit").is_dir():
            return str(parent)
    return str(Path.cwd())


# Default persistence directory
_RESULTS_DIR = str(Path(_resolve_test_root()) / "evidence" / "test-results")

# In-memory store for test results (D.2: also persisted to disk)
_test_results: dict = {}


def _persist_result(run_id: str, result: dict, results_dir: str = None) -> None:
    """Persist a test result to JSON file. Per D.2."""
    target_dir = Path(results_dir or _RESULTS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{run_id}.json"
    filepath.write_text(json.dumps(result, indent=2, default=str))


def _load_persisted_results(results_dir: str = None) -> dict:
    """Load persisted test results from disk. Per D.2."""
    target_dir = Path(results_dir or _RESULTS_DIR)
    results = {}
    if target_dir.is_dir():
        for filepath in sorted(target_dir.glob("*.json"), reverse=True)[:50]:
            try:
                data = json.loads(filepath.read_text())
                run_id = filepath.stem
                results[run_id] = data
            except Exception:
                continue
    return results


# Load persisted results on import (D.2: survive restarts)
try:
    _test_results.update(_load_persisted_results())
except Exception:
    pass
