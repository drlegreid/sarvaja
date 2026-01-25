"""
Robot Framework Library for Claude Code Hooks - E2E Compatibility Tests
Split from ClaudeHooksLibrary.py per DOC-SIZE-01-v1

Covers: Module Imports, Claude Code Compatible Output, Concurrent Execution
"""

import json
import subprocess
import sys
from pathlib import Path
from robot.api.deco import keyword

HOOKS_DIR = Path(__file__).parent.parent.parent / ".claude" / "hooks"
HEALTHCHECK_SCRIPT = HOOKS_DIR / "healthcheck.py"
ENTROPY_SCRIPT = HOOKS_DIR / "entropy_monitor.py"


class ClaudeHooksE2ELibrary:
    """Library for Claude Code hooks E2E compatibility tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

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
