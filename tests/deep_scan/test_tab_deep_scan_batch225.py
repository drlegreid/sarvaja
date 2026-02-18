"""Batch 225 — Middleware + startup + controllers defense tests.

Validates fixes for:
- BUG-225-STARTUP-001: asyncio.get_running_loop() instead of get_event_loop()
- BUG-225-MW-001: 4xx should be logged at WARNING not INFO
- BUG-225-CTRL-009: agent_sessions cleared on non-200 response
- BUG-225-CTRL-007: backlog loader doesn't set has_error on transient failures
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-225-STARTUP-001: get_running_loop() ──────────────────────────

class TestStartupLoopFix:
    """api_startup.py must use get_running_loop() not get_event_loop()."""

    def test_no_deprecated_get_event_loop(self):
        src = (SRC / "governance/api_startup.py").read_text()
        assert "get_event_loop()" not in src

    def test_uses_get_running_loop(self):
        src = (SRC / "governance/api_startup.py").read_text()
        assert "get_running_loop()" in src


# ── BUG-225-MW-001: 4xx logging level ────────────────────────────────

class TestAccessLog4xxLevel:
    """4xx responses should be logged at WARNING level."""

    def test_4xx_logged_as_warning(self):
        src = (SRC / "governance/middleware/access_log.py").read_text()
        # Find the 4xx block
        idx = src.index("status_code >= 400")
        block = src[idx:idx + 200]
        assert "logger.warning" in block


# ── BUG-225-CTRL-009: agent_sessions stale data ──────────────────────

class TestTrustAgentSessionsClear:
    """select_agent must clear agent_sessions on non-200 response."""

    def test_non_200_clears_agent_sessions(self):
        src = (SRC / "agent/governance_ui/controllers/trust.py").read_text()
        # Search full file — nested function has heavy indentation
        assert "BUG-225-CTRL-009" in src
        # The clearing should happen in both the else and except paths
        count = src.count("state.agent_sessions = []")
        assert count >= 2, f"Expected at least 2 clear points, found {count}"


# ── BUG-225-CTRL-007: backlog loader error handling ───────────────────

class TestBacklogLoaderErrorHandling:
    """load_backlog_data should NOT set has_error on transient failures."""

    def test_no_has_error_in_backlog_exception(self):
        src = (SRC / "agent/governance_ui/controllers/data_loaders.py").read_text()
        backlog_start = src.index("Load backlog failed")
        backlog_section = src[backlog_start:backlog_start + 200]
        # Should NOT set has_error
        assert "state.has_error" not in backlog_section


# ── Middleware module import defense tests ─────────────────────────────

class TestMiddlewareImports:
    """Defense tests for middleware modules."""

    def test_access_log_importable(self):
        from governance.middleware.access_log import AccessLogMiddleware
        assert AccessLogMiddleware is not None

    def test_event_log_importable(self):
        import governance.middleware.event_log
        assert governance.middleware.event_log is not None

    def test_dashboard_log_importable(self):
        import governance.middleware.dashboard_log
        assert governance.middleware.dashboard_log is not None

    def test_middleware_init_importable(self):
        import governance.middleware
        assert governance.middleware is not None


# ── Startup module import defense tests ───────────────────────────────

class TestStartupImports:
    """Defense tests for startup/lifecycle modules."""

    def test_api_importable(self):
        import governance.api
        assert governance.api is not None

    def test_api_startup_importable(self):
        import governance.api_startup
        assert governance.api_startup is not None


# ── Controller module defense tests ───────────────────────────────────

class TestControllerImportDefense:
    """Defense tests for controller modules."""

    def test_trust_controller_importable(self):
        import agent.governance_ui.controllers.trust
        assert agent.governance_ui.controllers.trust is not None

    def test_decisions_controller_importable(self):
        import agent.governance_ui.controllers.decisions
        assert agent.governance_ui.controllers.decisions is not None

    def test_data_loaders_importable(self):
        import agent.governance_ui.controllers.data_loaders
        assert agent.governance_ui.controllers.data_loaders is not None

    def test_infra_loaders_importable(self):
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        assert callable(register_infra_loader_controllers)
