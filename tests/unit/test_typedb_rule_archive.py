"""
Unit tests for TypeDB Rule Archive Operations.

Batch 155: Tests for governance/typedb/queries/rules/archive.py
- RuleArchiveOperations mixin: archive_rule, get_archived_rules,
  get_archived_rule, restore_rule
"""

import json
from dataclasses import dataclass, asdict
from unittest.mock import MagicMock, patch

import pytest

from governance.typedb.queries.rules.archive import RuleArchiveOperations, ARCHIVE_DIR
from governance.typedb.entities import Rule


class _TestableArchive(RuleArchiveOperations):
    """Concrete class for testing the archive mixin."""
    def __init__(self):
        self.database = "test-db"
        self.get_rule_by_id = MagicMock()
        self.get_rule_dependencies = MagicMock(return_value=[])
        self.get_rules_depending_on = MagicMock(return_value=[])
        self.create_rule = MagicMock()


def _make_rule(**kwargs):
    defaults = {
        "id": "RULE-001", "name": "Test Rule", "category": "Governance",
        "priority": "HIGH", "directive": "Do things", "status": "ACTIVE",
    }
    defaults.update(kwargs)
    return Rule(**defaults)


# ── archive_rule ─────────────────────────────────────────

class TestArchiveRule:
    def test_archives_existing_rule(self, tmp_path):
        a = _TestableArchive()
        rule = _make_rule()
        a.get_rule_by_id.return_value = rule

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            record = a.archive_rule("RULE-001", reason="deprecated")

        assert record is not None
        assert record["rule"]["id"] == "RULE-001"
        assert record["reason"] == "deprecated"
        assert record["archived_from_db"] == "test-db"
        # File should exist on disk
        files = list(tmp_path.glob("RULE-001_*.json"))
        assert len(files) == 1

    def test_returns_none_if_not_found(self):
        a = _TestableArchive()
        a.get_rule_by_id.return_value = None
        assert a.archive_rule("RULE-999") is None

    def test_captures_dependencies(self, tmp_path):
        a = _TestableArchive()
        a.get_rule_by_id.return_value = _make_rule()
        a.get_rule_dependencies.return_value = ["RULE-002"]
        a.get_rules_depending_on.return_value = ["RULE-003"]

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            record = a.archive_rule("RULE-001")

        assert record["dependencies"] == ["RULE-002"]
        assert record["dependents"] == ["RULE-003"]

    def test_handles_dependency_errors(self, tmp_path):
        a = _TestableArchive()
        a.get_rule_by_id.return_value = _make_rule()
        a.get_rule_dependencies.side_effect = Exception("db error")
        a.get_rules_depending_on.side_effect = Exception("db error")

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            record = a.archive_rule("RULE-001")

        assert record["dependencies"] == []
        assert record["dependents"] == []


# ── get_archived_rules ───────────────────────────────────

class TestGetArchivedRules:
    def test_empty_when_no_dir(self, tmp_path):
        a = _TestableArchive()
        missing = tmp_path / "nonexistent"
        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", missing):
            assert a.get_archived_rules() == []

    def test_reads_archive_files(self, tmp_path):
        a = _TestableArchive()
        record = {"rule": {"id": "RULE-001"}, "reason": "test"}
        (tmp_path / "RULE-001_20260213.json").write_text(json.dumps(record))

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            results = a.get_archived_rules()

        assert len(results) == 1
        assert results[0]["rule"]["id"] == "RULE-001"
        assert "archive_file" in results[0]

    def test_skips_corrupt_files(self, tmp_path):
        a = _TestableArchive()
        (tmp_path / "bad.json").write_text("not valid json{{{")
        record = {"rule": {"id": "RULE-002"}, "reason": "ok"}
        (tmp_path / "RULE-002_20260213.json").write_text(json.dumps(record))

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            results = a.get_archived_rules()

        assert len(results) == 1
        assert results[0]["rule"]["id"] == "RULE-002"

    def test_sorted_reverse(self, tmp_path):
        a = _TestableArchive()
        for i in range(3):
            name = f"RULE-00{i}_2026021{i}.json"
            (tmp_path / name).write_text(json.dumps({"rule": {"id": f"R-{i}"}}))

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            results = a.get_archived_rules()

        assert len(results) == 3
        # Reverse sorted by filename
        assert results[0]["rule"]["id"] == "R-2"


# ── get_archived_rule ────────────────────────────────────

class TestGetArchivedRule:
    def test_finds_rule(self, tmp_path):
        a = _TestableArchive()
        record = {"rule": {"id": "RULE-001"}, "reason": "test"}
        (tmp_path / "RULE-001_20260213.json").write_text(json.dumps(record))

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            result = a.get_archived_rule("RULE-001")

        assert result is not None
        assert result["rule"]["id"] == "RULE-001"

    def test_not_found(self, tmp_path):
        a = _TestableArchive()
        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            assert a.get_archived_rule("RULE-999") is None


# ── restore_rule ─────────────────────────────────────────

class TestRestoreRule:
    def test_restores_from_archive(self, tmp_path):
        a = _TestableArchive()
        record = {"rule": {"id": "RULE-001", "name": "Test", "category": "Gov",
                           "priority": "HIGH", "directive": "Do things"}}
        (tmp_path / "RULE-001_20260213.json").write_text(json.dumps(record))
        a.get_rule_by_id.return_value = None  # Not currently in DB
        a.create_rule.return_value = _make_rule()

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            result = a.restore_rule("RULE-001")

        assert result is not None
        a.create_rule.assert_called_once()
        call_kwargs = a.create_rule.call_args[1]
        assert call_kwargs["status"] == "DRAFT"

    def test_not_in_archive(self, tmp_path):
        a = _TestableArchive()
        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            assert a.restore_rule("RULE-999") is None

    def test_raises_if_rule_exists(self, tmp_path):
        a = _TestableArchive()
        record = {"rule": {"id": "RULE-001", "name": "T", "category": "C",
                           "priority": "H", "directive": "D"}}
        (tmp_path / "RULE-001_20260213.json").write_text(json.dumps(record))
        a.get_rule_by_id.return_value = _make_rule()  # Already in DB

        with patch("governance.typedb.queries.rules.archive.ARCHIVE_DIR", tmp_path):
            with pytest.raises(ValueError, match="already exists"):
                a.restore_rule("RULE-001")
