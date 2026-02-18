"""Batch 135: Controllers + Routes — 4 modules, ~60 tests. DOC-SIZE-01-v1."""
import unittest
from unittest.mock import patch, MagicMock
_D = "governance.routes.sessions.detail"
_I = "agent.governance_ui.controllers.infra"
_T = "agent.governance_ui.controllers.tests"
_B = "agent.governance_ui.controllers.backlog"

def _ctrl():
    c, t = MagicMock(), {}
    def trig(name):
        def dec(fn):
            t[name] = fn
            return fn
        return dec
    c.trigger = trig
    return c, t

def _hc(data, status=200):
    m = MagicMock()
    m.__enter__ = MagicMock(return_value=m)
    m.__exit__ = MagicMock(return_value=False)
    r = MagicMock(status_code=status, text="err")
    r.json.return_value = data
    m.get.return_value = m.post.return_value = m.put.return_value = r
    return m

class TestDetail(unittest.TestCase):
    """Module 1: governance/routes/sessions/detail.py endpoints."""
    def _c(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from governance.routes.sessions.detail import router
        a = FastAPI(); a.include_router(router, prefix="/api")
        return TestClient(a)

    @patch(f"{_D}.get_session_detail", return_value={"zoom": 1})
    def test_detail_ok(self, _): self.assertEqual(self._c().get("/api/sessions/S1/detail?zoom=1").json()["zoom"], 1)
    @patch(f"{_D}.get_session_detail", return_value=None)
    def test_detail_404(self, _): self.assertEqual(self._c().get("/api/sessions/S1/detail").status_code, 404)
    @patch(f"{_D}.get_session_detail", return_value={"tool_calls": [{"t": 1}], "tool_calls_total": 1})
    def test_tools_ok(self, _):
        r = self._c().get("/api/sessions/S1/tools?page=1")
        self.assertEqual(len(r.json()["tool_calls"]), 1)
    @patch(f"{_D}.get_session_detail", return_value=None)
    def test_tools_404(self, _): self.assertEqual(self._c().get("/api/sessions/S1/tools").status_code, 404)
    @patch(f"{_D}.get_session_detail", return_value={"thinking_blocks": [{"b": 1}], "thinking_blocks_total": 1})
    def test_thoughts_ok(self, _): self.assertEqual(self._c().get("/api/sessions/S1/thoughts").json()["total"], 1)
    @patch(f"{_D}.get_session_detail", return_value=None)
    def test_thoughts_404(self, _): self.assertEqual(self._c().get("/api/sessions/S1/thoughts").status_code, 404)
    @patch(f"{_D}.render_markdown", return_value="<h1>Hi</h1>")
    @patch("governance.services.sessions.get_session")
    def test_evidence_ok(self, gs, _):
        import os as _os
        # Use the actual project evidence dir to pass the traversal check
        detail_file = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "governance", "routes", "sessions", "detail.py"))
        _this_dir = _os.path.dirname(detail_file)
        project_root = _os.path.realpath(_os.path.join(_this_dir, "..", "..", ".."))
        evidence_dir = _os.path.join(project_root, "evidence")
        file_path = _os.path.join(evidence_dir, "test_evidence_ok.md")
        gs.return_value = {"file_path": file_path}
        with patch("pathlib.Path") as mp:
            i = MagicMock(); i.exists.return_value = True; i.read_text.return_value = "# Hi"; i.stat.return_value = MagicMock(st_size=100)
            mp.return_value = i
            self.assertIn("html", self._c().get("/api/sessions/S1/evidence/rendered").json())
    @patch("governance.services.sessions.get_session", return_value=None)
    def test_evidence_no_sess(self, _): self.assertEqual(self._c().get("/api/sessions/S1/evidence/rendered").status_code, 404)
    @patch("governance.services.sessions.get_session", return_value={"file_path": None})
    def test_evidence_no_path(self, _): self.assertEqual(self._c().get("/api/sessions/S1/evidence/rendered").status_code, 404)
    @patch("governance.services.sessions.get_session")
    def test_evidence_gone(self, gs):
        import os as _os
        detail_file = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "governance", "routes", "sessions", "detail.py"))
        _this_dir = _os.path.dirname(detail_file)
        project_root = _os.path.realpath(_os.path.join(_this_dir, "..", "..", ".."))
        evidence_dir = _os.path.join(project_root, "evidence")
        file_path = _os.path.join(evidence_dir, "nonexistent_evidence.md")
        gs.return_value = {"file_path": file_path}
        with patch("pathlib.Path") as mp:
            mp.return_value.exists.return_value = False
            self.assertEqual(self._c().get("/api/sessions/S1/evidence/rendered").status_code, 404)
    @patch(f"{_D}.get_session_detail", return_value={"tool_calls": [], "tool_calls_total": 0})
    def test_tools_paging(self, m):
        self._c().get("/api/sessions/S1/tools?page=2&per_page=5")
        m.assert_called_with("S1", zoom=2, page=2, per_page=5)
    @patch(f"{_D}.get_session_detail", return_value={"thinking_blocks": [], "thinking_blocks_total": 0})
    def test_thoughts_paging(self, m):
        self._c().get("/api/sessions/S1/thoughts?page=3&per_page=10")
        m.assert_called_with("S1", zoom=3, page=3, per_page=10)
    @patch(f"{_D}.get_session_detail", return_value={"zoom": 0})
    def test_detail_zoom0(self, _): self.assertEqual(self._c().get("/api/sessions/S1/detail?zoom=0").status_code, 200)
    @patch(f"{_D}.get_session_detail", return_value={"zoom": 3})
    def test_detail_zoom3(self, _): self.assertEqual(self._c().get("/api/sessions/S1/detail?zoom=3").status_code, 200)
    @patch(f"{_D}.render_markdown", return_value="<p>x</p>")
    @patch("governance.services.sessions.get_session")
    def test_evidence_has_raw(self, gs, _):
        import os as _os
        detail_file = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "governance", "routes", "sessions", "detail.py"))
        _this_dir = _os.path.dirname(detail_file)
        project_root = _os.path.realpath(_os.path.join(_this_dir, "..", "..", ".."))
        evidence_dir = _os.path.join(project_root, "evidence")
        file_path = _os.path.join(evidence_dir, "test_raw.md")
        gs.return_value = {"file_path": file_path}
        with patch("pathlib.Path") as mp:
            i = MagicMock(); i.exists.return_value = True; i.read_text.return_value = "x"; i.stat.return_value = MagicMock(st_size=50)
            mp.return_value = i
            self.assertIn("raw", self._c().get("/api/sessions/S1/evidence/rendered").json())

