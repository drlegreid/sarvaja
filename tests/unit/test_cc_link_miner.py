"""
Tests for cross-entity link miner (JSONL -> TypeDB relations).

Batch 168: New coverage for governance/services/cc_link_miner.py (0->16 tests).
"""
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest


@dataclass
class _FakeEntry:
    text_content: str = ""
    entry_type: str = "assistant"
    timestamp: object = None
    git_branch: str = ""


class TestDecisionPattern:
    def test_extract_decision_refs_basic(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        result = _extract_decision_refs("See DECISION-008 for details")
        assert "DECISION-008" in result

    def test_extract_decision_refs_multiple(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        result = _extract_decision_refs("DECISION-001 and DECISION-042")
        assert "DECISION-001" in result
        assert "DECISION-042" in result

    def test_extract_decision_refs_case_insensitive(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        result = _extract_decision_refs("decision-123 found")
        assert "DECISION-123" in result

    def test_extract_decision_refs_no_match(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        result = _extract_decision_refs("no decisions here")
        assert len(result) == 0

    def test_extract_decision_refs_short_number_ignored(self):
        from governance.services.cc_link_miner import _extract_decision_refs
        result = _extract_decision_refs("DECISION-01 too short")
        assert len(result) == 0


class TestValidateEntityExists:
    def test_cache_hit(self):
        from governance.services.cc_link_miner import _validate_entity_exists
        cache = {"task:T-001": True}
        result = _validate_entity_exists(None, "task", "T-001", cache)
        assert result is True

    def test_task_exists(self):
        from governance.services.cc_link_miner import _validate_entity_exists
        client = MagicMock()
        client.get_task.return_value = {"task_id": "T-001"}
        cache = {}
        result = _validate_entity_exists(client, "task", "T-001", cache)
        assert result is True
        assert cache["task:T-001"] is True

    def test_rule_not_found(self):
        from governance.services.cc_link_miner import _validate_entity_exists
        client = MagicMock()
        # Production code uses get_rule_by_id, not get_rule
        client.get_rule_by_id.return_value = None
        cache = {}
        result = _validate_entity_exists(client, "rule", "RULE-001", cache)
        assert result is False

    def test_decision_lookup(self):
        from governance.services.cc_link_miner import _validate_entity_exists
        from unittest.mock import MagicMock as MM
        client = MM()
        # Production code uses get_all_decisions() and checks decision_id set
        decision = MM()
        decision.decision_id = "D-1"
        client.get_all_decisions.return_value = [decision]
        cache = {}
        result = _validate_entity_exists(client, "decision", "D-1", cache)
        assert result is True

    def test_exception_returns_false(self):
        from governance.services.cc_link_miner import _validate_entity_exists
        client = MagicMock()
        client.get_task.side_effect = Exception("DB error")
        cache = {}
        result = _validate_entity_exists(client, "task", "T-ERR", cache)
        assert result is False


class TestMineSessionLinks:
    @patch("governance.services.cc_link_miner.save_checkpoint")
    @patch("governance.services.cc_link_miner.load_checkpoint", return_value=None)
    @patch("governance.services.cc_link_miner.extract_gap_refs", return_value=set())
    @patch("governance.services.cc_link_miner.extract_rule_refs", return_value=set())
    @patch("governance.services.cc_link_miner.extract_task_refs", return_value=set())
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    def test_dry_run_no_links(self, mock_parse, mock_task, mock_rule, mock_gap, mock_load, mock_save, tmp_path):
        from governance.services.cc_link_miner import mine_session_links

        fake_jsonl = tmp_path / "fake.jsonl"
        fake_jsonl.write_text("")
        mock_parse.return_value = iter([_FakeEntry(text_content="hello")])
        result = mine_session_links(fake_jsonl, "SESSION-X", dry_run=True)
        assert result["status"] == "dry_run"
        assert result["tasks_linked"] == 0

    @patch("governance.services.cc_link_miner.save_checkpoint")
    @patch("governance.services.cc_link_miner.load_checkpoint", return_value=None)
    @patch("governance.services.cc_link_miner.extract_gap_refs", return_value=set())
    @patch("governance.services.cc_link_miner.extract_rule_refs", return_value={"RULE-001"})
    @patch("governance.services.cc_link_miner.extract_task_refs", return_value={"T-001"})
    @patch("governance.session_metrics.parser.parse_log_file_extended")
    def test_dry_run_captures_refs(self, mock_parse, mock_task, mock_rule, mock_gap, mock_load, mock_save, tmp_path):
        from governance.services.cc_link_miner import mine_session_links

        fake_jsonl = tmp_path / "fake.jsonl"
        fake_jsonl.write_text("")
        mock_parse.return_value = iter([_FakeEntry(text_content="T-001 and RULE-001")])
        result = mine_session_links(fake_jsonl, "SESSION-X", dry_run=True)
        assert "T-001" in result["refs_found"]["tasks"]
        assert "RULE-001" in result["refs_found"]["rules"]

    def test_module_has_logger(self):
        from governance.services.cc_link_miner import logger
        assert logger.name == "governance.services.cc_link_miner"

    def test_decision_pattern_exported(self):
        from governance.services.cc_link_miner import _DECISION_PATTERN
        assert _DECISION_PATTERN.pattern
