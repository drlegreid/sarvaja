"""
Unit tests for JSONL schema change detection in cc_session_scanner.

Per P2-10f Session 3: Schema resilience — future Claude Code JSONL format
changes must not crash ingestion. TDD: tests written before implementation.

Tests:
- detect_entry_schema() classifies fields per entry
- scan_jsonl_metadata() returns schema_info with fields/versions/warnings
- Unknown fields logged but don't crash
- Missing expected fields logged but don't crash
- Mixed old/new format entries handled gracefully
"""
import json
import logging
import pytest
from pathlib import Path

from tests.fixtures.cc_jsonl_factory import CCJsonlFactory

from governance.services.cc_session_scanner import (
    scan_jsonl_metadata,
    EXPECTED_COMMON_FIELDS,
    EXPECTED_FIELDS_BY_TYPE,
    detect_entry_schema,
)


class TestExpectedFieldConstants:
    """Verify the expected field constants exist and are reasonable."""

    def test_common_fields_is_frozenset(self):
        assert isinstance(EXPECTED_COMMON_FIELDS, frozenset)

    def test_common_fields_include_core(self):
        for field in ("type", "uuid", "timestamp", "sessionId"):
            assert field in EXPECTED_COMMON_FIELDS, f"Missing common field: {field}"

    def test_type_specific_fields_exist(self):
        assert "user" in EXPECTED_FIELDS_BY_TYPE
        assert "assistant" in EXPECTED_FIELDS_BY_TYPE
        assert "system" in EXPECTED_FIELDS_BY_TYPE

    def test_assistant_has_message(self):
        assert "message" in EXPECTED_FIELDS_BY_TYPE["assistant"]

    def test_assistant_has_request_id(self):
        assert "requestId" in EXPECTED_FIELDS_BY_TYPE["assistant"]


class TestDetectEntrySchema:
    """Tests for detect_entry_schema() — per-entry field classification."""

    def test_standard_user_entry_no_unknowns(self):
        factory = CCJsonlFactory()
        entry = factory.make_user_prompt("hello")
        result = detect_entry_schema(entry)
        assert result["entry_type"] == "user"
        assert result["unknown_fields"] == set()

    def test_standard_assistant_entry_no_unknowns(self):
        factory = CCJsonlFactory()
        entry = factory.make_assistant_response("answer")
        result = detect_entry_schema(entry)
        assert result["entry_type"] == "assistant"
        assert result["unknown_fields"] == set()

    def test_unknown_field_detected(self):
        factory = CCJsonlFactory()
        entry = factory.make_user_prompt("hello")
        entry["newClaudeField"] = "some-value"
        entry["experimentalFlag"] = True
        result = detect_entry_schema(entry)
        assert "newClaudeField" in result["unknown_fields"]
        assert "experimentalFlag" in result["unknown_fields"]

    def test_missing_expected_field_detected(self):
        # Simulate an entry missing some expected fields
        entry = {"type": "user", "timestamp": "2026-03-19T10:00:00Z"}
        result = detect_entry_schema(entry)
        assert "uuid" in result["missing_fields"]
        assert "sessionId" in result["missing_fields"]

    def test_system_compaction_entry(self):
        factory = CCJsonlFactory()
        entry = factory.make_compaction(5000)
        result = detect_entry_schema(entry)
        assert result["entry_type"] == "system"
        # compactMetadata is expected for system entries
        assert "compactMetadata" in EXPECTED_FIELDS_BY_TYPE["system"]

    def test_custom_title_entry(self):
        entry = {
            "type": "custom-title",
            "timestamp": "2026-03-19T10:00:00Z",
            "customTitle": "My Session Name",
        }
        result = detect_entry_schema(entry)
        assert result["entry_type"] == "custom-title"

    def test_unknown_entry_type(self):
        entry = {
            "type": "future-event-type",
            "timestamp": "2026-03-19T10:00:00Z",
            "uuid": "abc",
            "data": {"nested": True},
        }
        result = detect_entry_schema(entry)
        assert result["entry_type"] == "future-event-type"
        # For unknown types, all non-common fields are "unknown"
        assert "data" in result["unknown_fields"]

    def test_returns_all_field_names(self):
        factory = CCJsonlFactory()
        entry = factory.make_user_prompt("hello")
        result = detect_entry_schema(entry)
        assert "all_fields" in result
        assert "type" in result["all_fields"]
        assert "uuid" in result["all_fields"]
        assert "message" in result["all_fields"]

    def test_version_extracted(self):
        factory = CCJsonlFactory(version="3.0.0")
        entry = factory.make_user_prompt("hello")
        result = detect_entry_schema(entry)
        assert result["version"] == "3.0.0"

    def test_no_version_returns_none(self):
        entry = {"type": "user", "timestamp": "2026-03-19T10:00:00Z"}
        result = detect_entry_schema(entry)
        assert result["version"] is None


