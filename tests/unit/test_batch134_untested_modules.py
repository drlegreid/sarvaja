"""Batch 134: Unit tests for 4 previously untested modules."""
import sys, subprocess
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
import pytest

from governance.routes.reports import _generate_recommendations, _generate_objectives
from governance.routes.infra import (
    CONTAINER_NAMES, _find_socket, _fetch_logs_subprocess, _fetch_own_process_logs,
)
from governance.services.projects import (
    create_project, get_project, list_projects, delete_project,
    link_session_to_project, _projects_store,
)
sys.modules.setdefault("governance.client", MagicMock())
from agent.orchestrator.engine_models import AgentRole, AgentInfo
from agent.orchestrator.engine import OrchestratorEngine

_R, _I, _P = "governance.routes.reports", "governance.routes.infra", "governance.services.projects"

def _engine():
    return OrchestratorEngine(MagicMock())

def _agent(aid="A1", role=AgentRole.CODING, trust=0.9, status="AVAILABLE"):
    return AgentInfo(agent_id=aid, name="T", role=role, trust_score=trust, status=status)

def _rpt(tasks=None, agents=None, client_rv=None):
    s = ExitStack()
    s.enter_context(patch(f"{_R}.get_typedb_client", return_value=client_rv))
    s.enter_context(patch(f"{_R}._sessions_store", {}))
    s.enter_context(patch(f"{_R}._tasks_store", tasks or {}))
    s.enter_context(patch(f"{_R}._agents_store", agents or {}))
    return s

# ── Module 1: reports.py ─────────────────────────────────────────────────
class TestRecommendations:
    def test_high_pending(self): assert "prioritizing backlog" in _generate_recommendations(15, 0.9, 25)
    def test_low_trust(self): assert "trust scores" in _generate_recommendations(5, 0.5, 25)
    def test_few_rules(self): assert "governance rules" in _generate_recommendations(5, 0.9, 10)
    def test_all_bad(self):
        r = _generate_recommendations(20, 0.3, 5)
        assert "backlog" in r and "trust" in r and "rules" in r
    def test_all_good(self): assert "normal parameters" in _generate_recommendations(5, 0.9, 25)
    def test_period(self): assert _generate_recommendations(5, 0.9, 25).endswith(".")
    def test_boundary_10(self): assert "backlog" not in _generate_recommendations(10, 0.9, 25)
    def test_boundary_07(self): assert "trust" not in _generate_recommendations(5, 0.7, 25)
    def test_boundary_20(self): assert "governance rules" not in _generate_recommendations(5, 0.9, 20)

class TestObjectives:
    def test_pending(self): assert "Complete top 3" in _generate_objectives(5, 0)
    def test_fewer_3(self): assert "Complete top 2" in _generate_objectives(2, 0)
    def test_no_pending(self): assert "Complete top" not in _generate_objectives(0, 0)
    def test_dsp(self): assert "DSP cycle" in _generate_objectives(0, 0)
    def test_archive(self): assert "Archive" in _generate_objectives(0, 10)
    def test_no_archive(self): assert "Archive" not in _generate_objectives(0, 3)
    def test_boundary_5(self): assert "Archive" not in _generate_objectives(0, 5)
    def test_period(self): assert _generate_objectives(3, 8).endswith(".")
    def test_evidence(self):
        r = _generate_objectives(0, 0)
        assert "evidence" in r.lower() or "SESSION-EVID" in r