class TestInfra(unittest.TestCase):
    """Module 2: agent/governance_ui/controllers/infra.py functions."""
    @patch(f"{_I}.os.path.exists", return_value=False)
    def test_not_container(self, _):
        from agent.governance_ui.controllers.infra import is_in_container
        self.assertFalse(is_in_container())
    @patch(f"{_I}.os.path.exists", side_effect=lambda p: p == "/.dockerenv")
    def test_docker(self, _):
        from agent.governance_ui.controllers.infra import is_in_container
        self.assertTrue(is_in_container())
    @patch(f"{_I}.os.path.exists", side_effect=lambda p: p == "/run/.containerenv")
    def test_podman_env(self, _):
        from agent.governance_ui.controllers.infra import is_in_container
        self.assertTrue(is_in_container())
    @patch(f"{_I}.socket.socket")
    def test_port_open(self, ms):
        ms.return_value.connect_ex.return_value = 0
        from agent.governance_ui.controllers.infra import check_port
        self.assertTrue(check_port("localhost", 1729))
    @patch(f"{_I}.socket.socket")
    def test_port_closed(self, ms):
        ms.return_value.connect_ex.return_value = 1
        from agent.governance_ui.controllers.infra import check_port
        self.assertFalse(check_port("localhost", 9999))
    @patch(f"{_I}.socket.socket", side_effect=OSError)
    def test_port_err(self, _):
        from agent.governance_ui.controllers.infra import check_port
        self.assertFalse(check_port("localhost", 1729))
    @patch(f"{_I}.is_in_container", return_value=True)
    def test_podman_in_container(self, _):
        from agent.governance_ui.controllers.infra import check_podman_health
        self.assertTrue(check_podman_health())
    @patch(f"{_I}.is_in_container", return_value=False)
    @patch(f"{_I}.subprocess.run", return_value=MagicMock(returncode=0))
    def test_podman_ok(self, *_):
        from agent.governance_ui.controllers.infra import check_podman_health
        self.assertTrue(check_podman_health())
    @patch(f"{_I}.is_in_container", return_value=False)
    @patch(f"{_I}.subprocess.run", return_value=MagicMock(returncode=1))
    def test_podman_fail(self, *_):
        from agent.governance_ui.controllers.infra import check_podman_health
        self.assertFalse(check_podman_health())
    @patch(f"{_I}.check_podman_health", return_value=True)
    def test_svc_podman(self, _):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertEqual(check_service_health("podman")["status"], "OK")
    def test_svc_unknown(self):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertEqual(check_service_health("nope")["status"], "UNKNOWN")
    @patch(f"{_I}.check_port", return_value=False)
    @patch(f"{_I}.is_in_container", return_value=False)
    def test_required_down(self, *_):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertEqual(check_service_health("typedb")["status"], "DOWN")
    @patch(f"{_I}.check_port", return_value=False)
    @patch(f"{_I}.is_in_container", return_value=False)
    def test_optional_off(self, *_):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertEqual(check_service_health("ollama")["status"], "OFF")
    @patch(f"{_I}.check_port", return_value=True)
    @patch(f"{_I}.is_in_container", return_value=False)
    def test_svc_up(self, *_):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertEqual(check_service_health("typedb")["status"], "OK")
    @patch(f"{_I}.check_service_health", return_value={"status": "OK", "ok": True})
    def test_all_services(self, _):
        from agent.governance_ui.controllers.infra import check_all_services, SERVICE_CONFIG
        r = check_all_services()
        self.assertIn("podman", r)
        for k in SERVICE_CONFIG: self.assertIn(k, r)
    def test_mcp_none(self):
        from agent.governance_ui.controllers.infra import get_mcp_server_status, MCP_SERVERS
        r = get_mcp_server_status(None)
        for n in MCP_SERVERS: self.assertEqual(r[n], "ON-DEMAND")
    def test_mcp_components(self):
        from agent.governance_ui.controllers.infra import get_mcp_server_status
        r = get_mcp_server_status({"components": {"gov-core": "OK"}})
        self.assertEqual(r["gov-core"], "OK"); self.assertEqual(r["claude-mem"], "ON-DEMAND")
    def test_constants(self):
        from agent.governance_ui.controllers.infra import MCP_SERVERS, SERVICE_CONFIG, REQUIRED_SERVICES
        self.assertIn("gov-core", MCP_SERVERS); self.assertIn("typedb", SERVICE_CONFIG)
        self.assertTrue(REQUIRED_SERVICES.issubset(set(SERVICE_CONFIG.keys())))
    def test_dsp_no_dir(self):
        from agent.governance_ui.controllers.infra import check_dsp_conditions
        p = MagicMock(); p.exists.return_value = False
        self.assertFalse(check_dsp_conditions(p)["dsp_suggested"])
    def test_dsp_suggested(self):
        from agent.governance_ui.controllers.infra import check_dsp_conditions
        p = MagicMock(); p.exists.return_value = True
        p.glob.side_effect = lambda pat: [MagicMock()] * 25 if "SESSION-" in pat else []
        self.assertTrue(check_dsp_conditions(p)["dsp_suggested"])
    def test_dsp_recent(self):
        from agent.governance_ui.controllers.infra import check_dsp_conditions
        from datetime import datetime
        p = MagicMock(); p.exists.return_value = True; now = datetime.now()
        df = MagicMock(); df.name = f"SESSION-{now.year}-{now.month:02d}-{now.day:02d}-DSP.md"
        p.glob.side_effect = lambda pat: [MagicMock()] * 5 if "SESSION-" in pat else [df]
        self.assertFalse(check_dsp_conditions(p)["dsp_suggested"])
    @patch(f"{_I}.check_port", return_value=True)
    @patch(f"{_I}.is_in_container", return_value=True)
    def test_svc_in_container_uses_container_host(self, *_):
        from agent.governance_ui.controllers.infra import check_service_health
        self.assertTrue(check_service_health("chromadb")["ok"])


