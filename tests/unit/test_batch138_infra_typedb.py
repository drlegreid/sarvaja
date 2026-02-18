"""Batch 138: Unit tests for infra_loaders + TypeDB task CRUD."""
import json
import os
import sys
import types
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ===== Module 1: controllers/infra_loaders.py ================================

def _make_state(**kw):
    s = MagicMock()
    for k, v in kw.items():
        setattr(s, k, v)
    return s


def _make_ctrl():
    c = MagicMock()
    _triggers = {}

    def trigger(name):
        def dec(fn):
            _triggers[name] = fn
            return fn
        return dec

    c.trigger = trigger
    c._triggers = _triggers
    return c


class TestLoadInfraStatus:
    def setup_method(self):
        self.state = _make_state(infra_services={}, infra_stats={}, infra_loading=True)
        self.ctrl = _make_ctrl()

    @patch("socket.socket")
    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run")
    def test_healthy(self, sub_run, os_exists, sock_cls):
        sub_run.return_value = MagicMock(returncode=0)
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        sock_cls.return_value = mock_sock
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        result = register_infra_loader_controllers(self.state, self.ctrl, "http://test:8082")
        with patch("builtins.open", side_effect=FileNotFoundError):
            result["load_infra_status"]()
        assert self.state.infra_loading is False
        services = self.state.infra_services
        assert services["podman"]["ok"] is True

    @patch("socket.socket")
    @patch("os.path.exists", return_value=True)
    def test_in_container(self, os_exists, sock_cls):
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        sock_cls.return_value = mock_sock
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        result = register_infra_loader_controllers(self.state, self.ctrl, "http://test:8082")
        with patch("builtins.open", side_effect=FileNotFoundError):
            result["load_infra_status"]()
        assert self.state.infra_services["podman"]["ok"] is True

    @patch("socket.socket")
    @patch("os.path.exists", return_value=False)
    @patch("subprocess.run")
    def test_degraded(self, sub_run, os_exists, sock_cls):
        sub_run.return_value = MagicMock(returncode=0)
        mock_sock = MagicMock()
        call_count = [0]

        def port_check(addr):
            call_count[0] += 1
            # typedb=ok, chromadb=ok, litellm=fail, ollama=fail
            return 0 if call_count[0] <= 2 else 1

        mock_sock.connect_ex.side_effect = port_check
        sock_cls.return_value = mock_sock
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        result = register_infra_loader_controllers(self.state, self.ctrl, "http://test:8082")
        with patch("builtins.open", side_effect=FileNotFoundError):
            result["load_infra_status"]()
        assert self.state.infra_stats["status"] == "degraded"


class TestStartService:
    @patch("subprocess.Popen")
    def test_start_service(self, popen):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["start_service"]("typedb")
        popen.assert_called_once()
        assert "typedb" in popen.call_args[0][0]

    @patch("subprocess.Popen")
    def test_start_all(self, popen):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["start_all_services"]()
        popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_restart_stack(self, popen):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["restart_stack"]()
        popen.assert_called_once()
        assert "restart" in popen.call_args[0][0]

    @patch("subprocess.Popen", side_effect=FileNotFoundError("no podman"))
    def test_start_error(self, popen):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["start_service"]("typedb")
        assert "Failed" in state.infra_last_action


class TestLoadContainerLogs:
    @patch("httpx.get")
    def test_success(self, hget):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"lines": ["log1", "log2"]}
        hget.return_value = resp
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["load_container_logs"]("dashboard", 50, "")
        assert state.infra_log_lines == ["log1", "log2"]

    @patch("httpx.get", side_effect=ConnectionError("refused"))
    def test_error(self, hget):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["load_container_logs"]()
        assert "Failed" in state.infra_log_lines[0]


class TestCleanupZombies:
    @patch("subprocess.run")
    def test_success(self, sub_run):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["cleanup_zombies"]()
        assert "Cleaned up" in state.infra_last_action

    @patch("subprocess.run", side_effect=Exception("pkill fail"))
    def test_error(self, sub_run):
        state = _make_state()
        ctrl = _make_ctrl()
        from agent.governance_ui.controllers.infra_loaders import register_infra_loader_controllers
        register_infra_loader_controllers(state, ctrl, "http://test:8082")
        ctrl._triggers["cleanup_zombies"]()
        assert "failed" in state.infra_last_action.lower()


# ===== Module 2: typedb/queries/tasks/crud.py ================================

# Mock typedb.driver before importing
_mock_driver = types.ModuleType("typedb")
_mock_driver.driver = types.ModuleType("typedb.driver")
_mock_driver.driver.TransactionType = MagicMock()
_mock_driver.driver.TransactionType.WRITE = "WRITE"
_mock_driver.driver.TransactionType.READ = "READ"