class TestExecutiveReport:
    def _gen(self):
        from governance.routes.reports import _generate_executive_report
        return _generate_executive_report

    def test_no_args_today(self):
        from datetime import datetime
        with _rpt():
            assert self._gen()().period == datetime.now().strftime("%Y-%m-%d")
    def test_session_period(self):
        with _rpt(): assert self._gen()(session_id="S-X").period == "S-X"
    def test_date_range(self):
        with _rpt():
            assert self._gen()(start_date="2026-01-01", end_date="2026-01-31").period == "2026-01-01 to 2026-01-31"
    def test_7_sections(self):
        with _rpt(): assert len(self._gen()().sections) == 7
    def test_healthy(self):
        with _rpt({"t1": {"status": "DONE"}, "t2": {"status": "DONE"}},
                  {"a1": {"trust_score": 0.9, "status": "ACTIVE", "tasks_executed": 5}}):
            assert self._gen()().overall_status == "healthy"
    def test_warning(self):
        with _rpt({"t1": {"status": "TODO"}, "t2": {"status": "TODO"}},
                  {"a1": {"trust_score": 0.6, "status": "ACTIVE", "tasks_executed": 0}}):
            assert self._gen()().overall_status == "warning"
    def test_critical(self):
        with _rpt({"t1": {"status": "TODO"}, "t2": {"status": "TODO"}},
                  {"a1": {"trust_score": 0.4, "status": "X", "tasks_executed": 0}}):
            assert self._gen()().overall_status == "critical"
    def test_compliance_rate(self):
        c = MagicMock(); c.get_all_rules.return_value = [MagicMock(status="ACTIVE"), MagicMock(status="X")]
        with _rpt(client_rv=c):
            assert self._gen()().metrics_summary["compliance_rate"] == 50.0

class TestReportRoutes:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient; from governance.api import app
        return TestClient(app)
    def test_get_executive(self, client):
        with _rpt():
            r = client.get("/api/reports/executive")
            assert r.status_code == 200 and "sections" in r.json()
    def test_session_404(self, client):
        with _rpt():
            assert client.get("/api/reports/executive/sessions/NONEXIST").status_code == 404

# ── Module 2: infra.py ──────────────────────────────────────────────────
class TestContainerNames:
    def test_count(self): assert len(CONTAINER_NAMES) == 6
    def test_keys(self):
        for k in ("dashboard", "typedb", "chromadb", "litellm", "ollama", "agents"):
            assert k in CONTAINER_NAMES

class TestFindSocket:
    @patch(f"{_I}.os.path.isdir", return_value=False)
    @patch(f"{_I}.os.path.exists", return_value=False)
    def test_none(self, *_): assert _find_socket() is None
    @patch(f"{_I}.os.path.isdir", return_value=False)
    @patch(f"{_I}.os.path.exists", side_effect=lambda p: p == "/run/podman/podman.sock")
    def test_first(self, *_): assert _find_socket() == "/run/podman/podman.sock"
    @patch(f"{_I}.os.path.isdir", return_value=True)
    @patch(f"{_I}.os.path.exists", return_value=True)
    def test_skip_dir(self, *_): assert _find_socket() is None