class TestTestsCtrl(unittest.TestCase):
    """Module 3: agent/governance_ui/controllers/tests.py triggers."""
    def _reg(self):
        s = MagicMock(); c, t = _ctrl()
        with patch(f"{_T}.add_api_trace"), patch(f"{_T}.add_error_trace"):
            from agent.governance_ui.controllers.tests import register_tests_controllers
            r = register_tests_controllers(s, c, "http://t:8082")
        return s, t, r

    def test_returns_key(self):
        self.assertIn("load_tests_data", self._reg()[2])
    @patch(f"{_T}.add_api_trace")
    @patch(f"{_T}.httpx.Client")
    def test_load_results(self, mc, _):
        mc.return_value = _hc({"runs": [{"run_id": "R1"}]})
        s, t, _ = self._reg(); mc.return_value = _hc({"runs": [{"run_id": "R1"}]})
        t["load_test_results"](); self.assertFalse(s.tests_loading)
    @patch(f"{_T}.add_error_trace")
    @patch(f"{_T}.httpx.Client", side_effect=Exception("x"))
    def test_load_results_err(self, *_):
        s, t, _ = self._reg(); t["load_test_results"]()
        self.assertEqual(s.tests_recent_runs, [])
    @patch(f"{_T}.add_api_trace")
    @patch(f"{_T}.threading.Thread")
    @patch(f"{_T}.httpx.Client")
    def test_run(self, mc, mt, _):
        mc.return_value = _hc({"run_id": "R1"})
        s, t, _ = self._reg(); mc.return_value = _hc({"run_id": "R1"})
        t["run_tests"](); self.assertTrue(s.tests_running)
    @patch(f"{_T}.add_api_trace")
    @patch(f"{_T}.httpx.Client")
    def test_view_run(self, mc, _):
        mc.return_value = _hc({"run_id": "R1", "status": "done"})
        _, t, _ = self._reg(); mc.return_value = _hc({"run_id": "R1", "status": "done"})
        t["view_test_run"]("R1")
    def test_regression_exists(self): self.assertIn("run_regression", self._reg()[1])
    def test_regression_static_exists(self): self.assertIn("run_regression_static", self._reg()[1])
    @patch(f"{_T}.add_api_trace")
    @patch(f"{_T}.httpx.Client")
    def test_robot_summary(self, mc, _):
        mc.return_value = _hc({"available": True})
        _, t, _ = self._reg(); mc.return_value = _hc({"available": True})
        t["load_robot_summary"]()
    def test_all_triggers_registered(self):
        _, t, _ = self._reg()
        for k in ("load_test_results", "run_tests", "view_test_run", "run_regression",
                   "run_regression_static", "load_robot_summary"):
            self.assertIn(k, t)


