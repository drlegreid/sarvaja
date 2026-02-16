"""
Unit tests for Tab Deep Scan Batch 35 — Chat commands + DSM evidence + repair + scanner + preloader.

Covers: BUG-CMD-001 (LLM response crash), BUG-CMD-002 (operator precedence),
BUG-CMD-003 (silent exception), BUG-DSM-001 (findings KeyError),
BUG-DSM-002 (evidence write guard), BUG-REPAIR-002 (fixes KeyError),
BUG-SCANNER-001 (build_session_id defensive), BUG-PRELOADER-001 (silent phase detection).
Per TEST-E2E-01-v1: Tier 1 unit tests for data flow changes.
"""

import inspect
from unittest.mock import patch, MagicMock


# ── BUG-CMD-001: LLM response safe access ──────────────────────────


class TestLLMResponseSafeAccess:
    """query_llm must not crash on malformed LLM responses."""

    def test_no_bare_bracket_access(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.query_llm)
        # Should NOT have direct data["choices"][0] pattern
        assert 'data["choices"][0]' not in source

    def test_uses_get_for_choices(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.query_llm)
        assert '.get("choices")' in source

    def test_empty_choices_returns_message(self):
        """Empty choices array should return fallback, not crash."""
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": []}
        with patch("httpx.post", return_value=mock_resp):
            result = query_llm("test")
        assert "empty" in result.lower() or "no response" in result.lower()

    def test_missing_message_key(self):
        """Missing 'message' key should return fallback, not crash."""
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"index": 0}]}
        with patch("httpx.post", return_value=mock_resp):
            result = query_llm("test")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_valid_response_works(self):
        """Normal LLM response still works correctly."""
        from governance.routes.chat.commands import query_llm
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}]
        }
        with patch("httpx.post", return_value=mock_resp):
            result = query_llm("test")
        assert result == "Hello world"

    def test_bugfix_marker(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.query_llm)
        assert "BUG-CMD-001" in source


# ── BUG-CMD-002: Operator precedence in search ───────────────────────


class TestSearchOperatorPrecedence:
    """Rule search must concatenate name AND directive, not short-circuit."""

    def test_has_correct_parentheses(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.process_chat_command)
        # Must have explicit parentheses around (rule.name or "")
        assert '(rule.name or "")' in source

    def test_directive_included_in_search(self):
        """When rule.name is truthy, directive must still be searched."""
        # Simulate the corrected vs broken expression
        class FakeRule:
            name = "SomeRule"
            directive = "Always validate inputs"

        rule = FakeRule()
        # CORRECT expression (what the fix does):
        correct = ((rule.name or "") + (rule.directive or "")).lower()
        assert "validate" in correct

        # BROKEN expression (what the old code did):
        # Due to + binding tighter than or, this returns just rule.name
        broken = (rule.name or "" + rule.directive or "").lower()
        assert "validate" not in broken  # Proves the old code was wrong

    def test_bugfix_marker(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.process_chat_command)
        assert "BUG-CMD-002" in source


# ── BUG-CMD-003: Silent exception logging ────────────────────────────


class TestChatSessionsExceptionLogging:
    """Recent sessions query must log exceptions, not silently swallow."""

    def test_no_bare_except_pass(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.process_chat_command)
        # The old pattern was: except Exception:\n            pass
        # After fix, it should log
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "except Exception" in line and "recent" not in line.lower():
                continue
            if "except Exception:" in line.strip() and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                assert next_line != "pass", f"Silent except:pass at line {i}"

    def test_bugfix_marker(self):
        from governance.routes.chat import commands
        source = inspect.getsource(commands.process_chat_command)
        assert "BUG-CMD-003" in source


# ── BUG-DSM-001: Evidence findings KeyError ──────────────────────────


