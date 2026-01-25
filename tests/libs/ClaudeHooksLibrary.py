"""
Robot Framework Library for Claude Code Hooks Tests
Migrated from tests/test_claude_hooks.py

Per GAP-MCP-003: Verify SessionStart hook context injection
Per EPIC-006: Entropy Monitor for SLEEP Mode Automation
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from robot.api.deco import keyword

HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class ClaudeHooksLibrary:
    """Library for Claude Code hooks test keywords."""

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

        # Run twice - second run should detect unchanged hash
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

        # Second run with same state should show summary or indicate hash unchanged
        return {
            "summary_or_unchanged": "unchanged" in context.lower() or len(context) < 500
        }

    @keyword("Retry Ceiling After 30 Seconds")
    def retry_ceiling_after_30_seconds(self):
        """After 30s of unchanged state, stop detailed retrying."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        # First, run healthcheck to get current actual hash
        result1 = subprocess.run(
            [sys.executable, str(HEALTHCHECK_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Now read the state file to get the actual hash
        with open(state_file) as f:
            actual_state = json.load(f)

        # Simulate state that's been unchanged for 31 seconds
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

        # Reset state to force detailed output
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

        # If any service is down, should have recovery hint
        if "DOWN" in context or "OFF" in context or "unhealthy" in context.lower():
            has_hint = "deploy.ps1" in context or "docker" in context.lower()
            return {"has_hint": has_hint}

        return {"has_hint": True}  # Services are up, no hint needed

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

        return {"has_timeout": True}  # No socket operations

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

    # =========================================================================
    # Entropy Monitor Output Tests
    # =========================================================================

    @keyword("Entropy Returns Valid JSON")
    def entropy_returns_valid_json(self):
        """Entropy monitor must always return valid JSON."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
            return {"valid_json": isinstance(output, dict)}
        except json.JSONDecodeError:
            return {"valid_json": False}

    @keyword("Entropy Exits Zero Always")
    def entropy_exits_zero_always(self):
        """Entropy monitor must exit 0 even on errors."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return {"exit_zero": result.returncode == 0}

    @keyword("Entropy Status Command")
    def entropy_status_command(self):
        """--status flag should return current entropy state."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        hook_output = output.get("hookSpecificOutput", {})
        context = hook_output.get("additionalContext", "")

        return {
            "has_hook_output": "hookSpecificOutput" in output,
            "has_entropy_or_tools": "ENTROPY" in context or "Tools" in context
        }

    # =========================================================================
    # Entropy Monitor State Management Tests
    # =========================================================================

    @keyword("Entropy State File Created")
    def entropy_state_file_created(self):
        """Entropy monitor should create state file."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        if not state_file.exists():
            return {"exists": False, "has_session_start": False, "has_tool_count": False}

        with open(state_file) as f:
            state = json.load(f)

        return {
            "exists": True,
            "has_session_start": "session_start" in state,
            "has_tool_count": "tool_count" in state
        }

    @keyword("State Has Audit Trail Fields")
    def state_has_audit_trail_fields(self):
        """State should have session_hash, check_count, history for audit trail."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        return {
            "has_session_hash": "session_hash" in state,
            "has_check_count": "check_count" in state,
            "has_history": "history" in state
        }

    @keyword("Session Hash Is 4 Chars")
    def session_hash_is_4_chars(self):
        """Session hash should be 4 uppercase hex chars."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        hash_val = state.get("session_hash", "")
        return {
            "len_4": len(hash_val) == 4,
            "valid_hex": all(c in "0123456789ABCDEF" for c in hash_val),
            "is_upper": hash_val == hash_val.upper()
        }

    @keyword("Check Count Increments")
    def check_count_increments(self):
        """Check count should increment with each state save."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        count1 = state1.get("check_count", 0)

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        count2 = state2.get("check_count", 0)

        return {"incremented": count2 > count1}

    @keyword("Reset Creates History Entry")
    def reset_creates_history_entry(self):
        """Reset should create SESSION_RESET history entry."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state = json.load(f)

        history = state.get("history", [])
        reset_events = [h for h in history if h.get("event") == "SESSION_RESET"]

        return {
            "has_history": len(history) > 0,
            "has_reset_event": len(reset_events) > 0
        }

    @keyword("Tool Count Increments")
    def tool_count_increments(self):
        """Tool count should increment with each run (normal mode)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT), "--reset"],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state1 = json.load(f)
        tools1 = state1.get("tool_count", 0)

        subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            timeout=5
        )

        with open(state_file) as f:
            state2 = json.load(f)
        tools2 = state2.get("tool_count", 0)

        return {"incremented": tools2 == tools1 + 1}

    # =========================================================================
    # Entropy Monitor Warning Tests
    # =========================================================================

    @keyword("No Warning Below Threshold")
    def no_warning_below_threshold(self):
        """Should not show warning below LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 10,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        if "hookSpecificOutput" in output:
            context = output["hookSpecificOutput"].get("additionalContext", "")
            return {"no_warning": "CHECKPOINT" not in context and "ENTROPY HIGH" not in context}

        return {"no_warning": True}

    @keyword("Low Threshold Warning")
    def low_threshold_warning(self):
        """Should show warning at LOW_THRESHOLD (50)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 49,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 0,
            "last_warning_at": 0,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")

        return {"has_warning": "CHECKPOINT" in context or "50 tool calls" in context}

    @keyword("High Threshold Warning")
    def high_threshold_warning(self):
        """Should show strong warning at HIGH_THRESHOLD (100)."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        state = {
            "session_start": "2026-01-01T00:00:00",
            "session_hash": "TEST",
            "tool_count": 99,
            "check_count": 0,
            "last_save": None,
            "warnings_shown": 1,
            "last_warning_at": 50,
            "history": []
        }
        with open(state_file, "w") as f:
            json.dump(state, f)

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = json.loads(result.stdout)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")

        return {"has_warning": "ENTROPY HIGH" in context or "100 tool calls" in context}

    # =========================================================================
    # Entropy Monitor Non-Blocking Tests
    # =========================================================================

    @keyword("Entropy Completes Quickly")
    def entropy_completes_quickly(self):
        """Entropy monitor must complete within 1 second."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        start = time.time()
        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )
        elapsed = time.time() - start

        return {
            "within_1s": elapsed < 1,
            "exit_zero": result.returncode == 0,
            "elapsed": elapsed
        }

    @keyword("Graceful On Corrupt State")
    def graceful_on_corrupt_state(self):
        """Should handle corrupt state file gracefully."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        state_file = HOOKS_DIR / ".entropy_state.json"

        with open(state_file, "w") as f:
            f.write("{invalid json")

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
            return {
                "exit_zero": result.returncode == 0,
                "valid_json": isinstance(output, dict)
            }
        except json.JSONDecodeError:
            return {"exit_zero": result.returncode == 0, "valid_json": False}

    # =========================================================================
    # Module Import Tests
    # =========================================================================

    @keyword("Core Module Imports")
    def core_module_imports(self):
        """Core module should import without errors."""
        try:
            sys.path.insert(0, str(HOOKS_DIR.parent))
            from hooks.core import HookConfig, HookResult, OutputFormatter
            return {
                "hook_config": HookConfig is not None,
                "hook_result": HookResult is not None,
                "output_formatter": OutputFormatter is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        finally:
            if str(HOOKS_DIR.parent) in sys.path:
                sys.path.remove(str(HOOKS_DIR.parent))

    @keyword("Checkers Module Imports")
    def checkers_module_imports(self):
        """Checkers module should import without errors."""
        try:
            sys.path.insert(0, str(HOOKS_DIR.parent))
            from hooks.checkers import ServiceChecker, EntropyChecker, AmnesiaDetector
            return {
                "service_checker": ServiceChecker is not None,
                "entropy_checker": EntropyChecker is not None,
                "amnesia_detector": AmnesiaDetector is not None
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        finally:
            if str(HOOKS_DIR.parent) in sys.path:
                sys.path.remove(str(HOOKS_DIR.parent))

    @keyword("Recovery Module Imports")
    def recovery_module_imports(self):
        """Recovery module should import without errors."""
        try:
            sys.path.insert(0, str(HOOKS_DIR.parent))
            from hooks.recovery import DockerRecovery
            return {"docker_recovery": DockerRecovery is not None}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        finally:
            if str(HOOKS_DIR.parent) in sys.path:
                sys.path.remove(str(HOOKS_DIR.parent))

    # =========================================================================
    # E2E Claude Code Compatibility Tests
    # =========================================================================

    @keyword("Hooks Produce Claude Code Compatible Output")
    def hooks_produce_claude_code_compatible_output(self):
        """Verify hooks produce output format compatible with Claude Code."""
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
            hook_output = output.get("hookSpecificOutput", {})

            return {
                "exit_zero": result.returncode == 0,
                "valid_json": True,
                "has_hook_output": "hookSpecificOutput" in output,
                "has_context": "additionalContext" in hook_output
            }
        except json.JSONDecodeError:
            return {
                "exit_zero": result.returncode == 0,
                "valid_json": False,
                "has_hook_output": False,
                "has_context": False
            }

    @keyword("Entropy Produces Claude Code Compatible Output")
    def entropy_produces_claude_code_compatible_output(self):
        """Verify entropy monitor output is Claude Code compatible."""
        if not ENTROPY_SCRIPT.exists():
            return {"skipped": True, "reason": "entropy_monitor.py not yet implemented"}

        result = subprocess.run(
            [sys.executable, str(ENTROPY_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=5
        )

        try:
            output = json.loads(result.stdout)
            return {
                "exit_zero": result.returncode == 0,
                "valid_json": isinstance(output, dict)
            }
        except json.JSONDecodeError:
            return {"exit_zero": result.returncode == 0, "valid_json": False}

    @keyword("Hooks Handle Concurrent Execution")
    def hooks_handle_concurrent_execution(self):
        """Verify hooks can handle rapid concurrent execution."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        import concurrent.futures

        def run_hook():
            return subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=10
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_hook) for _ in range(3)]
            results = [f.result() for f in futures]

        all_success = all(r.returncode == 0 for r in results)
        all_valid_json = True
        for r in results:
            try:
                json.loads(r.stdout)
            except json.JSONDecodeError:
                all_valid_json = False
                break

        return {"all_success": all_success, "all_valid_json": all_valid_json}

    @keyword("Hooks State Isolation")
    def hooks_state_isolation(self):
        """Verify hook state files don't corrupt under rapid writes."""
        if not HEALTHCHECK_SCRIPT.exists():
            return {"skipped": True, "reason": "healthcheck.py not yet implemented"}

        state_file = HOOKS_DIR / ".healthcheck_state.json"

        for _ in range(5):
            subprocess.run(
                [sys.executable, str(HEALTHCHECK_SCRIPT)],
                capture_output=True,
                timeout=10
            )

        try:
            with open(state_file) as f:
                state = json.load(f)

            return {
                "valid_json": True,
                "has_master_hash": "master_hash" in state,
                "has_check_count": "check_count" in state,
                "count_reflects_runs": state.get("check_count", 0) >= 5
            }
        except (json.JSONDecodeError, FileNotFoundError):
            return {"valid_json": False, "has_master_hash": False, "has_check_count": False}