class TestBacklogCtrl(unittest.TestCase):
    """Module 4: agent/governance_ui/controllers/backlog.py triggers."""
    def _reg(self):
        s = MagicMock(); s.backlog_auto_refresh = False
        s.tasks_agent_id = "code-agent"; s.backlog_agent_id = "code-agent"
        c, t = _ctrl(); lf = MagicMock()
        from agent.governance_ui.controllers.backlog import register_backlog_controllers
        register_backlog_controllers(s, c, "http://t:8082", lf)
        return s, t, lf

    @patch(f"{_B}.httpx.Client")
    def test_claim_ok(self, mc):
        mc.return_value = _hc({})
        s, t, lf = self._reg(); mc.return_value = _hc({})
        t["claim_task"]("T1"); self.assertEqual(s.status_message, "Task T1 claimed successfully"); lf.assert_called()
    def test_claim_no_agent(self):
        s, t, _ = self._reg(); s.tasks_agent_id = ""; s.backlog_agent_id = ""
        t["claim_task"]("T1"); self.assertTrue(s.has_error)
    @patch(f"{_B}.httpx.Client", side_effect=Exception("x"))
    def test_claim_err(self, _):
        s, t, _ = self._reg(); t["claim_task"]("T1"); self.assertTrue(s.has_error)
    @patch(f"{_B}.httpx.Client")
    def test_complete_ok(self, mc):
        m = _hc({}); tr = MagicMock(status_code=200)
        tr.json.return_value = {"items": [{"id": "T1"}], "pagination": {}}
        m.get.return_value = tr; mc.return_value = m
        s, t, lf = self._reg(); mc.return_value = m
        t["complete_task"]("T1"); self.assertEqual(s.status_message, "Task T1 completed successfully"); lf.assert_called()
    @patch(f"{_B}.httpx.Client", side_effect=Exception("x"))
    def test_complete_err(self, _):
        s, t, _ = self._reg(); t["complete_task"]("T1"); self.assertTrue(s.has_error)
    def test_toggle(self):
        s, t, _ = self._reg(); s.backlog_auto_refresh = False
        with patch(f"{_B}.asyncio.get_event_loop") as ml:
            ml.return_value.create_task.return_value = MagicMock(done=lambda: False)
            t["toggle_backlog_auto_refresh"]()
        self.assertTrue(s.backlog_auto_refresh)
    def test_compat_triggers(self):
        _, t, _ = self._reg()
        self.assertIn("claim_backlog_task", t); self.assertIn("complete_backlog_task", t)
    @patch(f"{_B}.httpx.Client")
    def test_claim_sets_loading(self, mc):
        mc.return_value = _hc({})
        s, t, _ = self._reg(); mc.return_value = _hc({})
        t["claim_task"]("T1"); self.assertFalse(s.is_loading)
    @patch(f"{_B}.httpx.Client")
    def test_complete_sets_loading(self, mc):
        m = _hc({}); tr = MagicMock(status_code=200)
        tr.json.return_value = {"items": [], "pagination": {}}
        m.get.return_value = tr; mc.return_value = m
        s, t, _ = self._reg(); mc.return_value = m
        t["complete_task"]("T1"); self.assertFalse(s.is_loading)


if __name__ == "__main__":
    unittest.main()
