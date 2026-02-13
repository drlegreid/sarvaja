"""Batch 145: Unit tests for session_visibility, recover.py."""
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import datetime
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


# ===== Module 1: checkers/session_visibility.py ================================

_vis = _load_module("checkers_session_visibility", _HOOKS / "checkers" / "session_visibility.py")
TaskContext = _vis.TaskContext
load_env_var = _vis.load_env_var
load_visibility = _vis.load_visibility
save_visibility = _vis.save_visibility
start_session = _vis.start_session
start_task = _vis.start_task
record_rule_application = _vis.record_rule_application
record_tool_call = _vis.record_tool_call
complete_task = _vis.complete_task
get_session_visibility = _vis.get_session_visibility
get_task_rules_summary = _vis.get_task_rules_summary
get_token_usage_report = _vis.get_token_usage_report
record_commit_info = _vis.record_commit_info
get_task_commit_info = _vis.get_task_commit_info


class TestTaskContext:
    def test_creation(self):
        tc = TaskContext(
            task_id="T1", task_name="Test", session_id="S1",
            started_at="2026-01-01", rules_applied=[], tool_calls=[]
        )
        assert tc.task_id == "T1"
        assert tc.status == "in_progress"
        assert tc.tokens_used == 0


class TestLoadEnvVar:
    def test_from_env_file(self):
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
            f.write('API_KEY="test123"\n')
            f.write("OTHER=plain_value\n")
            tmp = Path(f.name)
        try:
            with patch.object(_vis, "ENV_FILE", tmp):
                assert load_env_var("API_KEY") == "test123"
                assert load_env_var("OTHER") == "plain_value"
        finally:
            tmp.unlink(missing_ok=True)

    def test_single_quoted(self):
        with tempfile.NamedTemporaryFile(suffix=".env", delete=False, mode="w") as f:
            f.write("KEY='single'\n")
            tmp = Path(f.name)
        try:
            with patch.object(_vis, "ENV_FILE", tmp):
                assert load_env_var("KEY") == "single"
        finally:
            tmp.unlink(missing_ok=True)

    def test_missing(self):
        with patch.object(_vis, "ENV_FILE", Path("/tmp/nonexistent_env")):
            with patch.dict("os.environ", {}, clear=True):
                assert load_env_var("MISSING_KEY") is None


class TestVisibilityLoadSave:
    def test_load_missing(self):
        with patch.object(_vis, "VISIBILITY_FILE", Path("/tmp/nonexistent_vis.json")):
            s = load_visibility()
            assert s["current_session"] is None
            assert s["active_tasks"] == {}

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                save_visibility({"current_session": None, "active_tasks": {}, "token_usage": {"total": 0}})
                loaded = load_visibility()
                assert "last_updated" in loaded


