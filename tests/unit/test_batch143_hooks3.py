"""Batch 143: Unit tests for core/base.py, core/state.py, entropy_monitor.py."""
import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_HOOKS = Path(__file__).resolve().parents[2] / ".claude" / "hooks"


def _load_module(name, filepath):
    """Load a module directly from file, bypassing __init__.py."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ===== Module 1: core/base.py =================================================

_base = _load_module("hooks_core_base", _HOOKS / "core" / "base.py")
HealthLevel = _base.HealthLevel
ServiceStatus = _base.ServiceStatus
HookConfig = _base.HookConfig
HookResult = _base.HookResult
ServiceInfo = _base.ServiceInfo
DEFAULT_CONFIG = _base.DEFAULT_CONFIG


class TestHealthLevel:
    def test_values(self):
        assert HealthLevel.OK.value == "OK"
        assert HealthLevel.CRITICAL.value == "CRITICAL"
        assert HealthLevel.DOWN.value == "DOWN"

    def test_all_levels(self):
        levels = [e.value for e in HealthLevel]
        assert "LOW" in levels
        assert "MEDIUM" in levels
        assert "HIGH" in levels


class TestServiceStatus:
    def test_values(self):
        assert ServiceStatus.OK.value == "OK"
        assert ServiceStatus.DOWN.value == "DOWN"
        assert ServiceStatus.PODMAN_DOWN.value == "PODMAN_DOWN"
        assert ServiceStatus.STARTING.value == "STARTING"


class TestHookConfig:
    def test_defaults(self):
        cfg = HookConfig()
        assert cfg.global_timeout == 15.0
        assert cfg.subprocess_timeout == 2.0
        assert cfg.socket_timeout == 0.5
        assert "typedb" in cfg.core_services

    def test_state_file_path(self):
        cfg = HookConfig()
        assert cfg.state_file.name == ".healthcheck_state.json"

    def test_entropy_file_path(self):
        cfg = HookConfig()
        assert cfg.entropy_file.name == ".entropy_state.json"

    def test_service_ports(self):
        cfg = HookConfig()
        assert cfg.service_ports["typedb"] == 1729
        assert cfg.service_ports["chromadb"] == 8001

    def test_expected_mcp_servers(self):
        cfg = HookConfig()
        assert any("mcp_server_core" in s for s in cfg.expected_mcp_servers)


class TestHookResult:
    def test_ok(self):
        r = HookResult.ok("All good", tool_count=10)
        assert r.success is True
        assert r.status == "OK"
        assert r.details["tool_count"] == 10

    def test_error(self):
        r = HookResult.error("Something broke", resolution_path="/fix")
        assert r.success is False
        assert r.status == "ERROR"
        assert r.resolution_path == "/fix"

    def test_warning(self):
        r = HookResult.warning("Heads up", level="HIGH")
        assert r.success is True
        assert r.status == "WARNING"
        assert r.details["level"] == "HIGH"

    def test_to_dict(self):
        r = HookResult.ok("OK")
        d = r.to_dict()
        assert d["success"] is True
        assert d["status"] == "OK"
        assert "details" in d

    @property
    def is_warning(self):
        """Test the is_warning check pattern used in EntropyChecker."""
        r = HookResult.warning("test")
        return r.status == "WARNING"


class TestServiceInfo:
    def test_basic(self):
        s = ServiceInfo(name="typedb", status=ServiceStatus.OK, ok=True, port=1729)
        assert s.name == "typedb"
        assert s.ok is True

    def test_to_dict(self):
        s = ServiceInfo(name="chromadb", status=ServiceStatus.DOWN, ok=False, port=8001)
        d = s.to_dict()
        assert d["status"] == "DOWN"
        assert d["ok"] is False
        assert d["port"] == 8001

    def test_optional(self):
        s = ServiceInfo(name="ollama", status=ServiceStatus.OFF, ok=False, optional=True)
        assert s.optional is True


# ===== Module 2: core/state.py =================================================

_state = _load_module("hooks_core_state", _HOOKS / "core" / "state.py")
compute_frankel_hash = _state.compute_frankel_hash
compute_component_hash = _state.compute_component_hash
compute_session_hash = _state.compute_session_hash
StateManager = _state.StateManager
HealthcheckState = _state.HealthcheckState
EntropyState = _state.EntropyState


class TestComputeFrankelHash:
    def test_deterministic(self):
        data = {"a": 1, "b": 2}
        h1 = compute_frankel_hash(data)
        h2 = compute_frankel_hash(data)
        assert h1 == h2

    def test_length(self):
        h = compute_frankel_hash({"test": True})
        assert len(h) == 8

    def test_uppercase(self):
        h = compute_frankel_hash({"x": 1})
        assert h == h.upper()

    def test_different_data(self):
        h1 = compute_frankel_hash({"a": 1})
        h2 = compute_frankel_hash({"a": 2})
        assert h1 != h2


class TestComputeComponentHash:
    def test_length(self):
        h = compute_component_hash("OK", 1729)
        assert len(h) == 4

    def test_uppercase(self):
        h = compute_component_hash("DOWN", 8001)
        assert h == h.upper()


class TestComputeSessionHash:
    def test_length(self):
        h = compute_session_hash("2026-01-01T00:00:00", 0)
        assert len(h) == 4

    def test_deterministic(self):
        h1 = compute_session_hash("2026-01-01", 42)
        h2 = compute_session_hash("2026-01-01", 42)
        assert h1 == h2


class TestStateManager:
    def test_load_missing_file(self):
        sm = StateManager(Path("/tmp/nonexistent_sm_test.json"))
        assert sm.load() == {}

    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            sm = StateManager(tmp)
            sm.save({"key": "value"})
            loaded = sm.load()
            assert loaded["key"] == "value"
        finally:
            tmp.unlink(missing_ok=True)

    def test_save_with_history(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            sm = StateManager(tmp, history_limit=5)
            state = {"data": 1}
            sm.save(state, add_history=True, history_entry={"event": "TEST"})
            loaded = sm.load()
            assert len(loaded["history"]) == 1
            assert loaded["history"][0]["event"] == "TEST"
        finally:
            tmp.unlink(missing_ok=True)

    def test_history_limit(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            sm = StateManager(tmp, history_limit=3)
            state = {"history": []}
            for i in range(5):
                sm.save(state, add_history=True, history_entry={"i": i})
                state = sm.load()
            assert len(state["history"]) == 3
        finally:
            tmp.unlink(missing_ok=True)

    def test_get_set_increment(self):
        sm = StateManager(Path("/tmp/sm_test.json"))
        sm._state = {"count": 5}
        assert sm.get("count") == 5
        assert sm.get("missing", "default") == "default"
        sm.set("count", 10)
        assert sm.state["count"] == 10
        new_val = sm.increment("count", 3)
        assert new_val == 13


class TestHealthcheckState:
    def test_default_state(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            hs = HealthcheckState(tmp)
            ds = hs.get_default_state()
            assert ds["master_hash"] == ""
            assert ds["check_count"] == 0
            assert ds["components"] == {}
        finally:
            tmp.unlink(missing_ok=True)

    def test_save_check(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            hs = HealthcheckState(tmp)
            # Initialize state
            hs.save(hs.get_default_state())
            services = {"typedb": {"status": "OK", "ok": True}}
            hs.save_check(services, "ABCD1234", {"typedb": "AB12"})
            loaded = hs.load()
            assert loaded["master_hash"] == "ABCD1234"
            assert loaded["check_count"] == 1
            assert loaded["components"]["typedb"] == "OK"
        finally:
            tmp.unlink(missing_ok=True)


class TestEntropyState:
    def test_default_state(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            es = EntropyState(tmp)
            ds = es.get_default_state()
            assert ds["tool_count"] == 0
            assert ds["session_hash"] == "0000"
        finally:
            tmp.unlink(missing_ok=True)

    def test_reset_session(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            es = EntropyState(tmp)
            state = es.reset_session()
            assert state["tool_count"] == 0
            assert len(state["session_hash"]) == 4
            loaded = es.load()
            assert len(loaded["history"]) == 1
            assert loaded["history"][0]["event"] == "SESSION_RESET"
        finally:
            tmp.unlink(missing_ok=True)

    def test_increment_tool_count(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"tool_count": 10, "check_count": 5, "history": []}, f)
            tmp = Path(f.name)
        try:
            es = EntropyState(tmp)
            new_count = es.increment_tool_count()
            assert new_count == 11
        finally:
            tmp.unlink(missing_ok=True)

    def test_mark_saved(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"tool_count": 50, "warnings_shown": 2, "history": []}, f)
            tmp = Path(f.name)
        try:
            es = EntropyState(tmp)
            es.mark_saved()
            loaded = es.load()
            assert loaded["warnings_shown"] == 0
            assert loaded["last_save"] is not None
            assert loaded["history"][-1]["event"] == "CONTEXT_SAVED"
        finally:
            tmp.unlink(missing_ok=True)

    def test_record_event(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"tool_count": 5, "session_hash": "AB12", "history": []}, f)
            tmp = Path(f.name)
        try:
            es = EntropyState(tmp)
            es.record_event("CUSTOM_EVENT")
            loaded = es.load()
            assert loaded["history"][-1]["event"] == "CUSTOM_EVENT"
        finally:
            tmp.unlink(missing_ok=True)


# ===== Module 3: entropy_monitor.py ============================================

_emon = _load_module("entropy_monitor", _HOOKS / "entropy_monitor.py")
em_generate_session_hash = _emon.generate_session_hash
em_load_state = _emon.load_state
em_save_state = _emon.save_state
em_get_session_minutes = _emon.get_session_minutes
em_format_output = _emon.format_output
em_reset_state = _emon.reset_state
em_mark_saved = _emon.mark_saved
em_detect_context_rot = _emon._detect_context_rot


class TestEmGenerateSessionHash:
    def test_length(self):
        h = em_generate_session_hash({"session_start": "2026-01-01", "tool_count": 0})
        assert len(h) == 4

    def test_deterministic(self):
        s = {"session_start": "2026-01-01", "tool_count": 5}
        assert em_generate_session_hash(s) == em_generate_session_hash(s)


class TestEmLoadSaveState:
    def test_load_missing(self):
        with patch.object(_emon, "STATE_FILE", Path("/tmp/nonexistent_em.json")):
            s = em_load_state()
            assert s["tool_count"] == 0

    def test_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch.object(_emon, "STATE_FILE", tmp):
                em_save_state({"tool_count": 42, "check_count": 10, "history": []})
                loaded = em_load_state()
                assert loaded["tool_count"] == 42
        finally:
            tmp.unlink(missing_ok=True)


class TestEmSaveStateHistory:
    def test_adds_history(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch.object(_emon, "STATE_FILE", tmp):
                state = {"tool_count": 10, "session_hash": "AB12", "history": []}
                em_save_state(state, add_history=True, event="TEST_EVENT")
                loaded = json.loads(tmp.read_text())
                assert len(loaded["history"]) == 1
                assert loaded["history"][0]["event"] == "TEST_EVENT"
        finally:
            tmp.unlink(missing_ok=True)

    def test_history_cap(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch.object(_emon, "STATE_FILE", tmp):
                state = {"tool_count": 1, "session_hash": "X", "history": [{"i": i} for i in range(55)]}
                em_save_state(state, add_history=True, event="OVERFLOW")
                loaded = json.loads(tmp.read_text())
                assert len(loaded["history"]) == 50
        finally:
            tmp.unlink(missing_ok=True)


class TestEmGetSessionMinutes:
    def test_recent(self):
        start = (datetime.now() - timedelta(minutes=30)).isoformat()
        minutes = em_get_session_minutes({"session_start": start})
        assert 29 <= minutes <= 31

    def test_error(self):
        assert em_get_session_minutes({"session_start": "invalid"}) == 0


class TestEmFormatOutput:
    def test_structure(self, capsys):
        em_format_output("test message")
        out = json.loads(capsys.readouterr().out)
        assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
        assert out["hookSpecificOutput"]["additionalContext"] == "test message"


class TestEmResetState:
    def test_resets(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            with patch.object(_emon, "STATE_FILE", tmp):
                em_reset_state()
                loaded = json.loads(tmp.read_text())
                assert loaded["tool_count"] == 0
                assert len(loaded["session_hash"]) == 4
                assert loaded["history"][0]["event"] == "SESSION_RESET"
        finally:
            tmp.unlink(missing_ok=True)


class TestEmMarkSaved:
    def test_marks(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump({"tool_count": 80, "warnings_shown": 3, "history": [],
                        "session_start": datetime.now().isoformat(),
                        "session_hash": "XY12"}, f)
            tmp = Path(f.name)
        try:
            with patch.object(_emon, "STATE_FILE", tmp):
                em_mark_saved()
                loaded = json.loads(tmp.read_text())
                assert loaded["warnings_shown"] == 0
                assert loaded["last_save"] is not None
        finally:
            tmp.unlink(missing_ok=True)


class TestDetectContextRot:
    def test_short_history(self):
        assert em_detect_context_rot(["Read", "Write"]) == 0.0

    def test_no_rot(self):
        tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Read", "Write", "Edit", "Bash"]
        score = em_detect_context_rot(tools)
        assert score < 0.5

    def test_high_rot(self):
        tools = ["Read"] * 20
        score = em_detect_context_rot(tools)
        assert score > 0.7

    def test_moderate_rot(self):
        tools = ["Read", "Read", "Write", "Read", "Read", "Write", "Read", "Read", "Write", "Read"]
        score = em_detect_context_rot(tools)
        assert 0.3 <= score <= 0.8
