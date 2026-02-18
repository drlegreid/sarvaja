"""
Unit tests for Rule Applicability Checker.

Batch 158a: Tests for .claude/hooks/checkers/rule_applicability.py
- ApplicabilityCheck dataclass
- MANDATORY_RULES / CONDITIONAL_RULES / RECOMMENDED_RULES / FORBIDDEN_PATTERNS
- check_mandatory_rules
- check_forbidden_actions
- check_conditional_rules
- get_applicability_status
- format_for_healthcheck
- get_rule_applicability_summary
"""

import importlib.util
from datetime import datetime
from pathlib import Path

import pytest


def _load_module():
    mod_path = (
        Path(__file__).parent.parent.parent
        / ".claude" / "hooks" / "checkers" / "rule_applicability.py"
    )
    spec = importlib.util.spec_from_file_location("rule_applicability", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
ApplicabilityCheck = _mod.ApplicabilityCheck
MANDATORY_RULES = _mod.MANDATORY_RULES
CONDITIONAL_RULES = _mod.CONDITIONAL_RULES
RECOMMENDED_RULES = _mod.RECOMMENDED_RULES
FORBIDDEN_PATTERNS = _mod.FORBIDDEN_PATTERNS
check_mandatory_rules = _mod.check_mandatory_rules
check_forbidden_actions = _mod.check_forbidden_actions
check_conditional_rules = _mod.check_conditional_rules
get_applicability_status = _mod.get_applicability_status
format_for_healthcheck = _mod.format_for_healthcheck
get_rule_applicability_summary = _mod.get_rule_applicability_summary


# ── ApplicabilityCheck dataclass ──────────────────────────

class TestApplicabilityCheck:
    def test_constructor(self):
        ac = ApplicabilityCheck(
            rule_id="R-1", applicability="MANDATORY",
            check_name="test", status="PASS", message="ok"
        )
        assert ac.rule_id == "R-1"
        assert ac.context is None

    def test_to_dict(self):
        ac = ApplicabilityCheck(
            rule_id="R-1", applicability="FORBIDDEN",
            check_name="chk", status="BLOCK", message="nope",
            context="ctx"
        )
        d = ac.to_dict()
        assert d["rule_id"] == "R-1"
        assert d["applicability"] == "FORBIDDEN"
        assert d["context"] == "ctx"
        datetime.fromisoformat(d["timestamp"])


# ── Constants ─────────────────────────────────────────────

class TestConstants:
    def test_mandatory_has_key_rules(self):
        assert "SESSION-EVID-01-v1" in MANDATORY_RULES
        assert "WORKFLOW-SHELL-01-v1" in MANDATORY_RULES

    def test_conditional_has_structure(self):
        for rule_id, cfg in CONDITIONAL_RULES.items():
            assert "condition" in cfg
            assert "when_true" in cfg
            assert "when_false" in cfg

    def test_recommended_non_empty(self):
        assert len(RECOMMENDED_RULES) >= 10

    def test_forbidden_patterns(self):
        assert "destructive_commands" in FORBIDDEN_PATTERNS
        assert "secret_exposure" in FORBIDDEN_PATTERNS
        for name, cfg in FORBIDDEN_PATTERNS.items():
            assert "patterns" in cfg
            assert "rule_ref" in cfg


# ── check_mandatory_rules ─────────────────────────────────

class TestCheckMandatoryRules:
    def test_empty_context(self):
        results = check_mandatory_rules({})
        assert isinstance(results, list)

    def test_healthy_services_pass(self):
        # BUG-RULE-HEALTHY-001: ServiceChecker uses "ok" key, not "healthy"
        ctx = {
            "services": {
                "typedb": {"ok": True},
                "chromadb": {"ok": True},
            }
        }
        results = check_mandatory_rules(ctx)
        health_check = next(
            r for r in results if r.check_name == "health_check_required"
        )
        assert health_check.status == "PASS"

    def test_unhealthy_services_fail(self):
        ctx = {
            "services": {
                "typedb": {"ok": False},
                "chromadb": {"ok": True},
            }
        }
        results = check_mandatory_rules(ctx)
        health_check = next(
            r for r in results if r.check_name == "health_check_required"
        )
        assert health_check.status == "FAIL"
        assert "MANDATORY" in health_check.message

    def test_bare_python_fails(self):
        ctx = {"command": "python script.py"}
        results = check_mandatory_rules(ctx)
        py_check = next(
            r for r in results if r.check_name == "python3_required"
        )
        assert py_check.status == "FAIL"

    def test_python3_ok(self):
        ctx = {"command": "python3 script.py"}
        results = check_mandatory_rules(ctx)
        py_checks = [r for r in results if r.check_name == "python3_required"]
        assert len(py_checks) == 0  # no violation

    def test_active_session_no_evidence_warning(self):
        ctx = {"session_active": True}
        results = check_mandatory_rules(ctx)
        ev_check = next(
            r for r in results if r.check_name == "evidence_logging"
        )
        assert ev_check.status == "WARNING"


# ── check_forbidden_actions ───────────────────────────────

class TestCheckForbiddenActions:
    def test_safe_command_passes(self):
        results = check_forbidden_actions("ls -la")
        assert results[0].status == "PASS"

    def test_rm_rf_root_blocked(self):
        results = check_forbidden_actions("rm -rf /")
        blocked = [r for r in results if r.status == "BLOCK"]
        assert len(blocked) >= 1
        assert blocked[0].applicability == "FORBIDDEN"

    def test_mkfs_blocked(self):
        results = check_forbidden_actions("mkfs.ext4 /dev/sda1")
        blocked = [r for r in results if r.status == "BLOCK"]
        assert len(blocked) >= 1

    def test_secret_exposure_blocked(self):
        results = check_forbidden_actions("API_KEY = 'abc123'")
        blocked = [r for r in results if r.status == "BLOCK"]
        assert len(blocked) >= 1

    def test_password_exposure_blocked(self):
        results = check_forbidden_actions("PASSWORD = hunter2")
        blocked = [r for r in results if r.status == "BLOCK"]
        assert len(blocked) >= 1


# ── check_conditional_rules ───────────────────────────────

class TestCheckConditionalRules:
    def test_no_context_all_skip(self):
        results = check_conditional_rules({})
        for r in results:
            assert r.status == "SKIP"
            assert r.applicability == "CONDITIONAL"

    def test_halt_requested_triggers(self):
        results = check_conditional_rules({"halt_requested": True})
        halt = next(r for r in results if "halt" in r.check_name)
        assert halt.status == "APPLICABLE"
        assert "HALT" in halt.message

    def test_entropy_high_triggers(self):
        results = check_conditional_rules({"entropy_high": True})
        ent = next(r for r in results if "entropy" in r.check_name)
        assert ent.status == "APPLICABLE"
        assert "Deep Sleep" in ent.message or "DSP" in ent.message

    def test_returns_all_conditional_rules(self):
        results = check_conditional_rules({})
        assert len(results) == len(CONDITIONAL_RULES)


# ── get_applicability_status ──────────────────────────────

class TestGetApplicabilityStatus:
    def test_compliant(self):
        # BUG-RULE-HEALTHY-001: ServiceChecker uses "ok" key, not "healthy"
        ctx = {
            "services": {"typedb": {"ok": True}, "chromadb": {"ok": True}},
            "command": "python3 run.py",
        }
        result = get_applicability_status(ctx)
        assert result["overall_status"] == "COMPLIANT"
        assert "timestamp" in result

    def test_mandatory_violations(self):
        ctx = {
            "services": {"typedb": {"healthy": False}, "chromadb": {"healthy": True}},
        }
        result = get_applicability_status(ctx)
        assert result["overall_status"] == "MANDATORY_VIOLATIONS"
        assert result["mandatory"]["failed"] >= 1

    def test_blocked_overrides(self):
        ctx = {
            "services": {"typedb": {"healthy": True}, "chromadb": {"healthy": True}},
            "command": "rm -rf /",
        }
        result = get_applicability_status(ctx)
        assert result["overall_status"] == "BLOCKED"
        assert result["forbidden"]["blocked"] >= 1

    def test_warnings_status(self):
        ctx = {"session_active": True}
        result = get_applicability_status(ctx)
        assert result["overall_status"] == "WARNINGS"


# ── format_for_healthcheck ────────────────────────────────

class TestFormatForHealthcheck:
    def test_compliant_output(self):
        status = {
            "overall_status": "COMPLIANT",
            "mandatory": {"passed": 2, "failed": 0, "warnings": 0, "checks": []},
            "forbidden": {"blocked": 0, "checks": []},
            "conditional": {"applicable_count": 0, "applicable_rules": []},
        }
        lines = format_for_healthcheck(status)
        text = "\n".join(lines)
        assert "COMPLIANT" in text
        assert "2 passed" in text

    def test_violations_shown(self):
        status = {
            "overall_status": "MANDATORY_VIOLATIONS",
            "mandatory": {
                "passed": 0, "failed": 1, "warnings": 0,
                "checks": [{"rule_id": "R-X", "status": "FAIL", "message": "Bad"}],
            },
            "forbidden": {"blocked": 0, "checks": []},
            "conditional": {"applicable_count": 0, "applicable_rules": []},
        }
        lines = format_for_healthcheck(status)
        text = "\n".join(lines)
        assert "[R-X]" in text

    def test_blocked_shown(self):
        status = {
            "overall_status": "BLOCKED",
            "mandatory": {"passed": 0, "failed": 0, "warnings": 0, "checks": []},
            "forbidden": {
                "blocked": 1,
                "checks": [{"rule_id": "SAFETY", "message": "Destructive"}],
            },
            "conditional": {"applicable_count": 0, "applicable_rules": []},
        }
        lines = format_for_healthcheck(status)
        text = "\n".join(lines)
        assert "BLOCKED" in text
        assert "Destructive" in text

    def test_conditional_shown(self):
        status = {
            "overall_status": "COMPLIANT",
            "mandatory": {"passed": 0, "failed": 0, "warnings": 0, "checks": []},
            "forbidden": {"blocked": 0, "checks": []},
            "conditional": {
                "applicable_count": 1,
                "applicable_rules": [{"rule_id": "COND-1", "message": "Triggered"}],
            },
        }
        lines = format_for_healthcheck(status)
        text = "\n".join(lines)
        assert "Triggered" in text


# ── get_rule_applicability_summary ────────────────────────

class TestGetRuleApplicabilitySummary:
    def test_compliant_summary(self):
        # BUG-RULE-HEALTHY-001: ServiceChecker uses "ok" key, not "healthy"
        ctx = {
            "services": {"typedb": {"ok": True}, "chromadb": {"ok": True}},
        }
        result = get_rule_applicability_summary(ctx)
        assert result["compliant"] is True
        assert result["blocked"] is False
        assert "COMPLIANT" in result["summary"]

    def test_blocked_summary(self):
        ctx = {"command": "rm -rf /"}
        result = get_rule_applicability_summary(ctx)
        assert result["blocked"] is True
        assert "BLOCKED" in result["summary"]

    def test_has_lines(self):
        result = get_rule_applicability_summary({})
        assert isinstance(result["lines"], list)
        assert "raw" in result
