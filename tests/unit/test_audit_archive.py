"""Unit tests for Audit Cold Archive — SRVJ-FEAT-AUDIT-TRAIL-01 P4.

Tests _archive_entries(), query_audit_archive(), and retention wiring.
Per TDD: Write RED tests first, then implement to GREEN.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def archive_dir(tmp_path):
    """Temporary archive directory for JSONL files."""
    d = tmp_path / "logs" / "audit"
    d.mkdir(parents=True)
    return d


SAMPLE_ENTRIES = [
    {
        "audit_id": "AUDIT-001",
        "correlation_id": "CORR-001",
        "timestamp": "2026-03-20T10:00:00",
        "actor_id": "system",
        "action_type": "CREATE",
        "entity_type": "task",
        "entity_id": "TASK-001",
        "old_value": None,
        "new_value": None,
        "applied_rules": [],
        "metadata": {},
    },
    {
        "audit_id": "AUDIT-002",
        "correlation_id": "CORR-002",
        "timestamp": "2026-03-20T11:00:00",
        "actor_id": "code-agent",
        "action_type": "UPDATE",
        "entity_type": "task",
        "entity_id": "TASK-001",
        "old_value": "TODO",
        "new_value": "IN_PROGRESS",
        "applied_rules": [],
        "metadata": {},
    },
    {
        "audit_id": "AUDIT-003",
        "correlation_id": "CORR-003",
        "timestamp": "2026-03-21T09:00:00",
        "actor_id": "system",
        "action_type": "LINK",
        "entity_type": "task",
        "entity_id": "TASK-002",
        "old_value": None,
        "new_value": None,
        "applied_rules": [],
        "metadata": {"linked_entity": {"type": "rule", "id": "R-001"}},
    },
]


class TestArchiveEntries:
    """Tests for _archive_entries() — writes JSONL files."""

    def test_writes_jsonl_one_line_per_entry(self, archive_dir):
        """_archive_entries writes one JSON line per entry."""
        from governance.stores.audit import _archive_entries
        _archive_entries(SAMPLE_ENTRIES[:2], archive_dir=archive_dir)
        files = list(archive_dir.glob("*.jsonl"))
        assert len(files) >= 1
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            parsed = json.loads(line)
            assert "audit_id" in parsed

    def test_appends_to_existing_daily_file(self, archive_dir):
        """_archive_entries appends to existing file for same date."""
        from governance.stores.audit import _archive_entries
        _archive_entries(SAMPLE_ENTRIES[:1], archive_dir=archive_dir)
        _archive_entries(SAMPLE_ENTRIES[1:2], archive_dir=archive_dir)
        # Both entries are 2026-03-20 → same file
        files = list(archive_dir.glob("2026-03-20.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 2

    def test_creates_directory_if_missing(self, tmp_path):
        """_archive_entries creates logs/audit/ directory if missing."""
        from governance.stores.audit import _archive_entries
        new_dir = tmp_path / "new" / "audit"
        assert not new_dir.exists()
        _archive_entries(SAMPLE_ENTRIES[:1], archive_dir=new_dir)
        assert new_dir.exists()

    def test_empty_list_no_file_written(self, archive_dir):
        """_archive_entries with empty list writes nothing."""
        from governance.stores.audit import _archive_entries
        _archive_entries([], archive_dir=archive_dir)
        files = list(archive_dir.glob("*.jsonl"))
        assert len(files) == 0

    def test_unicode_safe(self, archive_dir):
        """_archive_entries handles unicode characters in metadata."""
        from governance.stores.audit import _archive_entries
        entry = {**SAMPLE_ENTRIES[0], "metadata": {"msg": "日本語テスト 🎉"}}
        _archive_entries([entry], archive_dir=archive_dir)
        files = list(archive_dir.glob("*.jsonl"))
        content = files[0].read_text()
        assert "日本語テスト" in content

    def test_groups_by_date(self, archive_dir):
        """_archive_entries groups entries into correct daily files."""
        from governance.stores.audit import _archive_entries
        # Entry 0,1 = 2026-03-20, Entry 2 = 2026-03-21
        _archive_entries(SAMPLE_ENTRIES, archive_dir=archive_dir)
        assert (archive_dir / "2026-03-20.jsonl").exists()
        assert (archive_dir / "2026-03-21.jsonl").exists()
        lines_20 = (archive_dir / "2026-03-20.jsonl").read_text().strip().split("\n")
        lines_21 = (archive_dir / "2026-03-21.jsonl").read_text().strip().split("\n")
        assert len(lines_20) == 2
        assert len(lines_21) == 1


class TestArchiveWriteFailureSafe:
    """Tests that archive write failure doesn't block retention."""

    def test_write_failure_doesnt_raise(self, tmp_path):
        """_archive_entries silently handles write errors (log warning)."""
        from governance.stores.audit import _archive_entries
        # Use a read-only dir to force write failure
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)
        try:
            # Should not raise
            _archive_entries(SAMPLE_ENTRIES[:1], archive_dir=readonly_dir)
        finally:
            readonly_dir.chmod(0o755)


