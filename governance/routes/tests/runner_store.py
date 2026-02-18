"""
Test Result Storage & Persistence (DOC-SIZE-01-v1 split from runner.py)

Handles in-memory result store, disk persistence, and test root resolution.
Per D.2: Test results survive container restarts via JSON persistence.

Created: 2026-02-01
"""
import json
import logging
import re
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
# BUG-207-STORE-001: Cap at 200 entries to prevent unbounded growth
_MAX_TEST_RESULTS = 200
_test_results: dict = {}


def _cap_test_results() -> None:
    """Evict oldest entries if _test_results exceeds max size."""
    if len(_test_results) > _MAX_TEST_RESULTS:
        # BUG-221-EVICT-001: Sort by timestamp (oldest first), not alphabetically
        sorted_keys = sorted(_test_results.keys(), key=lambda k: _test_results[k].get("timestamp", k))
        excess = len(_test_results) - _MAX_TEST_RESULTS
        for k in sorted_keys[:excess]:
            _test_results.pop(k, None)


def _persist_result(run_id: str, result: dict, results_dir: str = None) -> None:
    """Persist a test result to JSON file. Per D.2."""
    # BUG-231-003: Whitelist sanitize run_id to prevent path traversal
    safe_id = re.sub(r'[^A-Za-z0-9_\-]', '_', run_id)
    target_dir = Path(results_dir or _RESULTS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / f"{safe_id}.json"
    # BUG-264-STORE-001: Specify encoding for cross-platform safety
    filepath.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    # BUG-207-STORE-001: Cap in-memory dict after each persist
    _cap_test_results()


def _load_persisted_results(results_dir: str = None) -> dict:
    """Load persisted test results from disk. Per D.2."""
    target_dir = Path(results_dir or _RESULTS_DIR)
    results = {}
    if target_dir.is_dir():
        for filepath in sorted(target_dir.glob("*.json"), reverse=True)[:50]:
            try:
                # BUG-264-STORE-002: Specify encoding for cross-platform safety
                data = json.loads(filepath.read_text(encoding="utf-8"))
                run_id = filepath.stem
                results[run_id] = data
            except Exception as e:
                # BUG-STORE-006: Log instead of silently skipping
                # BUG-440-RST-001: Upgrade debug→warning + exc_info for operational visibility
                logger.warning(f"Failed to load test result {filepath.name}: {e}", exc_info=True)
                continue
    return results


# Load persisted results on import (D.2: survive restarts)
try:
    _test_results.update(_load_persisted_results())
    # BUG-285-STORE-001: Cap immediately after bulk load to prevent exceeding max
    _cap_test_results()
except Exception as e:
    # BUG-285-STORE-001: Promote to warning — startup load failure is operationally significant
    # BUG-440-RST-002: Add exc_info for stack trace preservation
    logger.warning(f"Failed to load persisted test results on import: {e}", exc_info=True)
