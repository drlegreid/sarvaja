"""
Test Runner Discovery & Preflight Endpoints.

Per DOC-SIZE-01-v1: Extracted from runner.py.
Models, test category listing, and preflight file discovery.

Created: 2026-02-11
"""
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

from governance.routes.tests.runner_store import _resolve_test_root

logger = logging.getLogger(__name__)


class TestResult(BaseModel):
    """Individual test result."""
    nodeid: str
    outcome: str  # passed, failed, skipped
    duration: float
    error: Optional[str] = None


class TestRunSummary(BaseModel):
    """Test run summary."""
    timestamp: str
    status: str  # running, completed, failed
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    tests: List[TestResult]


async def list_test_categories():
    """List available test categories."""
    return {
        "categories": [
            {"id": "unit", "name": "Unit Tests", "pattern": "tests/unit/", "description": "Fast unit tests"},
            {"id": "governance", "name": "Governance", "pattern": "tests/test_governance.py tests/test_rules_governance.py", "description": "TypeDB governance tests"},
            {"id": "ui", "name": "UI Tests", "pattern": "tests/unit/ui/", "description": "Dashboard UI tests"},
            {"id": "kanren", "name": "Kanren", "pattern": "tests/test_kanren_constraints.py", "description": "Constraint engine tests"},
            {"id": "api", "name": "API Tests", "pattern": "tests/test_data_integrity.py tests/test_chat.py", "description": "REST API tests"},
            {"id": "e2e", "name": "E2E Tests", "pattern": "tests/e2e/", "description": "End-to-end pytest tests"},
            {"id": "robot", "name": "Robot Framework", "pattern": "tests/robot/e2e/", "description": "Robot Framework E2E suites"},
            {"id": "rules", "name": "Rules Tests", "pattern": "tests/rules/", "description": "Rule validation tests"},
            {"id": "regression", "name": "Full Regression", "pattern": "all", "description": "Static + Heuristic + Dynamic Playwright (default)"},
        ]
    }


async def preflight_check():
    """
    Verify test files are accessible before running.

    Returns discovered test files per category, resolved root path,
    and total file count. Use this to diagnose test runner issues.
    """
    test_root = _resolve_test_root()
    root_path = Path(test_root)
    tests_dir = root_path / "tests"

    categories = []
    total_files = 0

    # Unit tests
    unit_dir = tests_dir / "unit"
    unit_files = sorted(unit_dir.glob("test_*.py")) if unit_dir.is_dir() else []
    if (unit_dir / "ui").is_dir():
        unit_files.extend(sorted((unit_dir / "ui").glob("test_*.py")))
    categories.append({
        "id": "unit", "name": "Unit Tests",
        "file_count": len(unit_files),
        "files": [str(f.relative_to(root_path)) for f in unit_files[:20]],
    })
    total_files += len(unit_files)

    # Robot Framework tests
    robot_dirs = [tests_dir / "robot" / "e2e", tests_dir / "robot"]
    robot_files = []
    for rd in robot_dirs:
        if rd.is_dir():
            robot_files.extend(sorted(rd.glob("*.robot")))
    categories.append({
        "id": "robot", "name": "Robot Framework",
        "file_count": len(robot_files),
        "files": [str(f.relative_to(root_path)) for f in robot_files[:20]],
    })
    total_files += len(robot_files)

    # E2E pytest tests
    e2e_dir = tests_dir / "e2e"
    e2e_files = sorted(e2e_dir.glob("test_*.py")) if e2e_dir.is_dir() else []
    categories.append({
        "id": "e2e", "name": "E2E Tests",
        "file_count": len(e2e_files),
        "files": [str(f.relative_to(root_path)) for f in e2e_files[:20]],
    })
    total_files += len(e2e_files)

    # Root-level test files
    root_tests = sorted(tests_dir.glob("test_*.py"))
    categories.append({
        "id": "root", "name": "Root Tests",
        "file_count": len(root_tests),
        "files": [str(f.relative_to(root_path)) for f in root_tests[:20]],
    })
    total_files += len(root_tests)

    # Rules tests
    rules_dir = tests_dir / "rules"
    rules_files = sorted(rules_dir.glob("test_*.py")) if rules_dir.is_dir() else []
    categories.append({
        "id": "rules", "name": "Rules Tests",
        "file_count": len(rules_files),
        "files": [str(f.relative_to(root_path)) for f in rules_files[:20]],
    })
    total_files += len(rules_files)

    return {
        "test_root": test_root,
        "tests_dir_exists": tests_dir.is_dir(),
        "total_files": total_files,
        "categories": categories,
    }


def register_preflight_routes(router: APIRouter) -> None:
    """Register preflight and discovery routes on the given router."""
    router.get("/categories")(list_test_categories)
    router.get("/preflight")(preflight_check)
