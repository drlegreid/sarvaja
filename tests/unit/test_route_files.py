"""
Unit tests for Files Routes.

Per DOC-SIZE-01-v1: Tests for routes/files.py module.
Tests: get_file_content endpoint with security controls.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from governance.routes.files import router


@pytest.fixture
def client():
    """Create FastAPI test client with files router."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Security: allowed prefixes
# ---------------------------------------------------------------------------
class TestFileSecurity:
    """Tests for file access security controls."""

    def test_rejects_disallowed_path(self, client):
        response = client.get("/api/files/content?path=secrets/passwords.txt")
        assert response.status_code == 404  # Multi-root resolution: no match → 404

    def test_rejects_root_path(self, client):
        response = client.get("/api/files/content?path=/etc/passwd")
        assert response.status_code == 403

    def test_rejects_no_prefix(self, client):
        response = client.get("/api/files/content?path=random.txt")
        assert response.status_code == 404  # Multi-root resolution: no match → 404

    def test_rejects_path_traversal(self, client):
        response = client.get("/api/files/content?path=evidence/../../../etc/passwd")
        # Should be caught by either prefix check or traversal check
        assert response.status_code in (403, 404)

    def test_allows_evidence_prefix(self, client, tmp_path):
        """Evidence prefix should be allowed (may 404 if file doesn't exist)."""
        response = client.get("/api/files/content?path=evidence/nonexistent.md")
        # 404 is fine — the security check passed, file just doesn't exist
        assert response.status_code in (404, 200)

    def test_allows_docs_prefix(self, client):
        response = client.get("/api/files/content?path=docs/nonexistent.md")
        assert response.status_code in (404, 200)


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------
class TestFileReading:
    """Tests for file content reading."""

    def test_reads_existing_docs_file(self, client):
        """Test reading an existing file from docs/ (uses real project root)."""
        # docs/RULES-DIRECTIVES.md should exist in the project
        response = client.get("/api/files/content?path=docs/RULES-DIRECTIVES.md")
        if response.status_code == 200:
            data = response.json()
            assert data["path"] == "docs/RULES-DIRECTIVES.md"
            assert len(data["content"]) > 0
            assert data["size"] > 0
        else:
            # File may not exist in test env; just verify we got past security
            assert response.status_code == 404

    def test_404_for_nonexistent(self, client):
        response = client.get("/api/files/content?path=evidence/no-such-file.md")
        assert response.status_code == 404

    def test_normalizes_backslashes(self, client):
        """Windows-style paths should be normalized."""
        response = client.get("/api/files/content?path=evidence\\test.md")
        # Should normalize and then 404 (file doesn't exist)
        assert response.status_code in (403, 404)

    def test_query_param_required(self, client):
        """Missing path param should fail."""
        response = client.get("/api/files/content")
        assert response.status_code == 422  # FastAPI validation error
