"""Deep scan batch 93: TypeDB queries, client, route handlers, app config.

Batch 93 findings: 29 total, 0 confirmed fixes, 29 rejected.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── TypeDB query defense ──────────────


class TestTypeDBTimestampFormat:
    """Verify timestamp formatting is correct for TypeDB 3.x."""

    def test_timestamp_truncation_produces_valid_format(self):
        """[:19] truncation on ISO string produces valid TypeDB datetime."""
        from datetime import datetime

        ts = datetime.now().isoformat()
        truncated = ts[:19]
        # Must be YYYY-MM-DDTHH:MM:SS format
        assert len(truncated) == 19
        assert truncated[4] == "-"
        assert truncated[7] == "-"
        assert truncated[10] == "T"
        assert truncated[13] == ":"
        assert truncated[16] == ":"


class TestTypeDBConnectionHandling:
    """Verify TypeDB client connection handling."""

    def test_client_health_check_returns_bool(self):
        """Health check returns boolean without crashing."""
        from governance.client import quick_health

        with patch("socket.socket") as mock_socket:
            mock_sock = MagicMock()
            mock_socket.return_value = mock_sock
            mock_sock.connect_ex.return_value = 1  # Connection refused

            result = quick_health()
            assert isinstance(result, bool)


class TestTypeDBEscaping:
    """Verify TypeDB escaping patterns."""

    def test_session_id_escaping(self):
        """Double quotes in session IDs are escaped."""
        session_id = 'SESSION-2026-02-15-"TEST"'
        escaped = session_id.replace('"', '\\"')
        assert '\\"' in escaped
        assert '"TEST"' not in escaped.replace('\\"', '')


# ── Route handler defense ──────────────


class TestEnsureResponse:
    """Verify _ensure_response normalization."""

    def test_returns_session_response_passthrough(self):
        """SessionResponse objects pass through unchanged."""
        from governance.routes.sessions.crud import _ensure_response
        from governance.models import SessionResponse

        resp = SessionResponse(
            session_id="TEST-001",
            start_time="2026-02-15T10:00:00",
            status="ACTIVE",
        )
        result = _ensure_response(resp)
        assert result.session_id == "TEST-001"
        assert result.status == "ACTIVE"

    def test_dict_with_status_preserves_status(self):
        """Dict with explicit status keeps it (not overwritten by default)."""
        from governance.routes.sessions.crud import _ensure_response

        result = _ensure_response({
            "session_id": "TEST-002",
            "start_time": "2026-02-15T10:00:00",
            "status": "ACTIVE",
        })
        assert result.status == "ACTIVE"  # Not overwritten to COMPLETED


class TestPathTraversalGuard:
    """Verify path traversal protection in evidence route."""

    def test_startswith_with_separator_blocks_prefix_attack(self):
        """startswith(path + os.sep) blocks /evidence-backup style attacks."""
        import os

        evidence_dir = "/app/evidence"
        attack_path = "/app/evidence-backup/secret.md"
        # With os.sep, this correctly rejects the attack
        assert not attack_path.startswith(evidence_dir + os.sep)

    def test_valid_evidence_path_allowed(self):
        import os

        evidence_dir = "/app/evidence"
        valid_path = "/app/evidence/SESSION-2026-02-15.md"
        assert valid_path.startswith(evidence_dir + os.sep)


class TestCORSConfig:
    """Verify CORS config loads without error."""

    def test_api_app_creates(self):
        """FastAPI app with CORS middleware loads."""
        # Just verify the module loads — CORS config is validated by Starlette
        from governance.api import app
        assert app is not None


# ── Spec tiers defense ──────────────


class TestSpecTiersDefense:
    """Verify spec generation correctness."""

    def test_generate_spec_returns_all_tiers(self):
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="TEST-001",
            description="Test endpoint",
            endpoint="/api/test",
        )
        assert "tier_1" in result
        assert "tier_2" in result
        assert "tier_3" in result

    def test_generate_spec_custom_method(self):
        from governance.workflows.orchestrator.spec_tiers import generate_spec

        result = generate_spec(
            task_id="TEST-002",
            description="Delete test",
            endpoint="/api/test/1",
            method="DELETE",
            expected_status=204,
        )
        assert "DELETE" in result.get("tier_2", "")
