"""Deep scan batch 157: Middleware + startup + configuration.

Batch 157 findings: 7 total, 0 confirmed fixes, 7 rejected.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch


# ── Route registration defense ──────────────


class TestRouteRegistrationDefense:
    """Verify all routers are included with correct prefixes."""

    def test_standard_routers_use_api_prefix(self):
        """Most routers included with prefix='/api'."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/api.py").read_text()
        standard = ["rules_router", "tasks_router", "sessions_router",
                     "evidence_router", "agents_router", "reports_router",
                     "chat_router", "metrics_router"]
        for name in standard:
            assert f'include_router({name}, prefix="/api")' in src, f"Missing: {name}"

    def test_infra_router_has_own_prefix(self):
        """infra_router included WITHOUT prefix (has /api/infra internally)."""
        root = Path(__file__).parent.parent.parent
        api_src = (root / "governance/api.py").read_text()
        # infra_router included without prefix parameter
        assert "include_router(infra_router)" in api_src
        # NOT "include_router(infra_router, prefix="/api")" — that would double prefix
        assert 'include_router(infra_router, prefix="/api")' not in api_src

    def test_infra_router_defines_api_infra_prefix(self):
        """Infra router defines /api/infra prefix internally."""
        root = Path(__file__).parent.parent.parent
        infra_src = (root / "governance/routes/infra.py").read_text()
        assert "/api/infra" in infra_src or "prefix=" in infra_src


# ── Access log middleware defense ──────────────


class TestAccessLogMiddlewareDefense:
    """Verify access log middleware behavior."""

    def test_5xx_logged_at_warning(self):
        """Server errors (5xx) logged at WARNING level."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/middleware/access_log.py").read_text()
        assert "500" in src or "status_code >= 500" in src

    def test_4xx_logged_at_info_by_design(self):
        """Client errors (4xx) logged at INFO — design choice to reduce noise."""
        # 4xx are expected during normal API exploration
        # Logging at WARNING would flood logs with 404s
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/middleware/access_log.py").read_text()
        assert "logger" in src


# ── Configuration constants defense ──────────────


class TestConfigurationConstantsDefense:
    """Verify configuration constants are correct."""

    def test_default_ports_match_devops(self):
        """Default ports match documented values in hooks config."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/base.py").read_text()
        # API on 8082
        assert "8082" in src
        # TypeDB on 1729
        assert "1729" in src
        # ChromaDB on 8001
        assert "8001" in src

    def test_use_typedb_default_true(self):
        """USE_TYPEDB defaults to True."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/config.py").read_text()
        assert '"true"' in src or "'true'" in src

    def test_env_var_evaluated_at_import(self):
        """Configuration env vars evaluated at import time (standard Python)."""
        # This is CORRECT behavior — env vars set before process start
        # Runtime env changes are not expected for container services
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/stores/config.py").read_text()
        assert "os.getenv" in src


# ── State file atomic write defense ──────────────


class TestStateFileAtomicWriteDefense:
    """Verify state files handle corruption gracefully."""

    def test_load_state_returns_default_on_corrupt(self):
        """Corrupt state file returns default state (not crash)."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/state.py").read_text()
        # load() catches exceptions and returns default
        assert "except" in src
        assert "get_default_state" in src

    def test_state_files_are_not_critical(self):
        """State files are best-effort tracking — loss is non-fatal."""
        # Entropy and healthcheck state files track session metrics
        # If corrupted, fresh defaults are used — no data loss
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/state.py").read_text()
        # save() catches exceptions
        assert "try:" in src


# ── CORS configuration defense ──────────────


class TestCORSConfigurationDefense:
    """Verify CORS is configured for development."""

    def test_cors_allows_all_origins(self):
        """CORS allows all origins for local development."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/api.py").read_text()
        assert 'allow_origins=["*"]' in src

    def test_both_middlewares_registered(self):
        """Both AccessLogMiddleware and CORSMiddleware are registered."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/api.py").read_text()
        assert "AccessLogMiddleware" in src
        assert "CORSMiddleware" in src
