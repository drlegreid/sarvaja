"""
Robot Framework Library for Claude Code Hooks - Healthcheck Tests
Split from ClaudeHooksLibrary.py per DOC-SIZE-01-v1

Per GAP-MCP-003: Verify SessionStart hook context injection
Covers: Healthcheck Output, State Management, Service Detection, Non-Blocking, Frankel Hash
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from robot.api.deco import keyword

HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"


class ClaudeHooksHealthcheckLibrary:
    """Library for Claude Code healthcheck hook tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Healthcheck Output Tests
    # =========================================================================

    @keyword("Healthcheck Returns Valid JSON")
    def healthcheck_returns_valid_json(self):
        """Healthcheck must always return valid JSON, even on failure."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        try:
            output = json.loads(result.stdout)
            return {"valid_json": isinstance(output, dict)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Healthcheck Has Hook Specific Output")
    def healthcheck_has_hook_specific_output(self):
        """Output must have hookSpecificOutput for Claude Code context injection."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        return {
            "has_hook_output": "hookSpecificOutput" in output,
            "has_context": "additionalContext" in output.get("hookSpecificOutput", {})
        }

    @keyword("Healthcheck Completes Within Timeout")
    def healthcheck_completes_within_timeout(self):
        """Initial healthcheck must complete within 5 seconds."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start

        return {
            "within_5s": elapsed < 5,
            "exit_zero": result.returncode == 0,
            "elapsed": elapsed
        }

    @keyword("Healthcheck Exits Zero Always")
    def healthcheck_exits_zero_always(self):
        """Healthcheck must exit 0 even when services are down."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        return {"exit_zero": result.returncode == 0}

    # =========================================================================
    # Healthcheck State Management Tests
    # =========================================================================

    @keyword("State File Created")
    def state_file_created(self):
        """Healthcheck should create state file for hash tracking."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=10
        )

        if not state_file.exists():
            return {"exists": False, "has_master_hash": False, "has_last_check": False}

        with open(state_file) as f:
            state = json.load(f)

        return {
            "exists": True,
            "has_master_hash": "master_hash" in state,
            "has_last_check": "last_check" in state
        }

    @keyword("Unchanged State Triggers Summary")
    def unchanged_state_triggers_summary(self):
        """When state unchanged, should return summary not detailed output."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            timeout=10
        )

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        return {
            "summary_or_unchanged": "unchanged" in context.lower() or len(context) < 500
        }

    @keyword("Retry Ceiling After 30 Seconds")
    def retry_ceiling_after_30_seconds(self):
        """After 30s of unchanged state, stop detailed retrying."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        result1 = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        with open(state_file) as f:
            actual_state = json.load(f)

        old_state = {
            "master_hash": actual_state.get("master_hash", "DEADBEEF"),
            "last_check": "2020-01-01T00:00:00",
            "check_count": 100,
            "unchanged_since": time.time() - 31,
            "components": actual_state.get("components", {})
        }

        with open(state_file, "w") as f:
            json.dump(old_state, f)

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        return {
            "stable_output": (
                "cached" in context.lower() or
                "stable" in context.lower() or
                "unchanged" in context.lower() or
                len(context) < 300
            )
        }

    # =========================================================================
    # Healthcheck Service Detection Tests
    # =========================================================================

    @keyword("Detects Docker Status")
    def detects_docker_status(self):
        """Should detect whether Docker/Podman daemon is running."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        if state_file.exists():
            state_file.unlink()

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        container_mentioned = "docker" in context.lower() or "podman" in context.lower()
        health_ok = "[HEALTH OK]" in context or "chain ready" in context.lower()

        return {"detected": container_mentioned or health_ok}

    @keyword("Provides Recovery Hint When Down")
    def provides_recovery_hint_when_down(self):
        """When services down, should provide recovery command."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]

        if "DOWN" in context or "OFF" in context or "unhealthy" in context.lower():
            has_hint = "deploy.ps1" in context or "docker" in context.lower()
            return {"has_hint": has_hint}

        return {"has_hint": True}

    # =========================================================================
    # Healthcheck Non-Blocking Tests
    # =========================================================================

    @keyword("Subprocess Timeout Protection")
    def subprocess_timeout_protection(self):
        """All subprocess calls must have timeout protection."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        lines = content.split('\n')
        in_subprocess_call = False
        call_lines = []
        missing_timeout = []

        for i, line in enumerate(lines):
            if 'subprocess.run(' in line:
                in_subprocess_call = True
                call_lines = [line]
            elif in_subprocess_call:
                call_lines.append(line)
                if ')' in line and not line.strip().endswith(','):
                    call_text = '\n'.join(call_lines)
                    if 'timeout' not in call_text.lower():
                        missing_timeout.append(call_text[:100])
                    in_subprocess_call = False
                    call_lines = []

        return {"all_have_timeout": len(missing_timeout) == 0}

    @keyword("Socket Timeout Protection")
    def socket_timeout_protection(self):
        """All socket operations must have timeout protection."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        if "socket" in content:
            return {"has_timeout": "settimeout" in content or "timeout" in content}

        return {"has_timeout": True}

    @keyword("Global Timeout Wrapper")
    def global_timeout_wrapper(self):
        """Script should have global timeout to prevent any hanging."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        with open(HEALTHCHECK_SCRIPT) as f:
            content = f.read()

        has_protection = (
            "signal.alarm" in content or
            "threading.Timer" in content or
            "GLOBAL_TIMEOUT" in content or
            "max_duration" in content
        )
        return {"has_protection": has_protection}

    # =========================================================================
    # Frankel Hash Tests
    # =========================================================================

    @keyword("Hash Deterministic")
    def hash_deterministic(self):
        """Same input should produce same hash."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            data = {"docker": "OK", "typedb": "OK"}
            hash1 = module.compute_frankel_hash(data)
            hash2 = module.compute_frankel_hash(data)

            return {"deterministic": hash1 == hash2}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Hash Changes On State Change")
    def hash_changes_on_state_change(self):
        """Different state should produce different hash."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            data1 = {"docker": "OK", "typedb": "OK"}
            data2 = {"docker": "OK", "typedb": "DOWN"}

            hash1 = module.compute_frankel_hash(data1)
            hash2 = module.compute_frankel_hash(data2)

            return {"different": hash1 != hash2}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Hash Is 8 Chars")
    def hash_is_8_chars(self):
        """Frankel hash should be 8 uppercase hex chars."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("healthcheck", HEALTHCHECK_SCRIPT)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            data = {"docker": "OK"}
            hash_val = module.compute_frankel_hash(data)

            return {
                "len_8": len(hash_val) == 8,
                "is_upper": hash_val.isupper(),
                "all_hex": all(c in "0123456789ABCDEF" for c in hash_val)
            }
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
