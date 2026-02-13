"""Batch 136: Unit tests for 3 data access modules."""
import importlib.util, sys, types
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

_BASE = Path(__file__).resolve().parents[2] / "agent" / "governance_ui" / "data_access"

def _load(filename, name, mocks=None):
    for k, v in (mocks or {}).items():
        sys.modules.setdefault(k, v)
    spec = importlib.util.spec_from_file_location(name, _BASE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_mock_common = MagicMock()
_tc = types.ModuleType("_tc")
for _n in ("TRUST_WEIGHTS", "MAX_TENURE_DAYS", "calculate_trust_score",
           "build_trust_leaderboard", "calculate_consensus_score", "get_governance_stats"):
    setattr(_tc, _n, {} if _n == "TRUST_WEIGHTS" else 365 if _n == "MAX_TENURE_DAYS"
            else (lambda *a, **k: None))

# Temporarily inject mocks just for module loading, then restore
_originals = {k: sys.modules.get(k) for k in
              ("governance.mcp_tools.common", "agent.governance_ui.data_access.trust_calculations",
               "agent.journey_analyzer")}
sys.modules["governance.mcp_tools.common"] = _mock_common
sys.modules["agent.governance_ui.data_access.trust_calculations"] = _tc
T = _load("trust.py", "_t_trust")
_mock_jp = MagicMock()
sys.modules["agent.journey_analyzer"] = _mock_jp
J = _load("journey.py", "_t_journey")
E = _load("executive.py", "_t_exec")
# Restore all originals
for k, v in _originals.items():
    if v is None:
        sys.modules.pop(k, None)
    else:
        sys.modules[k] = v

class _TB:
    def setup_method(self):
        self.c = MagicMock()
        _mock_common.get_typedb_client.return_value = self.c
        # Inject mock into sys.modules only during test execution
        self._patcher = patch.dict(sys.modules,
            {"governance.mcp_tools.common": _mock_common})
        self._patcher.start()
    def teardown_method(self):
        self._patcher.stop()

# ===== Module 1: trust.py =================================================

class TestGetAgents(_TB):
    def test_ok(self):
        self.c.connect.return_value = True
        self.c.list_agents.return_value = [{"id": "a1"}]
        assert T.get_agents() == [{"id": "a1"}]
        self.c.close.assert_called_once()
    def test_fail(self):
        self.c.connect.return_value = False
        assert T.get_agents() == []
        self.c.close.assert_called_once()
    def test_none(self):
        self.c.connect.return_value = True
        self.c.list_agents.return_value = None
        assert T.get_agents() == []
    def test_exc_closes(self):
        self.c.connect.return_value = True
        self.c.list_agents.side_effect = RuntimeError("x")
        with pytest.raises(RuntimeError):
            T.get_agents()
        self.c.close.assert_called_once()
    def test_multi(self):
        self.c.connect.return_value = True
        self.c.list_agents.return_value = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        assert len(T.get_agents()) == 3

class TestGetAgentTrustScore(_TB):
    def test_success(self):
        self.c.connect.return_value = True
        self.c.get_agent_trust.return_value = 0.85
        assert T.get_agent_trust_score("a1") == 0.85
    def test_connect_fail(self):
        self.c.connect.return_value = False
        assert T.get_agent_trust_score("a1") is None
    def test_passes_id(self):
        self.c.connect.return_value = True
        self.c.get_agent_trust.return_value = 0.5
        T.get_agent_trust_score("my-agent")
        self.c.get_agent_trust.assert_called_once_with("my-agent")
    def test_none_trust(self):
        self.c.connect.return_value = True
        self.c.get_agent_trust.return_value = None
        assert T.get_agent_trust_score("x") is None
    def test_zero_score(self):
        self.c.connect.return_value = True
        self.c.get_agent_trust.return_value = 0.0
        assert T.get_agent_trust_score("y") == 0.0

class TestGetAgentActions(_TB):
    def test_success(self):
        self.c.connect.return_value = True
        self.c.get_agent_actions.return_value = [{"action": "vote"}]
        assert T.get_agent_actions("a1") == [{"action": "vote"}]
    def test_connect_fail(self):
        self.c.connect.return_value = False
        assert T.get_agent_actions("a1") == []
    def test_none_result(self):
        self.c.connect.return_value = True
        self.c.get_agent_actions.return_value = None
        assert T.get_agent_actions("a1") == []
    def test_passes_id(self):
        self.c.connect.return_value = True
        self.c.get_agent_actions.return_value = []
        T.get_agent_actions("agent-x")
        self.c.get_agent_actions.assert_called_once_with("agent-x")

class TestGetProposals(_TB):
    def test_no_filter(self):
        self.c.connect.return_value = True
        self.c.list_proposals.return_value = [{"id": "p1"}]
        assert T.get_proposals() == [{"id": "p1"}]
        self.c.list_proposals.assert_called_once_with(status=None)
    def test_status_filter(self):
        self.c.connect.return_value = True
        self.c.list_proposals.return_value = [{"id": "p2"}]
        T.get_proposals(status="approved")
        self.c.list_proposals.assert_called_once_with(status="approved")
    def test_connect_fail(self):
        self.c.connect.return_value = False
        assert T.get_proposals() == []
    def test_none_result(self):
        self.c.connect.return_value = True
        self.c.list_proposals.return_value = None
        assert T.get_proposals() == []

class TestGetProposalVotes(_TB):
    def test_success(self):
        self.c.connect.return_value = True
        self.c.get_proposal_votes.return_value = [{"vote": "yes"}]
        assert T.get_proposal_votes("p1") == [{"vote": "yes"}]
    def test_connect_fail(self):
        self.c.connect.return_value = False
        assert T.get_proposal_votes("p1") == []
    def test_none_result(self):
        self.c.connect.return_value = True
        self.c.get_proposal_votes.return_value = None
        assert T.get_proposal_votes("p1") == []
    def test_passes_id(self):
        self.c.connect.return_value = True
        self.c.get_proposal_votes.return_value = []
        T.get_proposal_votes("prop-42")
        self.c.get_proposal_votes.assert_called_once_with("prop-42")

class TestGetEscalatedProposals(_TB):
    def test_success(self):
        self.c.connect.return_value = True
        self.c.get_escalated_proposals.return_value = [{"id": "e1"}]
        assert T.get_escalated_proposals() == [{"id": "e1"}]
    def test_connect_fail(self):
        self.c.connect.return_value = False
        assert T.get_escalated_proposals() == []
    def test_none_result(self):
        self.c.connect.return_value = True
        self.c.get_escalated_proposals.return_value = None
        assert T.get_escalated_proposals() == []

# ===== Module 2: journey.py ===============================================
class TestGetJourneyAnalyzer:
    def setup_method(self):
        J._journey_analyzer_instance = None
        self.mock_a = MagicMock()
        _mock_jp.create_journey_analyzer.return_value = self.mock_a
        self._p = patch.dict(sys.modules, {"agent.journey_analyzer": _mock_jp})
        self._p.start()
    def teardown_method(self):
        self._p.stop()
    def test_creates_on_first_call(self):
        assert J.get_journey_analyzer() is self.mock_a
        _mock_jp.create_journey_analyzer.assert_called_once()
    def test_singleton_reuse(self):
        first = J.get_journey_analyzer()
        _mock_jp.create_journey_analyzer.reset_mock()
        assert J.get_journey_analyzer() is first
        _mock_jp.create_journey_analyzer.assert_not_called()
    def test_reset_creates_new(self):
        J.get_journey_analyzer()
        J._journey_analyzer_instance = None
        new = MagicMock()
        _mock_jp.create_journey_analyzer.return_value = new
        assert J.get_journey_analyzer() is new

class _JBase:
    def setup_method(self):
        self.a = MagicMock()
        J._journey_analyzer_instance = self.a

class TestLogJourneyQuestion(_JBase):
    def test_delegates(self):
        self.a.log_question.return_value = {"id": "q1"}
        assert J.log_journey_question("What?", "user") == {"id": "q1"}
        self.a.log_question.assert_called_once_with("What?", "user", None, None, True)
    def test_all_params(self):
        J.log_journey_question("Q", "agent", "cat", {"k": "v"}, False)
        self.a.log_question.assert_called_once_with("Q", "agent", "cat", {"k": "v"}, False)
    def test_returns_analyzer_result(self):
        self.a.log_question.return_value = {"id": "q2", "count": 3}
        assert J.log_journey_question("Q", "s")["count"] == 3

class TestGetRecurringQuestions(_JBase):
    def test_defaults(self):
        self.a.get_recurring_questions.return_value = []
        assert J.get_recurring_questions() == []
        self.a.get_recurring_questions.assert_called_once_with(2, None, False)
    def test_custom(self):
        J.get_recurring_questions(min_count=5, days=30, semantic_match=True)
        self.a.get_recurring_questions.assert_called_once_with(5, 30, True)

class TestGetJourneyPatterns(_JBase):
    def test_returns(self):
        self.a.detect_patterns.return_value = [{"pattern": "loop"}]
        assert J.get_journey_patterns() == [{"pattern": "loop"}]
    def test_empty(self):
        self.a.detect_patterns.return_value = []
        assert J.get_journey_patterns() == []

class TestGetKnowledgeGaps(_JBase):
    def test_returns(self):
        self.a.get_knowledge_gaps.return_value = [{"gap": "auth"}]
        assert J.get_knowledge_gaps() == [{"gap": "auth"}]

class TestGetQuestionHistory(_JBase):
    def test_defaults(self):
        self.a.get_question_history.return_value = []
        J.get_question_history()
        self.a.get_question_history.assert_called_once_with(50, None, None)
    def test_custom(self):
        J.get_question_history(limit=10, source="user", category="rules")
        self.a.get_question_history.assert_called_once_with(10, "user", "rules")
    def test_returns_list(self):
        self.a.get_question_history.return_value = [{"q": "hi"}]
        assert J.get_question_history() == [{"q": "hi"}]

# ===== Module 3: executive.py =============================================
def _mhc(status=200, data=None):
    resp = MagicMock(status_code=status)
    resp.json.return_value = data or {}
    mc = MagicMock()
    mc.get.return_value = resp
    mc.__enter__ = MagicMock(return_value=mc)
    mc.__exit__ = MagicMock(return_value=False)
    return mc

class TestGetExecutiveReport:
    @patch("httpx.Client")
    def test_no_params(self, cls):
        cls.return_value = _mhc(200, {"sections": ["s1"]})
        assert E.get_executive_report() == {"sections": ["s1"]}
    @patch("httpx.Client")
    def test_session_id(self, cls):
        mc = _mhc(200, {"ok": True}); cls.return_value = mc
        E.get_executive_report(session_id="S1")
        mc.get.assert_called_once_with("/api/reports/executive", params={"session_id": "S1"})
    @patch("httpx.Client")
    def test_date_range(self, cls):
        mc = _mhc(200, {}); cls.return_value = mc
        E.get_executive_report(start_date="2026-01-01", end_date="2026-01-31")
        mc.get.assert_called_once_with("/api/reports/executive",
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
    @patch("httpx.Client")
    def test_all_params(self, cls):
        mc = _mhc(200, {"full": True}); cls.return_value = mc
        E.get_executive_report("S2", "2026-02-01", "2026-02-28")
        mc.get.assert_called_once_with("/api/reports/executive",
            params={"session_id": "S2", "start_date": "2026-02-01", "end_date": "2026-02-28"})
    @patch("httpx.Client")
    def test_500_error(self, cls):
        cls.return_value = _mhc(500)
        r = E.get_executive_report()
        assert r["overall_status"] == "error" and r["sections"] == [] and "500" in r["error"]
    @patch("httpx.Client")
    def test_404_error(self, cls):
        cls.return_value = _mhc(404)
        r = E.get_executive_report()
        assert r["overall_status"] == "error" and "404" in r["error"]
    @patch("httpx.Client")
    def test_connection_error(self, cls):
        cls.side_effect = ConnectionError("refused")
        r = E.get_executive_report()
        assert r["overall_status"] == "error" and "refused" in r["error"]
        assert r["sections"] == [] and r["metrics_summary"] == {}
    @patch("httpx.Client")
    def test_timeout_error(self, cls):
        cls.side_effect = TimeoutError("timed out")
        r = E.get_executive_report()
        assert r["overall_status"] == "error" and "timed out" in r["error"]
    @patch("httpx.Client")
    def test_empty_params_sent(self, cls):
        mc = _mhc(200, {}); cls.return_value = mc
        E.get_executive_report()
        mc.get.assert_called_once_with("/api/reports/executive", params={})
    @patch("httpx.Client")
    def test_only_start_date(self, cls):
        mc = _mhc(200, {}); cls.return_value = mc
        E.get_executive_report(start_date="2026-03-01")
        mc.get.assert_called_once_with("/api/reports/executive",
            params={"start_date": "2026-03-01"})
    @patch("httpx.Client")
    def test_error_has_metrics_summary(self, cls):
        cls.return_value = _mhc(503)
        r = E.get_executive_report()
        assert r["metrics_summary"] == {} and r["sections"] == []
    @patch("httpx.Client")
    def test_only_end_date(self, cls):
        mc = _mhc(200, {}); cls.return_value = mc
        E.get_executive_report(end_date="2026-12-31")
        mc.get.assert_called_once_with("/api/reports/executive",
            params={"end_date": "2026-12-31"})