class TestScanJsonlMetadataSchemaInfo:
    """Tests for schema_info field in scan_jsonl_metadata() output."""

    def test_schema_info_present_in_metadata(self, tmp_path):
        """scan_jsonl_metadata() must return schema_info dict."""
        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=2)
        meta = scan_jsonl_metadata(path)
        assert meta is not None
        assert "schema_info" in meta

    def test_schema_info_has_versions(self, tmp_path):
        """schema_info.versions tracks CC version strings seen."""
        factory = CCJsonlFactory(version="2.1.76")
        path = factory.write_session_file(tmp_path, turns=1)
        meta = scan_jsonl_metadata(path)
        assert "2.1.76" in meta["schema_info"]["versions"]

    def test_schema_info_has_entry_types(self, tmp_path):
        """schema_info.entry_types tracks entry types seen."""
        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=2)
        meta = scan_jsonl_metadata(path)
        types = meta["schema_info"]["entry_types"]
        assert "user" in types
        assert "assistant" in types

    def test_schema_info_has_all_fields(self, tmp_path):
        """schema_info.all_fields is the union of all field names seen."""
        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=1)
        meta = scan_jsonl_metadata(path)
        all_fields = meta["schema_info"]["all_fields"]
        assert "type" in all_fields
        assert "uuid" in all_fields
        assert "timestamp" in all_fields

    def test_no_unknown_fields_for_standard_entries(self, tmp_path):
        """Standard CCJsonlFactory entries should produce zero unknown fields."""
        factory = CCJsonlFactory()
        path = factory.write_session_file(tmp_path, turns=3)
        meta = scan_jsonl_metadata(path)
        assert meta["schema_info"]["unknown_fields"] == set()

    def test_unknown_fields_detected_in_scan(self, tmp_path):
        """Entries with extra fields should be captured in unknown_fields."""
        factory = CCJsonlFactory()
        entries = factory.make_full_session(turns=1)
        # Add unknown fields to first entry
        entries[0]["futureField"] = "new-data"
        entries[0]["experimentalMetrics"] = {"tokens": 999}
        path = tmp_path / "unknown-fields.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        assert "futureField" in meta["schema_info"]["unknown_fields"]
        assert "experimentalMetrics" in meta["schema_info"]["unknown_fields"]

    def test_missing_fields_detected_in_scan(self, tmp_path):
        """Entries missing expected fields should be captured."""
        # Write minimal entries missing several expected fields
        entries = [
            {"type": "user", "timestamp": "2026-03-19T10:00:00Z", "message": {"role": "user", "content": []}},
            {"type": "assistant", "timestamp": "2026-03-19T10:01:00Z", "message": {"role": "assistant", "content": []}},
        ]
        path = tmp_path / "missing-fields.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        missing = meta["schema_info"]["missing_fields"]
        # These entries lack uuid, sessionId, version, etc.
        assert "uuid" in missing
        assert "sessionId" in missing

    def test_scan_succeeds_with_extra_fields(self, tmp_path):
        """Extra fields must not crash the scan — metadata still extracted."""
        factory = CCJsonlFactory()
        entries = factory.make_full_session(turns=2)
        for entry in entries:
            entry["v4_streaming_metadata"] = {"chunk_id": 1}
            entry["cache_policy"] = "always"
        path = tmp_path / "extra-fields.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        assert meta is not None
        # Core fields still correctly extracted
        assert meta["user_count"] > 0
        assert meta["assistant_count"] > 0
        assert meta["first_ts"] is not None

    def test_scan_succeeds_with_missing_fields(self, tmp_path):
        """Missing fields must not crash — scan still returns results."""
        entries = [
            {"type": "user", "timestamp": "2026-03-19T10:00:00Z"},
            {"type": "assistant", "timestamp": "2026-03-19T10:01:00Z",
             "message": {"content": [{"type": "text", "text": "hello"}]}},
        ]
        path = tmp_path / "minimal.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        assert meta is not None
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1

    def test_scan_logs_warning_for_unknown_fields(self, tmp_path, caplog):
        """Unknown fields should generate a log warning."""
        factory = CCJsonlFactory()
        entries = factory.make_full_session(turns=1)
        entries[0]["brandNewField"] = True
        path = tmp_path / "warn-unknown.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        with caplog.at_level(logging.INFO, logger="governance.services.cc_session_scanner"):
            meta = scan_jsonl_metadata(path)

        assert meta is not None
        # The warning is logged at INFO level (not ERROR — it's diagnostic, not a failure)
        assert any("unknown" in r.message.lower() or "brandNewField" in r.message
                    for r in caplog.records), (
            f"Expected warning about unknown fields. Got: {[r.message for r in caplog.records]}"
        )

    def test_mixed_versions_tracked(self, tmp_path):
        """Entries from different CC versions are all tracked."""
        entries = [
            {"type": "user", "timestamp": "2026-03-19T10:00:00Z", "version": "2.1.76"},
            {"type": "assistant", "timestamp": "2026-03-19T10:01:00Z", "version": "2.2.0",
             "message": {"content": []}},
        ]
        path = tmp_path / "mixed-ver.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        versions = meta["schema_info"]["versions"]
        assert "2.1.76" in versions
        assert "2.2.0" in versions

    def test_unknown_entry_type_does_not_crash(self, tmp_path):
        """Future entry types (e.g., 'progress', 'error') don't crash scan."""
        entries = [
            {"type": "user", "timestamp": "2026-03-19T10:00:00Z"},
            {"type": "progress", "timestamp": "2026-03-19T10:00:30Z",
             "progressData": {"step": 1, "total": 5}},
            {"type": "error", "timestamp": "2026-03-19T10:01:00Z",
             "errorCode": "RATE_LIMIT", "retryAfter": 30},
            {"type": "assistant", "timestamp": "2026-03-19T10:02:00Z",
             "message": {"content": [{"type": "text", "text": "done"}]}},
        ]
        path = tmp_path / "future-types.jsonl"
        CCJsonlFactory.write_jsonl(entries, path)

        meta = scan_jsonl_metadata(path)
        assert meta is not None
        assert meta["user_count"] == 1
        assert meta["assistant_count"] == 1
        types = meta["schema_info"]["entry_types"]
        assert "progress" in types
        assert "error" in types