class TestQueryAuditArchive:
    """Tests for query_audit_archive() — reads JSONL files."""

    def _seed_archive(self, archive_dir):
        """Write sample entries to archive files."""
        from governance.stores.audit import _archive_entries
        _archive_entries(SAMPLE_ENTRIES, archive_dir=archive_dir)

    def test_reads_jsonl_filters_by_entity_id(self, archive_dir):
        """query_audit_archive filters by entity_id."""
        from governance.stores.audit import query_audit_archive
        self._seed_archive(archive_dir)
        result = query_audit_archive(entity_id="TASK-001", archive_dir=archive_dir)
        assert len(result) == 2
        for entry in result:
            assert entry["entity_id"] == "TASK-001"

    def test_filters_by_action_type(self, archive_dir):
        """query_audit_archive filters by action_type."""
        from governance.stores.audit import query_audit_archive
        self._seed_archive(archive_dir)
        result = query_audit_archive(action_type="CREATE", archive_dir=archive_dir)
        assert len(result) == 1
        assert result[0]["action_type"] == "CREATE"

    def test_filters_by_date_range(self, archive_dir):
        """query_audit_archive filters by date_from and date_to."""
        from governance.stores.audit import query_audit_archive
        self._seed_archive(archive_dir)
        result = query_audit_archive(
            date_from="2026-03-21", date_to="2026-03-21",
            archive_dir=archive_dir
        )
        assert len(result) == 1
        assert result[0]["entity_id"] == "TASK-002"

    def test_returns_empty_if_no_archive_files(self, archive_dir):
        """query_audit_archive returns empty list if no files exist."""
        from governance.stores.audit import query_audit_archive
        result = query_audit_archive(archive_dir=archive_dir)
        assert result == []

    def test_corrupt_jsonl_lines_skipped(self, archive_dir):
        """query_audit_archive skips corrupt JSONL lines with warning."""
        from governance.stores.audit import query_audit_archive
        # Write a file with one good line and one corrupt line
        f = archive_dir / "2026-03-20.jsonl"
        f.write_text(
            json.dumps(SAMPLE_ENTRIES[0]) + "\n"
            "THIS IS NOT JSON\n"
            + json.dumps(SAMPLE_ENTRIES[1]) + "\n"
        )
        result = query_audit_archive(archive_dir=archive_dir)
        assert len(result) == 2  # 2 good lines, 1 skipped

    def test_respects_limit(self, archive_dir):
        """query_audit_archive respects limit parameter."""
        from governance.stores.audit import query_audit_archive
        self._seed_archive(archive_dir)
        result = query_audit_archive(limit=1, archive_dir=archive_dir)
        assert len(result) == 1