class TestDSMEvidenceFindings:
    """Evidence generation must use .get() for finding fields."""

    def test_uses_get_for_description(self):
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        assert ".get('description'" in source

    def test_uses_get_for_id(self):
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        assert ".get('id'" in source

    def test_malformed_finding_no_crash(self):
        """Finding without standard keys should not crash."""
        from governance.dsm.evidence import generate_evidence
        from governance.dsm.models import DSMCycle
        import tempfile
        from pathlib import Path

        cycle = DSMCycle(
            cycle_id="DSM-TEST-001",
            findings=[{"custom_field": "value"}],  # Missing id, type, severity, description
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_evidence(cycle, Path(tmpdir))
            assert result.endswith(".md")
            content = Path(result).read_text()
            assert "N/A" in content  # Default values used

    def test_bugfix_marker(self):
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        assert "BUG-DSM-001" in source


# ── BUG-DSM-002: Evidence write guard ────────────────────────────────


class TestDSMEvidenceWriteGuard:
    """Evidence file write must handle IOError."""

    def test_has_try_except_on_write(self):
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        assert "IOError" in source or "OSError" in source

    def test_bugfix_marker(self):
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        assert "BUG-DSM-002" in source


# ── BUG-REPAIR-002: Missing fixes key ───────────────────────────────


class TestRepairApplyFixesGuard:
    """apply_repair must handle missing 'fixes' key."""

    def test_uses_get_for_fixes(self):
        from governance.services import session_repair
        source = inspect.getsource(session_repair.apply_repair)
        assert '.get("fixes"' in source

    def test_missing_fixes_key_no_crash(self):
        """Plan item without 'fixes' key should not KeyError."""
        from governance.services.session_repair import apply_repair
        result = apply_repair({"session_id": "SESSION-TEST"}, dry_run=True)
        assert result["applied"] is False
        assert result["fixes"] == {}

    def test_update_failure_caught(self):
        """Update session failure should return error, not crash."""
        from governance.services.session_repair import apply_repair
        # Patch at source — apply_repair imports update_session lazily
        with patch("governance.services.sessions.update_session", side_effect=RuntimeError("DB down")):
            result = apply_repair(
                {"session_id": "SESSION-TEST", "fixes": {"agent_id": "code-agent"}},
                dry_run=False,
            )
        assert result["applied"] is False
        assert "error" in result

    def test_bugfix_marker(self):
        from governance.services import session_repair
        source = inspect.getsource(session_repair.apply_repair)
        assert "BUG-REPAIR-002" in source


# ── BUG-SCANNER-001: Defensive build_session_id ─────────────────────


class TestBuildSessionIdDefensive:
    """build_session_id must handle missing meta keys."""

    def test_uses_get_for_first_ts(self):
        from governance.services import cc_session_scanner
        source = inspect.getsource(cc_session_scanner.build_session_id)
        assert '.get("first_ts"' in source

    def test_uses_get_for_slug(self):
        from governance.services import cc_session_scanner
        source = inspect.getsource(cc_session_scanner.build_session_id)
        assert '.get("slug"' in source

    def test_empty_meta_no_crash(self):
        """Empty metadata dict should not crash."""
        from governance.services.cc_session_scanner import build_session_id
        result = build_session_id({}, "test-project")
        assert result.startswith("SESSION-")
        assert "UNKNOWN" in result

    def test_normal_meta_works(self):
        """Normal metadata produces correct ID."""
        from governance.services.cc_session_scanner import build_session_id
        meta = {"first_ts": "2026-02-15T10:00:00", "slug": "my-session"}
        result = build_session_id(meta, "test-project")
        assert result == "SESSION-2026-02-15-CC-MY-SESSION"

    def test_bugfix_marker(self):
        from governance.services import cc_session_scanner
        source = inspect.getsource(cc_session_scanner.build_session_id)
        assert "BUG-SCANNER-001" in source


# ── BUG-PRELOADER-001: Phase detection logging ──────────────────────


class TestPreloaderPhaseDetectionLogging:
    """Phase detection must log exceptions, not silently skip."""

    def test_no_bare_except_continue(self):
        from governance.context_preloader import preloader
        source = inspect.getsource(preloader.ContextPreloader._detect_active_phase)
        # Should not have bare except: continue (should have logging)
        assert "logger.debug" in source

    def test_bugfix_marker(self):
        from governance.context_preloader import preloader
        source = inspect.getsource(preloader.ContextPreloader._detect_active_phase)
        assert "BUG-PRELOADER-001" in source


# ── Cross-layer consistency ──────────────────────────────────────────


class TestCrossLayerConsistencyBatch35:
    """Cross-cutting patterns must be consistent."""

    def test_chat_commands_no_bare_except_pass(self):
        """No silent exception swallowing in chat commands."""
        from governance.routes.chat import commands
        source = inspect.getsource(commands)
        lines = source.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("except") and "Exception" in stripped and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line == "pass":
                    assert False, f"Silent except:pass found at line {i+1}"

    def test_dsm_evidence_all_fields_safe(self):
        """All finding field accesses should use .get()."""
        from governance.dsm import evidence
        source = inspect.getsource(evidence.generate_evidence)
        # Should not have any f['key'] pattern for findings
        assert "f['description']" not in source
        assert "f['id']" not in source
        assert "f['type']" not in source
        assert "f['severity']" not in source