class TestFetchLogsSub:
    @patch(f"{_I}.subprocess.run")
    def test_stdout(self, m):
        m.return_value = MagicMock(stdout="a\nb", stderr=""); assert "a" in _fetch_logs_subprocess("c", 50)
    @patch(f"{_I}.subprocess.run")
    def test_stderr(self, m):
        m.return_value = MagicMock(stdout="", stderr="e1\ne2"); assert "e1" in _fetch_logs_subprocess("c", 50)
    @patch(f"{_I}.subprocess.run", side_effect=FileNotFoundError)
    def test_fnf(self, _): assert _fetch_logs_subprocess("c", 50) == []
    @patch(f"{_I}.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 10))
    def test_timeout(self, _): assert any("Timeout" in l for l in _fetch_logs_subprocess("c", 50))
    @patch(f"{_I}.subprocess.run")
    def test_empty(self, m):
        m.return_value = MagicMock(stdout="", stderr="")
        assert _fetch_logs_subprocess("c", 50) == ["No log output from container"]
    @patch(f"{_I}.subprocess.run", side_effect=RuntimeError("x"))
    def test_generic(self, _): assert any("CLI fallback" in l for l in _fetch_logs_subprocess("c", 50))

class TestOwnProcessLogs:
    @patch(f"{_I}.subprocess.run")
    def test_python(self, m):
        m.return_value = MagicMock(stdout="PID USER\n1 root python3 x")
        assert any("python" in l.lower() for l in _fetch_own_process_logs(100))
    @patch(f"{_I}.subprocess.run", side_effect=Exception)
    def test_fallback(self, _): assert any("container" in l.lower() for l in _fetch_own_process_logs(50))
    @patch(f"{_I}.subprocess.run")
    def test_tail(self, m):
        m.return_value = MagicMock(stdout="PID\n" + "\n".join(f"l{i}" for i in range(20)))
        assert len(_fetch_own_process_logs(5)) <= 5

class TestInfraRoutes:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient; from governance.api import app
        return TestClient(app)
    def test_list(self, client): assert client.get("/api/infra/containers").status_code == 200
    @patch(f"{_I}._find_socket", return_value=None)
    @patch(f"{_I}._fetch_logs_subprocess", return_value=[])
    @patch(f"{_I}._fetch_own_process_logs", return_value=["x"])
    def test_fallback(self, _a, _b, _c, client):
        r = client.get("/api/infra/logs?container=dashboard")
        assert r.status_code == 200 and r.json()["source"] == "process-info"

# ── Module 3: projects.py ───────────────────────────────────────────────
class TestCreateProject:
    def setup_method(self): _projects_store.clear()
    @patch(f"{_P}._get_client", return_value=None)
    def test_auto_id(self, _): assert create_project(name="My Project")["project_id"].startswith("PROJ-")
    @patch(f"{_P}._get_client", return_value=None)
    def test_provided_id(self, _): assert create_project(project_id="PROJ-C", name="X")["project_id"] == "PROJ-C"
    @patch(f"{_P}._get_client")
    def test_typedb_ok(self, m):
        m.return_value = MagicMock(); m.return_value.insert_project.return_value = {"project_id": "P"}
        assert create_project(project_id="P")["project_id"] == "P"; assert "P" not in _projects_store
    @patch(f"{_P}._get_client")
    def test_typedb_fail(self, m):
        m.return_value = MagicMock(); m.return_value.insert_project.side_effect = Exception("e")
        assert create_project(project_id="PF", name="F")["project_id"] == "PF"; assert "PF" in _projects_store
    @patch(f"{_P}._get_client", return_value=None)
    def test_in_memory(self, _): create_project(project_id="PM", name="M"); assert "PM" in _projects_store

class TestGetProject:
    def setup_method(self): _projects_store.clear()
    @patch(f"{_P}._get_client")
    def test_enriched(self, m):
        c = MagicMock(); c.get_project.return_value = {"project_id": "P1"}
        c.get_project_sessions.return_value = ["s1", "s2"]; c.get_project_plans.return_value = ["p"]
        m.return_value = c; r = get_project("P1")
        assert r["session_count"] == 2 and r["plan_count"] == 1
    @patch(f"{_P}._get_client")
    def test_enrichment_fail(self, m):
        c = MagicMock(); c.get_project.return_value = {"project_id": "P1"}
        c.get_project_sessions.side_effect = Exception; c.get_project_plans.side_effect = Exception
        m.return_value = c; assert get_project("P1")["session_count"] == 0
    @patch(f"{_P}._get_client", return_value=None)
    def test_fallback(self, _):
        _projects_store["P2"] = {"project_id": "P2"}; assert get_project("P2")["project_id"] == "P2"
    @patch(f"{_P}._get_client", return_value=None)
    def test_not_found(self, _): assert get_project("X") is None
    @patch(f"{_P}._get_client")
    def test_typedb_fail(self, m):
        m.return_value = MagicMock(); m.return_value.get_project.side_effect = Exception
        _projects_store["P3"] = {"project_id": "P3"}; assert get_project("P3")["project_id"] == "P3"

class TestListProjects:
    def setup_method(self): _projects_store.clear()
    @patch(f"{_P}._get_client")
    def test_typedb_ok(self, m):
        c = MagicMock(); c.list_projects.return_value = [{"project_id": "P"}]
        c.get_project_sessions.return_value = []; c.get_project_plans.return_value = []
        m.return_value = c; assert len(list_projects()["items"]) == 1
    @patch(f"{_P}._get_client", return_value=None)
    def test_pagination(self, _):
        for i in range(5): _projects_store[f"P{i}"] = {"project_id": f"P{i}"}
        r = list_projects(limit=2, offset=1); assert len(r["items"]) == 2
    @patch(f"{_P}._get_client", return_value=None)
    def test_empty(self, _): assert list_projects()["items"] == []
    @patch(f"{_P}._get_client")
    def test_typedb_fail(self, m):
        m.return_value = MagicMock(); m.return_value.list_projects.side_effect = Exception
        _projects_store["X"] = {"project_id": "X"}; assert len(list_projects()["items"]) == 1

class TestDeleteProject:
    def setup_method(self): _projects_store.clear()
    @patch(f"{_P}._get_client")
    def test_typedb_ok(self, m):
        m.return_value = MagicMock(); m.return_value.delete_project.return_value = True
        assert delete_project("P") is True
    @patch(f"{_P}._get_client", return_value=None)
    def test_exists(self, _):
        _projects_store["P"] = {}; assert delete_project("P") is True; assert "P" not in _projects_store
    @patch(f"{_P}._get_client", return_value=None)
    def test_not_exists(self, _): assert delete_project("X") is False
    @patch(f"{_P}._get_client")
    def test_typedb_fail(self, m):
        m.return_value = MagicMock(); m.return_value.delete_project.side_effect = Exception
        _projects_store["P"] = {}; assert delete_project("P") is True

class TestLinkSession:
    @patch(f"{_P}._get_client")
    def test_ok(self, m):
        m.return_value = MagicMock(); m.return_value.link_project_to_session.return_value = True
        assert link_session_to_project("P", "S") is True
    @patch(f"{_P}._get_client", return_value=None)
    def test_no_client(self, _): assert link_session_to_project("P", "S") is False
    @patch(f"{_P}._get_client")
    def test_exception(self, m):
        m.return_value = MagicMock(); m.return_value.link_project_to_session.side_effect = Exception
        assert link_session_to_project("P", "S") is False

# ── Module 4: engine.py ─────────────────────────────────────────────────
class TestEngineCore:
    def test_init_defaults(self):
        e = _engine(); assert not e._running and e._dispatch_count == 0 and e._started_at is None
    def test_init_custom(self): assert OrchestratorEngine(MagicMock(), max_queue_size=50)._queue._max_size == 50
    def test_not_running(self): assert not _engine().is_running
    def test_running(self): e = _engine(); e._running = True; assert e.is_running
    def test_stats_dict(self): assert isinstance(_engine().stats, dict)
    def test_stats_keys(self):
        for k in ("running", "dispatch_count", "agents_registered", "agents_available"):
            assert k in _engine().stats
    def test_stats_started_none(self): assert _engine().stats["started_at"] is None
    def test_stats_agent_counts(self):
        e = _engine(); e.register_agent(_agent())
        assert e.stats["agents_registered"] == 1 and e.stats["agents_available"] == 1

class TestEngineAgents:
    def test_register_ok(self): e = _engine(); assert e.register_agent(_agent()) is True
    def test_register_dup(self):
        e = _engine(); e.register_agent(_agent("A1")); assert e.register_agent(_agent("A1")) is False
    def test_register_multi(self):
        e = _engine(); e.register_agent(_agent("A1")); e.register_agent(_agent("A2"))
        assert len(e._agents) == 2
    def test_unregister_exists(self):
        e = _engine(); e.register_agent(_agent("A1"))
        assert e.unregister_agent("A1") is True and "A1" not in e._agents
    def test_unregister_missing(self): assert _engine().unregister_agent("X") is False
    def test_get_found(self):
        e = _engine(); e.register_agent(_agent("A1")); assert e.get_agent("A1").agent_id == "A1"
    def test_get_none(self): assert _engine().get_agent("X") is None
    def test_available_filter(self):
        e = _engine(); e.register_agent(_agent("A1")); e.register_agent(_agent("A2", status="BUSY"))
        assert len(e.get_available_agents()) == 1
    def test_available_role(self):
        e = _engine(); e.register_agent(_agent("A1", role=AgentRole.CODING))
        e.register_agent(_agent("A2", role=AgentRole.SYNC))
        assert len(e.get_available_agents(role=AgentRole.CODING)) == 1
    def test_available_none(self):
        e = _engine(); e.register_agent(_agent("A1", status="BUSY")); assert e.get_available_agents() == []
    def test_available_no_role(self):
        e = _engine(); e.register_agent(_agent("A1", role=AgentRole.CODING))
        assert e.get_available_agents(role=AgentRole.RESEARCH) == []
