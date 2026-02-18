"""Deep scan batch 174: Hooks + config layer.

Batch 174 findings: 19 total, 3 confirmed fixes, 16 rejected/deferred.
- BUG-RULE-HEALTHY-001: rule_applicability used "healthy" key vs "ok" (always False).
- BUG-AMNESIA-DOCKER-001: amnesia.py checked "DOCKER_DOWN" (stale post-Podman migration).
- BUG-ENTROPY-OVERWRITE-001: entropy_monitor context rot silently overwritten by HIGH check.
"""
import pytest
from pathlib import Path


# ── Rule applicability service key defense ──────────────


class TestRuleApplicabilityServiceKeyDefense:
    """Verify rule_applicability uses correct service dict key."""

    def test_uses_ok_key_not_healthy(self):
        """Service checks use 'ok' key from ServiceChecker."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/rule_applicability.py").read_text()
        assert '.get("ok", False)' in src

    def test_no_healthy_key(self):
        """No residual 'healthy' key usage."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/rule_applicability.py").read_text()
        assert '.get("healthy"' not in src

    def test_service_checker_returns_ok_key(self):
        """ServiceChecker uses 'ok' as the boolean health key."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/services.py").read_text()
        assert '"ok":' in src


# ── Amnesia Podman migration defense ──────────────


class TestAmnesiaDockerMigrationDefense:
    """Verify amnesia detector uses PODMAN_DOWN, not DOCKER_DOWN."""

    def test_no_docker_down_string(self):
        """No residual DOCKER_DOWN string in amnesia.py."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/amnesia.py").read_text()
        assert "DOCKER_DOWN" not in src

    def test_podman_down_present(self):
        """PODMAN_DOWN string is used in amnesia detection."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/checkers/amnesia.py").read_text()
        assert "PODMAN_DOWN" in src

    def test_service_status_enum_has_podman(self):
        """ServiceStatus enum defines PODMAN_DOWN."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/base.py").read_text()
        assert 'PODMAN_DOWN = "PODMAN_DOWN"' in src

    def test_service_status_enum_no_docker(self):
        """ServiceStatus enum does NOT define DOCKER_DOWN."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/core/base.py").read_text()
        assert "DOCKER_DOWN" not in src


# ── Entropy monitor context rot defense ──────────────


class TestEntropyMonitorContextRotDefense:
    """Verify context rot message not silently overwritten."""

    def test_high_threshold_uses_elif(self):
        """HIGH threshold check uses elif (not if) to preserve context rot."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        # After CONTEXT_ROT block, HIGH should use elif
        rot_pos = src.index("CONTEXT_ROT")
        after_rot = src[rot_pos:]
        # First threshold check after CONTEXT_ROT should be elif
        high_check = after_rot.index("HIGH_THRESHOLD")
        before_high = after_rot[high_check - 50:high_check]
        assert "elif" in before_high

    def test_low_threshold_uses_elif(self):
        """LOW threshold also uses elif."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        rot_pos = src.index("CONTEXT_ROT")
        after_rot = src[rot_pos:]
        low_check_idx = after_rot.index("LOW_THRESHOLD")
        before_low = after_rot[low_check_idx - 50:low_check_idx]
        assert "elif" in before_low

    def test_thresholds_defined(self):
        """Both LOW and HIGH thresholds are defined."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/entropy_monitor.py").read_text()
        assert "LOW_THRESHOLD" in src
        assert "HIGH_THRESHOLD" in src


# ── Todo sync stable ID defense ──────────────


class TestTodoSyncStableIDDefense:
    """Verify todo_sync task ID generation is deterministic."""

    def test_id_uses_content_prefix(self):
        """Task ID is based on content prefix."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        assert "TODO-" in src
        assert "content[:40]" in src

    def test_sync_state_file_path(self):
        """Sync state file uses .claude directory."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/todo_sync.py").read_text()
        assert ".claude" in src
        assert "todo_sync_state.json" in src


# ── Hooks watchdog defense ──────────────


class TestHooksWatchdogDefense:
    """Verify healthcheck hooks have timeout protection."""

    def test_prompt_healthcheck_has_watchdog(self):
        """prompt_healthcheck has a watchdog timer."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/prompt_healthcheck.py").read_text()
        assert "threading.Timer" in src

    def test_healthcheck_has_watchdog(self):
        """healthcheck.py has a watchdog timer."""
        root = Path(__file__).parent.parent.parent
        src = (root / ".claude/hooks/healthcheck.py").read_text()
        assert "threading.Timer" in src
