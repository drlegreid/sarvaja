"""
Tests for test runner preflight checks and path resolution.

Per D.1: Fix test execution path - TDD test first.
Verifies:
- Preflight endpoint detects test files correctly
- Test category patterns match actual test structure
- Path resolution works in both container and local environments

Created: 2026-02-01
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for runner API."""
    from governance.routes.tests.runner import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


class TestPreflightEndpoint:
    """Tests for GET /api/tests/preflight."""

    def test_preflight_returns_discovered_files(self, client):
        """Preflight should discover actual test files on disk."""
        response = client.get("/api/tests/preflight")
        assert response.status_code == 200
        data = response.json()
        assert "test_root" in data
        assert "categories" in data
        assert "total_files" in data
        assert data["total_files"] > 0

    def test_preflight_discovers_unit_tests(self, client):
        """Preflight should find unit tests in tests/unit/."""
        response = client.get("/api/tests/preflight")
        data = response.json()
        categories = data["categories"]
        unit_cat = next((c for c in categories if c["id"] == "unit"), None)
        assert unit_cat is not None
        assert unit_cat["file_count"] > 0

    def test_preflight_discovers_robot_tests(self, client):
        """Preflight should find Robot Framework tests."""
        response = client.get("/api/tests/preflight")
        data = response.json()
        categories = data["categories"]
        robot_cat = next((c for c in categories if c["id"] == "robot"), None)
        assert robot_cat is not None
        assert robot_cat["file_count"] > 0

    def test_preflight_discovers_e2e_tests(self, client):
        """Preflight should find E2E tests."""
        response = client.get("/api/tests/preflight")
        data = response.json()
        categories = data["categories"]
        e2e_cat = next((c for c in categories if c["id"] == "e2e"), None)
        assert e2e_cat is not None
        assert e2e_cat["file_count"] > 0

    def test_preflight_shows_test_root_path(self, client):
        """Preflight should report the resolved test root path."""
        response = client.get("/api/tests/preflight")
        data = response.json()
        assert Path(data["test_root"]).exists()


class TestCategoryPatterns:
    """Tests for test category patterns matching actual files."""

    def test_categories_list_updated(self, client):
        """Categories endpoint should reflect actual test structure."""
        response = client.get("/api/tests/categories")
        data = response.json()
        cat_ids = [c["id"] for c in data["categories"]]
        assert "unit" in cat_ids
        assert "robot" in cat_ids

    def test_unit_category_resolves_to_existing_files(self, client):
        """Unit category pattern should match existing test files."""
        response = client.get("/api/tests/categories")
        data = response.json()
        unit_cat = next(c for c in data["categories"] if c["id"] == "unit")
        # Pattern should point to tests/unit/ directory
        assert "tests/unit" in unit_cat["pattern"]


class TestPathResolution:
    """Tests for test runner working directory resolution."""

    def test_resolve_test_root_finds_tests_dir(self):
        """_resolve_test_root should find a directory containing tests/."""
        from governance.routes.tests.runner import _resolve_test_root
        root = _resolve_test_root()
        assert (Path(root) / "tests").is_dir()

    def test_resolve_test_root_has_unit_tests(self):
        """Resolved root should contain tests/unit/ subdirectory."""
        from governance.routes.tests.runner import _resolve_test_root
        root = _resolve_test_root()
        assert (Path(root) / "tests" / "unit").is_dir()
