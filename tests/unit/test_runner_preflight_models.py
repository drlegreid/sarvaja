"""
Unit tests for Test Runner Preflight Models & Functions.

Batch 154: Mock-based tests for governance/routes/tests/runner_preflight.py
- TestResult / TestRunSummary Pydantic models
- list_test_categories: async category listing
- preflight_check: filesystem discovery with mocked root
- register_preflight_routes: route registration
"""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from governance.routes.tests.runner_preflight import (
    TestResult,
    TestRunSummary,
    list_test_categories,
    preflight_check,
    register_preflight_routes,
)


# ── Pydantic models ─────────────────────────────────────

class TestTestResultModel:
    def test_basic_fields(self):
        r = TestResult(nodeid="test_foo.py::test_bar", outcome="passed", duration=0.5)
        assert r.nodeid == "test_foo.py::test_bar"
        assert r.outcome == "passed"
        assert r.duration == 0.5
        assert r.error is None

    def test_with_error(self):
        r = TestResult(nodeid="t", outcome="failed", duration=1.0, error="AssertionError")
        assert r.error == "AssertionError"

    def test_serialization(self):
        r = TestResult(nodeid="t", outcome="skipped", duration=0.0)
        d = r.model_dump()
        assert d["nodeid"] == "t"
        assert d["outcome"] == "skipped"


class TestTestRunSummaryModel:
    def test_basic_fields(self):
        s = TestRunSummary(
            timestamp="2026-02-13T00:00:00",
            status="completed",
            total=10, passed=8, failed=1, skipped=1,
            duration_seconds=5.5,
            tests=[],
        )
        assert s.total == 10
        assert s.passed == 8
        assert s.status == "completed"

    def test_with_tests(self):
        t = TestResult(nodeid="t1", outcome="passed", duration=0.1)
        s = TestRunSummary(
            timestamp="ts", status="running",
            total=1, passed=1, failed=0, skipped=0,
            duration_seconds=0.1, tests=[t],
        )
        assert len(s.tests) == 1
        assert s.tests[0].nodeid == "t1"


# ── list_test_categories ─────────────────────────────────

class TestListTestCategories:
    def test_returns_categories(self):
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        assert "categories" in result
        assert len(result["categories"]) >= 5

    def test_has_unit_category(self):
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        ids = [c["id"] for c in result["categories"]]
        assert "unit" in ids

    def test_has_regression_category(self):
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        ids = [c["id"] for c in result["categories"]]
        assert "regression" in ids

    def test_each_has_required_fields(self):
        result = asyncio.get_event_loop().run_until_complete(list_test_categories())
        for cat in result["categories"]:
            assert "id" in cat
            assert "name" in cat
            assert "pattern" in cat


# ── preflight_check ──────────────────────────────────────

class TestPreflightCheckMocked:
    def test_discovers_unit_tests(self, tmp_path):
        tests_dir = tmp_path / "tests"
        unit_dir = tests_dir / "unit"
        unit_dir.mkdir(parents=True)
        (unit_dir / "test_foo.py").write_text("# test")
        (unit_dir / "test_bar.py").write_text("# test")

        with patch("governance.routes.tests.runner_preflight._resolve_test_root",
                    return_value=str(tmp_path)):
            result = asyncio.get_event_loop().run_until_complete(preflight_check())

        assert result["tests_dir_exists"] is True
        assert result["total_files"] >= 2
        unit_cat = next(c for c in result["categories"] if c["id"] == "unit")
        assert unit_cat["file_count"] == 2

    def test_empty_tests_dir(self, tmp_path):
        (tmp_path / "tests").mkdir()
        with patch("governance.routes.tests.runner_preflight._resolve_test_root",
                    return_value=str(tmp_path)):
            result = asyncio.get_event_loop().run_until_complete(preflight_check())
        assert result["total_files"] == 0

    def test_missing_tests_dir(self, tmp_path):
        with patch("governance.routes.tests.runner_preflight._resolve_test_root",
                    return_value=str(tmp_path)):
            result = asyncio.get_event_loop().run_until_complete(preflight_check())
        assert result["tests_dir_exists"] is False

    def test_robot_files_discovered(self, tmp_path):
        robot_dir = tmp_path / "tests" / "robot" / "e2e"
        robot_dir.mkdir(parents=True)
        (robot_dir / "dash.robot").write_text("*** Test ***")
        with patch("governance.routes.tests.runner_preflight._resolve_test_root",
                    return_value=str(tmp_path)):
            result = asyncio.get_event_loop().run_until_complete(preflight_check())
        robot_cat = next(c for c in result["categories"] if c["id"] == "robot")
        assert robot_cat["file_count"] == 1

    def test_ui_subdir_included(self, tmp_path):
        ui_dir = tmp_path / "tests" / "unit" / "ui"
        ui_dir.mkdir(parents=True)
        (ui_dir / "test_ui.py").write_text("# test")
        with patch("governance.routes.tests.runner_preflight._resolve_test_root",
                    return_value=str(tmp_path)):
            result = asyncio.get_event_loop().run_until_complete(preflight_check())
        unit_cat = next(c for c in result["categories"] if c["id"] == "unit")
        assert unit_cat["file_count"] == 1


# ── register_preflight_routes ────────────────────────────

class TestRegisterPreflightRoutes:
    def test_registers_two_routes(self):
        mock_router = MagicMock()
        register_preflight_routes(mock_router)
        assert mock_router.get.call_count == 2