class TestStartSession:
    def test_creates_session(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                result = start_session("S-TEST-001")
                assert result["session_id"] == "S-TEST-001"
                assert result["tool_calls"] == 0


class TestStartTask:
    def test_creates_task(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                task = start_task("T1", "Test Task")
                assert task.task_id == "T1"
                assert task.session_id == "S1"

    def test_no_session(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                task = start_task("T1", "Test", session_id="explicit")
                assert task.session_id == "explicit"


class TestRecordRuleApplication:
    def test_records(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                record_rule_application("T1", "RULE-001")
                loaded = load_visibility()
                assert "RULE-001" in loaded["active_tasks"]["T1"]["rules_applied"]
                assert "RULE-001" in loaded["current_session"]["rules_applied"]

    def test_no_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                record_rule_application("T1", "RULE-001")
                record_rule_application("T1", "RULE-001")
                loaded = load_visibility()
                assert loaded["active_tasks"]["T1"]["rules_applied"].count("RULE-001") == 1


class TestRecordToolCall:
    def test_records(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                record_tool_call("T1", "Read", duration_ms=100, tokens=500)
                loaded = load_visibility()
                assert len(loaded["active_tasks"]["T1"]["tool_calls"]) == 1
                assert loaded["active_tasks"]["T1"]["tokens_used"] == 500
                assert loaded["current_session"]["tool_calls"] == 1
                assert loaded["token_usage"]["total"] == 500


class TestCompleteTask:
    def test_completes(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                result = complete_task("T1")
                assert result["status"] == "completed"
                assert result["completed_at"] is not None
                loaded = load_visibility()
                assert "T1" not in loaded["active_tasks"]
                assert len(loaded["completed_tasks"]) == 1

    def test_not_found(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                assert complete_task("NONEXISTENT") is None


class TestGetSessionVisibility:
    def test_returns_summary(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                result = get_session_visibility()
                assert result["active_task_count"] == 1
                assert result["current_session"]["session_id"] == "S1"


class TestGetTaskRulesSummary:
    def test_active_task(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                record_rule_application("T1", "R1")
                result = get_task_rules_summary("T1")
                assert result["rule_count"] == 1
                assert result["status"] == "active"

    def test_completed_task(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                complete_task("T1")
                result = get_task_rules_summary("T1")
                assert result["status"] == "completed"

    def test_not_found(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                result = get_task_rules_summary("NOPE")
                assert "error" in result


class TestCommitTracking:
    def test_record_and_get(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                start_session("S1")
                start_task("T1", "Test")
                record_commit_info("T1", "abc123", ["a.py", "b.py"], "Fix bug")
                result = get_task_commit_info("T1")
                assert result["commit_count"] == 1
                assert "a.py" in result["files_changed"]

    def test_not_found(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file):
                result = get_task_commit_info("NOPE")
                assert "error" in result


class TestGetTokenUsageReport:
    def test_no_api_key(self):
        with tempfile.TemporaryDirectory() as td:
            vis_file = Path(td) / "vis.json"
            with patch.object(_vis, "VISIBILITY_FILE", vis_file), \
                 patch.object(_vis, "ENV_FILE", Path("/tmp/nonexistent_env")):
                with patch.dict("os.environ", {}, clear=True):
                    result = get_token_usage_report()
                    assert result["api_key_configured"] is False
                    assert result["total_tokens"] == 0


# ===== Module 2: recover.py ===================================================

_recover = _load_module("recover_script", _HOOKS / "recover.py")
get_timestamp = _recover.get_timestamp
create_backup = _recover.create_backup
get_minimal_settings = _recover.get_minimal_settings
restore_minimal = _recover.restore_minimal
restore_from_backup = _recover.restore_from_backup
list_backups = _recover.list_backups


class TestGetTimestamp:
    def test_format(self):
        ts = get_timestamp()
        assert len(ts) == 15  # YYYYMMDD_HHMMSS
        assert "_" in ts


class TestCreateBackup:
    def test_creates_backup(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "settings.local.json"
            settings.write_text('{"hooks": {}}')
            backup_dir = Path(td) / "backups"
            with patch.object(_recover, "SETTINGS_FILE", settings), \
                 patch.object(_recover, "BACKUP_DIR", backup_dir):
                result = create_backup()
                assert result is not None
                assert result.exists()
                assert backup_dir.exists()

    def test_no_settings(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "nonexistent.json"
            with patch.object(_recover, "SETTINGS_FILE", settings):
                result = create_backup()
                assert result is None


class TestGetMinimalSettings:
    def test_has_session_start(self):
        settings = get_minimal_settings()
        assert "hooks" in settings
        assert "SessionStart" in settings["hooks"]


class TestRestoreMinimal:
    def test_writes_file(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "settings.local.json"
            with patch.object(_recover, "SETTINGS_FILE", settings):
                restore_minimal()
                assert settings.exists()
                data = json.loads(settings.read_text())
                assert "SessionStart" in data["hooks"]


class TestRestoreFromBackup:
    def test_success(self):
        with tempfile.TemporaryDirectory() as td:
            settings = Path(td) / "settings.local.json"
            settings.write_text('{"old": true}')
            backup = Path(td) / "backup.bak"
            backup.write_text('{"restored": true}')
            backup_dir = Path(td) / "backups"
            with patch.object(_recover, "SETTINGS_FILE", settings), \
                 patch.object(_recover, "BACKUP_DIR", backup_dir):
                result = restore_from_backup(backup)
                assert result is True
                data = json.loads(settings.read_text())
                assert data["restored"] is True

    def test_not_found(self):
        result = restore_from_backup(Path("/tmp/nonexistent_backup.bak"))
        assert result is False


class TestListBackups:
    def test_no_dir(self):
        with patch.object(_recover, "BACKUP_DIR", Path("/tmp/nonexistent_backups")):
            result = list_backups()
            assert result == []

    def test_with_backups(self):
        with tempfile.TemporaryDirectory() as td:
            backup_dir = Path(td) / "backups"
            backup_dir.mkdir()
            (backup_dir / "settings.local.json.20260101_120000.bak").write_text("{}")
            (backup_dir / "settings.local.json.20260102_120000.bak").write_text("{}")
            with patch.object(_recover, "BACKUP_DIR", backup_dir):
                result = list_backups()
                assert len(result) == 2