class TestUpdateAttribute:
    def test_with_old_value(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            tx = MagicMock()
            tx.query.return_value.resolve.return_value = None
            _update_attribute(tx, "T1", "task-status", "OPEN", "IN_PROGRESS")
            assert tx.query.call_count == 2  # delete + insert

    def test_without_old_value(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            tx = MagicMock()
            tx.query.return_value.resolve.return_value = None
            _update_attribute(tx, "T1", "task-name", None, "New Name")
            assert tx.query.call_count == 1  # insert only

    def test_escapes_quotes(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _update_attribute
            tx = MagicMock()
            tx.query.return_value.resolve.return_value = None
            _update_attribute(tx, "T1", "task-name", 'He said "hi"', 'She said "bye"')
            call_args = [c[0][0] for c in tx.query.call_args_list]
            assert all('\\"' in arg for arg in call_args)


class TestSetLifecycleTimestamps:
    def test_claimed_at_on_in_progress(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _set_lifecycle_timestamps
            tx = MagicMock()
            tx.query.return_value.resolve.return_value = None
            current = MagicMock(claimed_at=None, completed_at=None)
            _set_lifecycle_timestamps(tx, "T1", "IN_PROGRESS", current)
            assert tx.query.call_count == 1
            assert "claimed-at" in tx.query.call_args[0][0]

    def test_completed_at_on_done(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _set_lifecycle_timestamps
            tx = MagicMock()
            tx.query.return_value.resolve.return_value = None
            current = MagicMock(claimed_at="2026-01-01", completed_at=None)
            _set_lifecycle_timestamps(tx, "T1", "DONE", current)
            assert "completed-at" in tx.query.call_args[0][0]

    def test_no_op_if_already_set(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import _set_lifecycle_timestamps
            tx = MagicMock()
            current = MagicMock(claimed_at="2026-01-01", completed_at="2026-01-02")
            _set_lifecycle_timestamps(tx, "T1", "DONE", current)
            tx.query.assert_not_called()


class TestTaskCRUDInsert:
    def _make_client(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        c = type("C", (TaskCRUDOperations,), {})()
        c._driver = MagicMock()
        c.database = "test-db"
        c.get_task = MagicMock()
        tx = MagicMock()
        tx.query.return_value.resolve.return_value = None
        c._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        c._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return c, tx

    def test_insert_basic(self):
        c, tx = self._make_client()
        c.get_task.return_value = MagicMock(task_id="T1")
        result = c.insert_task("T1", "Test Task", "OPEN", "P10")
        assert result is not None
        tx.commit.assert_called_once()

    def test_insert_with_rules(self):
        c, tx = self._make_client()
        c.get_task.return_value = MagicMock(task_id="T1")
        c.insert_task("T1", "Test", "OPEN", "P10", linked_rules=["RULE-001", "RULE-002"])
        # base insert + 2 rule relations
        assert tx.query.call_count == 3

    def test_insert_failure(self):
        c, tx = self._make_client()
        c._driver.transaction.side_effect = Exception("DB error")
        result = c.insert_task("T1", "Test", "OPEN", "P10")
        assert result is None


class TestTaskCRUDUpdate:
    def _make_client(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        c = type("C", (TaskCRUDOperations,), {})()
        c._driver = MagicMock()
        c.database = "test-db"
        c.get_task = MagicMock()
        tx = MagicMock()
        tx.query.return_value.resolve.return_value = None
        c._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        c._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return c, tx

    def test_not_found(self):
        c, _ = self._make_client()
        c.get_task.return_value = None
        assert c.update_task("T-NONE", status="DONE") is False

    def test_status_change(self):
        c, tx = self._make_client()
        c.get_task.return_value = MagicMock(
            status="OPEN", name="Test", phase="P10",
            claimed_at=None, completed_at=None, item_type=None, document_path=None,
        )
        assert c.update_task("T1", status="IN_PROGRESS") is True
        tx.commit.assert_called_once()

    def test_update_error(self):
        c, tx = self._make_client()
        c.get_task.return_value = MagicMock(status="OPEN", name="T", phase="P10")
        c._driver.transaction.side_effect = Exception("fail")
        assert c.update_task("T1", status="DONE") is False


class TestTaskCRUDDelete:
    def _make_client(self):
        with patch.dict(sys.modules, {"typedb": _mock_driver, "typedb.driver": _mock_driver.driver}):
            from governance.typedb.queries.tasks.crud import TaskCRUDOperations
        c = type("C", (TaskCRUDOperations,), {})()
        c._driver = MagicMock()
        c.database = "test-db"
        tx = MagicMock()
        tx.query.return_value.resolve.return_value = None
        c._driver.transaction.return_value.__enter__ = MagicMock(return_value=tx)
        c._driver.transaction.return_value.__exit__ = MagicMock(return_value=False)
        return c, tx

    def test_delete_success(self):
        c, tx = self._make_client()
        assert c.delete_task("T1") is True
        # 3 commits: 2 relationship cleanup transactions + 1 entity delete
        assert tx.commit.call_count == 3

    def test_delete_error(self):
        c, _ = self._make_client()
        c._driver.transaction.side_effect = Exception("DB fail")
        assert c.delete_task("T1") is False
