"""
Unit tests for Healthcheck Output Formatters.

Batch 156: Tests for .claude/hooks/healthcheck_formatters.py
- check_dsp_conditions: evidence count, DSP cycle age detection
- format_detailed: full healthcheck output
- format_summary: one-line health status
- format_cached: retry ceiling output
"""

import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest


def _load_formatters():
    """Load the formatters module from hooks directory."""
    mod_path = Path(__file__).parent.parent.parent / ".claude" / "hooks" / "healthcheck_formatters.py"
    spec = importlib.util.spec_from_file_location("healthcheck_formatters", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_fmt = _load_formatters()


# ── check_dsp_conditions ─────────────────────────────────

class TestCheckDspConditions:
    def test_no_evidence_dir(self, tmp_path):
        result = _fmt.check_dsp_conditions(project_root=tmp_path)
        assert result["suggested"] is False
        assert len(result["alerts"]) <= 1  # No DSP cycle alert only

    def test_low_evidence_count(self, tmp_path):
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        for i in range(5):
            (evidence_dir / f"SESSION-2026-02-{i:02d}-TEST.md").touch()
        result = _fmt.check_dsp_conditions(project_root=tmp_path)
        # 5 < 20 threshold, shouldn't trigger accumulation alert
        assert not any("accumulation" in a.lower() for a in result["alerts"])

    def test_high_evidence_count_triggers(self, tmp_path):
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        for i in range(25):
            (evidence_dir / f"SESSION-2026-02-{i:02d}-TEST.md").touch()
        result = _fmt.check_dsp_conditions(project_root=tmp_path)
        assert any("accumulation" in a.lower() or "25" in a for a in result["alerts"])

    def test_no_dsp_cycle_alert(self, tmp_path):
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        result = _fmt.check_dsp_conditions(project_root=tmp_path)
        assert any("No DSP" in a for a in result["alerts"])

    def test_suggested_when_two_alerts(self, tmp_path):
        evidence_dir = tmp_path / "evidence"
        evidence_dir.mkdir()
        # 25 evidence files + no DSP cycle = 2 alerts
        for i in range(25):
            (evidence_dir / f"SESSION-2026-02-{i:02d}-TEST.md").touch()
        result = _fmt.check_dsp_conditions(project_root=tmp_path)
        assert result["suggested"] is True
        assert result["override_needed"] is True


# ── format_detailed ──────────────────────────────────────

class TestFormatDetailed:
    def test_all_ok(self):
        services = {
            "podman": {"ok": True, "status": "OK", "port": ""},
            "typedb": {"ok": True, "status": "OK", "port": "1729"},
            "chromadb": {"ok": True, "status": "OK", "port": "8001"},
        }
        result = _fmt.format_detailed(
            services, master_hash="ABCD1234",
            component_hashes={"podman": "1111", "typedb": "2222", "chromadb": "3333"},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "ABCD1234" in result
        assert "TYPEDB" in result
        assert "CHROMADB" in result

    def test_dsp_warning_shown(self):
        services = {"podman": {"ok": True, "status": "OK"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            dsp_info={"suggested": True, "alerts": ["High entropy"]},
        )
        assert "DSP REQUIRED" in result
        assert "High entropy" in result

    def test_starting_services(self):
        services = {"typedb": {"ok": False, "is_starting": True, "status": "STARTING"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            core_services=["typedb"],
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "SERVICES STARTING" in result

    def test_amnesia_warning(self):
        services = {"podman": {"ok": True, "status": "OK"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            amnesia={"detected": True, "confidence": 0.85, "indicators": ["context gap"]},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "AMNESIA RISK" in result
        assert "85%" in result

    def test_entropy_high(self):
        services = {"podman": {"ok": True, "status": "OK"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            entropy={"tool_count": 120, "minutes": 60, "entropy": "HIGH"},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "120" in result
        assert "/save" in result

    def test_recovery_actions(self):
        services = {"typedb": {"ok": False, "status": "DOWN"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            core_services=["typedb"],
            recovery_actions=["podman restart typedb"],
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "Auto-Recovery" in result
        assert "podman restart typedb" in result

    def test_mcp_usage(self):
        services = {"podman": {"ok": True, "status": "OK"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            mcp_usage={"mcp_categories": {"gov-tasks": 5}, "todowrite_count": 2, "warnings_issued": 0},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "gov-tasks=5" in result
        assert "TodoWrite=2" in result

    def test_zombie_cleanup(self):
        services = {"podman": {"ok": True, "status": "OK"}}
        result = _fmt.format_detailed(
            services, master_hash="XX",
            zombies={"cleaned": 3, "action_required": False, "memory_pct": 50},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "Killed 3" in result


# ── format_summary ───────────────────────────────────────

class TestFormatSummary:
    def test_all_ok(self):
        services = {
            "podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True},
        }
        result = _fmt.format_summary(
            services, master_hash="ABCD",
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "[HEALTH OK]" in result
        assert "ABCD" in result

    def test_service_down(self):
        services = {
            "podman": {"ok": True}, "typedb": {"ok": False}, "chromadb": {"ok": True},
        }
        result = _fmt.format_summary(
            services, master_hash="ABCD",
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "[HEALTH WARN]" in result
        assert "typedb" in result

    def test_with_recovery_actions(self):
        services = {"typedb": {"ok": False}}
        result = _fmt.format_summary(
            services, master_hash="XX",
            core_services=["typedb"],
            recovery_actions=["restarting typedb"],
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "[HEALTH RECOVERING]" in result

    def test_amnesia_suffix(self):
        services = {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}}
        result = _fmt.format_summary(
            services, master_hash="XX",
            amnesia={"detected": True, "confidence": 0.9},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "AMNESIA RISK 90%" in result

    def test_dsp_suffix(self):
        services = {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}}
        result = _fmt.format_summary(
            services, master_hash="XX",
            dsp_info={"suggested": True, "alerts": ["test"]},
        )
        assert "DSP REQUIRED" in result

    def test_zombie_suffix(self):
        services = {"podman": {"ok": True}, "typedb": {"ok": True}, "chromadb": {"ok": True}}
        result = _fmt.format_summary(
            services, master_hash="XX",
            zombies={"cleaned": 5, "stale_count": 0, "memory_pct": 50},
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "cleaned 5 zombies" in result

    def test_auto_recovery_disabled(self):
        services = {"typedb": {"ok": False}}
        result = _fmt.format_summary(
            services, master_hash="XX",
            core_services=["typedb"],
            auto_recovery_enabled=False,
            dsp_info={"suggested": False, "alerts": []},
        )
        assert "AUTO-RECOVERY DISABLED" in result


# ── format_cached ────────────────────────────────────────

class TestFormatCached:
    def test_all_ok(self):
        prev = {"master_hash": "ABCD", "components": {"podman": "OK", "typedb": "OK"}}
        result = _fmt.format_cached(prev)
        assert "[CACHED]" in result
        assert "MCP chain ready" in result

    def test_failed_service(self):
        prev = {"master_hash": "ABCD", "components": {"typedb": "DOWN"}}
        result = _fmt.format_cached(prev, core_services=["typedb"])
        assert "[CACHED]" in result
        assert "typedb" in result
        assert "podman compose" in result

    def test_missing_hash_defaults(self):
        result = _fmt.format_cached({})
        assert "????????" in result
