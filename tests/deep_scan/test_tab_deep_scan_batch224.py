"""Batch 224 — API routes defense tests.

Validates fixes for:
- BUG-224-RULES-001: /rules/dependencies/overview must be before /{rule_id}
- BUG-224-AGENT-001: toggle_agent_status and record_agent_task need try/except
- BUG-224-AGENT-002: get_agent_sessions needs try/except
- BUG-224-TASK-003: get_task_sessions TOCTOU fix (existence check first)
- BUG-224-OBS-001: summary["alerts"] KeyError guard
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-224-RULES-001: Route ordering ────────────────────────────────

class TestRulesRouteOrdering:
    """Static /rules/dependencies/overview must be registered before /{rule_id}."""

    def test_dependency_overview_before_rule_id(self):
        src = (SRC / "governance/routes/rules/crud.py").read_text()
        # dependencies/overview must appear BEFORE {rule_id}
        dep_pos = src.index('"/rules/dependencies/overview"')
        rule_pos = src.index('"/rules/{rule_id}"')
        assert dep_pos < rule_pos, "Static route must be registered before dynamic route"


# ── BUG-224-AGENT-001: Exception handling ─────────────────────────────

class TestAgentEndpointExceptionHandling:
    """toggle_agent_status and record_agent_task must have try/except."""

    def test_toggle_has_try_except(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        # Find the toggle function and verify it has exception handling
        toggle_start = src.index("def toggle_agent_status")
        toggle_section = src[toggle_start:toggle_start + 500]
        assert "except HTTPException:" in toggle_section
        assert "except Exception as e:" in toggle_section

    def test_record_task_has_try_except(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        record_start = src.index("def record_agent_task")
        record_section = src[record_start:record_start + 500]
        assert "except HTTPException:" in record_section
        assert "except Exception as e:" in record_section


# ── BUG-224-AGENT-002: Agent sessions exception handling ──────────────

class TestAgentSessionsExceptionHandling:
    """get_agent_sessions must have try/except."""

    def test_agent_sessions_has_try_except(self):
        src = (SRC / "governance/routes/agents/crud.py").read_text()
        fn_start = src.index("def get_agent_sessions")
        fn_section = src[fn_start:fn_start + 1200]
        assert "except HTTPException:" in fn_section
        assert "except Exception as e:" in fn_section


# ── BUG-224-TASK-003: TOCTOU fix ─────────────────────────────────────

class TestTaskSessionsToctouFix:
    """get_task_sessions must check existence BEFORE fetching sessions."""

    def test_existence_check_before_sessions_fetch(self):
        src = (SRC / "governance/routes/tasks/crud.py").read_text()
        fn_start = src.index("def get_task_sessions")
        fn_section = src[fn_start:fn_start + 500]
        # get_task should appear before get_sessions_for_task
        existence_pos = fn_section.index("get_task(task_id)")
        sessions_pos = fn_section.index("get_sessions_for_task")
        assert existence_pos < sessions_pos


# ── BUG-224-OBS-001: Alerts KeyError guard ────────────────────────────

class TestObservabilityAlertsGuard:
    """summary['alerts'] must use .get() guard."""

    def test_alerts_uses_get(self):
        src = (SRC / "governance/routes/agents/observability.py").read_text()
        assert 'summary.get("alerts", [])' in src


# ── Route module import defense tests ─────────────────────────────────

class TestRouteModuleImports:
    """Defense tests for route modules."""

    def test_rules_crud_importable(self):
        import governance.routes.rules.crud
        assert governance.routes.rules.crud is not None

    def test_agents_crud_importable(self):
        import governance.routes.agents.crud
        assert governance.routes.agents.crud is not None

    def test_agents_observability_importable(self):
        import governance.routes.agents.observability
        assert governance.routes.agents.observability is not None

    def test_agents_visibility_importable(self):
        import governance.routes.agents.visibility
        assert governance.routes.agents.visibility is not None

    def test_agents_helpers_importable(self):
        from governance.routes.agents.helpers import build_agent_relations_lookup
        assert callable(build_agent_relations_lookup)

    def test_tasks_crud_importable(self):
        import governance.routes.tasks.crud
        assert governance.routes.tasks.crud is not None

    def test_proposals_importable(self):
        import governance.routes.proposals
        assert governance.routes.proposals is not None

    def test_audit_importable(self):
        import governance.routes.audit
        assert governance.routes.audit is not None

    def test_evidence_importable(self):
        import governance.routes.evidence
        assert governance.routes.evidence is not None

    def test_reports_importable(self):
        import governance.routes.reports
        assert governance.routes.reports is not None

    def test_metrics_importable(self):
        import governance.routes.metrics
        assert governance.routes.metrics is not None

    def test_infra_importable(self):
        import governance.routes.infra
        assert governance.routes.infra is not None

    def test_files_importable(self):
        import governance.routes.files
        assert governance.routes.files is not None
