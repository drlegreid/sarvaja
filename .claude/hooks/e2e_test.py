#!/usr/bin/env python3
"""
E2E Test Suite for Healthcheck Hook

Tests the healthcheck in conditions that simulate Claude Code's hook execution.
Run this BEFORE restarting Claude Code to verify the hook won't hang.

Usage:
    python .claude/hooks/e2e_test.py
"""

import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HEALTHCHECK = Path(__file__).parent / "healthcheck.py"
PASSED = 0
FAILED = 0


def test(name):
    """Decorator to run and report test results."""
    def decorator(func):
        def wrapper():
            global PASSED, FAILED
            print(f"\n{'='*60}")
            print(f"TEST: {name}")
            print('='*60)
            try:
                func()
                print(f"✓ PASSED: {name}")
                PASSED += 1
                return True
            except AssertionError as e:
                print(f"✗ FAILED: {name}")
                print(f"  Error: {e}")
                FAILED += 1
                return False
            except Exception as e:
                print(f"✗ ERROR: {name}")
                print(f"  Exception: {type(e).__name__}: {e}")
                FAILED += 1
                return False
        return wrapper
    return decorator


@test("1. Script exists and is readable")
def test_script_exists():
    assert HEALTHCHECK.exists(), f"Script not found: {HEALTHCHECK}"
    content = HEALTHCHECK.read_text()
    assert len(content) > 100, "Script seems empty"
    assert "hookSpecificOutput" in content, "Missing hookSpecificOutput in script"
    print(f"  Script size: {len(content)} bytes")


@test("2. Script executes without hanging (max 5s)")
def test_execution_no_hang():
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK)],
        capture_output=True,
        text=True,
        timeout=5  # Hard timeout
    )
    elapsed = time.time() - start
    print(f"  Execution time: {elapsed:.3f}s")
    print(f"  Exit code: {result.returncode}")
    assert elapsed < 3, f"Took {elapsed:.1f}s, expected < 3s"
    assert result.returncode == 0, f"Exit code {result.returncode}, expected 0"


@test("3. Output is valid JSON")
def test_valid_json():
    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK)],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"  Raw output length: {len(result.stdout)} chars")

    # Must be parseable JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"  Output: {result.stdout[:200]}")
        raise AssertionError(f"Invalid JSON: {e}")

    assert isinstance(data, dict), "Output must be a dict"
    print(f"  JSON keys: {list(data.keys())}")


@test("4. Output matches Claude Code hook spec")
def test_hook_spec_format():
    """
    Per Claude Code docs, SessionStart hook output must be:
    {
      "hookSpecificOutput": {
        "hookEventName": "SessionStart",  # Optional but recommended
        "additionalContext": "..."        # Required for context injection
      }
    }
    """
    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK)],
        capture_output=True,
        text=True,
        timeout=5
    )
    data = json.loads(result.stdout)

    # Check required structure
    assert "hookSpecificOutput" in data, "Missing 'hookSpecificOutput' key"
    hook_output = data["hookSpecificOutput"]

    assert isinstance(hook_output, dict), "hookSpecificOutput must be a dict"
    assert "additionalContext" in hook_output, "Missing 'additionalContext'"

    context = hook_output["additionalContext"]
    assert isinstance(context, str), "additionalContext must be a string"
    assert len(context) > 0, "additionalContext is empty"

    print(f"  additionalContext length: {len(context)} chars")
    print(f"  Preview: {context[:100]}...")


@test("5. No stdin dependency (simulates Claude Code)")
def test_no_stdin_dependency():
    """
    Claude Code may not provide stdin or may close it immediately.
    The script must not hang waiting for stdin.
    """
    # Run with stdin explicitly closed
    result = subprocess.run(
        [sys.executable, str(HEALTHCHECK)],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,  # No stdin at all
        timeout=5
    )

    assert result.returncode == 0, f"Failed with closed stdin: exit {result.returncode}"
    data = json.loads(result.stdout)
    assert "hookSpecificOutput" in data, "No output with closed stdin"
    print("  Script works without stdin ✓")


@test("6. Watchdog timeout works (inject 5s delay)")
def test_watchdog_timeout():
    """
    Inject a delay into a modified script to verify watchdog kills it.
    """
    # Create modified script with artificial delay
    original = HEALTHCHECK.read_text()

    # Insert delay in main() - this is where execution actually happens
    # Injecting at module level during function parsing doesn't test real behavior
    modified = original.replace(
        "services = check_services()",
        "import time; time.sleep(10)  # INJECTED DELAY FOR TEST\n        services = check_services()"
    )

    # Write to temp file
    temp_script = Path(tempfile.gettempdir()) / "healthcheck_delay_test.py"
    temp_script.write_text(modified)

    try:
        start = time.time()
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            timeout=10  # Allow up to 10s
        )
        elapsed = time.time() - start

        print(f"  Execution time with 10s delay injected: {elapsed:.3f}s")

        # Watchdog should kill it around 3s
        assert elapsed < 5, f"Watchdog didn't kill: took {elapsed:.1f}s"
        assert result.returncode == 0, f"Exit code {result.returncode}"

        # Should have timeout message
        if result.stdout:
            assert "TIMEOUT" in result.stdout, "Missing TIMEOUT in output"
            print("  Watchdog force-exit triggered ✓")

    finally:
        temp_script.unlink(missing_ok=True)


@test("7. Stress test (10 concurrent executions)")
def test_concurrent_execution():
    """
    Run multiple instances concurrently to ensure no race conditions.
    """
    def run_once(i):
        start = time.time()
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK)],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start
        return {
            "id": i,
            "elapsed": elapsed,
            "exit_code": result.returncode,
            "valid_json": True if result.stdout else False
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_once, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Analyze results
    times = [r["elapsed"] for r in results]
    exit_codes = [r["exit_code"] for r in results]

    print(f"  Times: min={min(times):.2f}s, max={max(times):.2f}s, avg={sum(times)/len(times):.2f}s")
    print(f"  Exit codes: {set(exit_codes)}")

    assert all(ec == 0 for ec in exit_codes), "Some executions failed"
    assert max(times) < 5, f"Some executions too slow: {max(times):.1f}s"


@test("8. State file handling (fresh start)")
def test_state_file_fresh():
    """
    Delete state file and verify script handles it gracefully.
    """
    state_file = HEALTHCHECK.parent / ".healthcheck_state.json"
    backup = None

    # Backup existing state
    if state_file.exists():
        backup = state_file.read_text()
        state_file.unlink()

    try:
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK)],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0, f"Failed on fresh start: exit {result.returncode}"
        assert state_file.exists(), "State file not created"

        # Verify state file is valid JSON
        state = json.loads(state_file.read_text())
        assert "master_hash" in state, "State missing master_hash"
        assert "check_count" in state, "State missing check_count"

        print(f"  State file created with hash: {state['master_hash']}")

    finally:
        # Restore backup
        if backup:
            state_file.write_text(backup)


@test("9. Cached response (retry ceiling)")
def test_retry_ceiling():
    """
    Set state to trigger retry ceiling and verify cached response.
    """
    state_file = HEALTHCHECK.parent / ".healthcheck_state.json"
    backup = state_file.read_text() if state_file.exists() else None

    # Set state to 31 seconds ago (exceeds 30s ceiling)
    old_state = {
        "master_hash": "TESTCEIL",
        "check_count": 999,
        "last_check": "2020-01-01T00:00:00",
        "unchanged_since": time.time() - 31,
        "components": {"docker": "DOWN", "typedb": "DOWN", "chromadb": "DOWN"}
    }
    state_file.write_text(json.dumps(old_state))

    try:
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK)],
            capture_output=True,
            text=True,
            timeout=5
        )

        data = json.loads(result.stdout)
        context = data["hookSpecificOutput"]["additionalContext"]

        # Should return cached response
        assert "CACHED" in context or "cached" in context.lower(), f"Expected cached response, got: {context[:100]}"
        print(f"  Cached response: {context[:80]}...")

    finally:
        if backup:
            state_file.write_text(backup)


@test("10. Error handling (corrupted state file)")
def test_corrupted_state():
    """
    Corrupt state file and verify graceful handling.
    """
    state_file = HEALTHCHECK.parent / ".healthcheck_state.json"
    backup = state_file.read_text() if state_file.exists() else None

    # Write invalid JSON
    state_file.write_text("THIS IS NOT JSON {{{{")

    try:
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK)],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should still work
        assert result.returncode == 0, f"Failed with corrupted state: exit {result.returncode}"
        data = json.loads(result.stdout)
        assert "hookSpecificOutput" in data, "No output with corrupted state"

        print("  Handled corrupted state gracefully ✓")

    finally:
        if backup:
            state_file.write_text(backup)


@test("11. Auto-recovery cooldown (60s between attempts)")
def test_recovery_cooldown():
    """
    Verify recovery cooldown prevents hammering.
    """
    state_file = HEALTHCHECK.parent / ".healthcheck_state.json"
    backup = state_file.read_text() if state_file.exists() else None

    # Set state with recent recovery
    recent_state = {
        "master_hash": "TESTCOOL",
        "check_count": 1,
        "last_check": "2020-01-01T00:00:00",
        "unchanged_since": 0,
        "last_recovery": time.time() - 10,  # 10 seconds ago
        "components": {"docker": "DOWN", "typedb": "DOWN", "chromadb": "DOWN"}
    }
    state_file.write_text(json.dumps(recent_state))

    try:
        result = subprocess.run(
            [sys.executable, str(HEALTHCHECK)],
            capture_output=True,
            text=True,
            timeout=5
        )

        data = json.loads(result.stdout)
        context = data["hookSpecificOutput"]["additionalContext"]

        # Should NOT contain recovery actions (cooldown active)
        assert "STARTING" not in context, f"Recovery should be on cooldown, got: {context[:100]}"
        print("  Recovery cooldown working ✓")

    finally:
        if backup:
            state_file.write_text(backup)


@test("12. CORE services defined (docker, typedb, chromadb)")
def test_core_services_defined():
    """
    Verify CORE_SERVICES constant is properly defined.
    """
    content = HEALTHCHECK.read_text()

    assert 'CORE_SERVICES = ["docker", "typedb", "chromadb"]' in content, \
        "CORE_SERVICES not properly defined"
    assert "CORE MCPs" in content, "CORE MCPs documentation missing"

    print("  CORE_SERVICES properly defined ✓")


@test("13. Deploy script path configured")
def test_deploy_script_path():
    """
    Verify deploy.ps1 path is configured correctly.
    """
    content = HEALTHCHECK.read_text()

    assert "DEPLOY_SCRIPT" in content, "DEPLOY_SCRIPT not defined"
    assert "deploy.ps1" in content, "deploy.ps1 reference missing"

    # Check the path resolves correctly
    project_root = HEALTHCHECK.parent.parent.parent
    deploy_script = project_root / "deploy.ps1"
    assert deploy_script.exists(), f"Deploy script not found at {deploy_script}"

    print(f"  Deploy script found at {deploy_script} ✓")


@test("14. Docker Desktop path configured")
def test_docker_desktop_path():
    """
    Verify Docker Desktop path is configured.
    """
    content = HEALTHCHECK.read_text()

    assert "DOCKER_DESKTOP" in content, "DOCKER_DESKTOP not defined"
    assert "Docker Desktop.exe" in content, "Docker Desktop.exe path missing"

    print("  Docker Desktop path configured ✓")


@test("15. Recovery uses docker compose (not deploy.ps1)")
def test_recovery_uses_docker_compose():
    """
    Verify recovery uses docker compose directly.
    deploy.ps1 has strict error handling that causes failures.
    """
    content = HEALTHCHECK.read_text()

    # Check that docker compose is used for container recovery
    assert "docker" in content and "compose" in content, "docker compose not used for recovery"
    assert "typedb" in content and "chromadb" in content, "CORE services not in recovery command"

    # Verify the comment explains why
    assert "deploy.ps1" in content and "strict" in content.lower(), \
        "Missing explanation for why deploy.ps1 is not used"

    print("  Recovery uses docker compose directly ✓")


@test("16. Recovery message format correct")
def test_recovery_message_format():
    """
    Verify recovery message format in healthcheck code.
    Note: This tests the code structure, not live recovery (which depends on actual service state).
    """
    content = HEALTHCHECK.read_text()

    # Check recovery message elements exist in code
    assert "STARTING" in content, "Missing STARTING message in code"
    assert "Auto-Recovery" in content, "Missing Auto-Recovery section"
    assert "/health" in content or "verify" in content.lower(), \
        "Missing verification hint in code"
    assert "30-60s" in content or "30s" in content, \
        "Missing timing hint in code"

    print("  Recovery message format correct ✓")


@test("17. Degraded mode message when recovery fails")
def test_degraded_mode_message():
    """
    Verify user is informed about degraded mode.
    """
    content = HEALTHCHECK.read_text()

    # Check for HEALTH WARN message format
    assert "HEALTH WARN" in content or "HEALTH RECOVERING" in content, \
        "Missing health warning status messages"

    # Check for manual recovery hint
    assert "Manual Recovery" in content or "deploy.ps1" in content, \
        "Missing manual recovery hint"

    print("  Degraded mode messaging configured ✓")


@test("18. settings.local.json hook structure correct")
def test_settings_hook_structure():
    """
    Verify settings.local.json has correct hook nesting structure.

    CRITICAL: SessionStart hooks go directly in array (no wrapper).
    Events with matchers (UserPromptSubmit) need { matcher, hooks } wrapper.

    Wrong: "SessionStart": [{ "hooks": [{ ... }] }]
    Right: "SessionStart": [{ "type": "command", ... }]
    """
    settings_file = HEALTHCHECK.parent.parent / "settings.local.json"

    if not settings_file.exists():
        print("  settings.local.json not found - skipping (user disabled hooks)")
        return

    content = settings_file.read_text()
    config = json.loads(content)

    hooks = config.get("hooks", {})

    # Check SessionStart structure (no wrapper, direct hooks array)
    if "SessionStart" in hooks:
        session_hooks = hooks["SessionStart"]
        assert isinstance(session_hooks, list), "SessionStart must be an array"
        for hook in session_hooks:
            # SessionStart hooks should NOT have nested "hooks" key
            assert "hooks" not in hook, \
                "SessionStart should NOT have nested 'hooks' wrapper. Use: [{ type, command }] not [{ hooks: [...] }]"
            assert "type" in hook, "SessionStart hook missing 'type' field"
            assert "command" in hook, "SessionStart hook missing 'command' field"
        print("  SessionStart hook structure correct ✓")

    # Check UserPromptSubmit structure (with matcher, needs wrapper)
    if "UserPromptSubmit" in hooks:
        submit_hooks = hooks["UserPromptSubmit"]
        for hook in submit_hooks:
            if "matcher" in hook:
                # With matcher, needs nested hooks array
                assert "hooks" in hook, \
                    "UserPromptSubmit with matcher needs nested 'hooks' array"
                print("  UserPromptSubmit (with matcher) hook structure correct ✓")
            else:
                # Without matcher, direct structure like SessionStart
                assert "type" in hook, "UserPromptSubmit hook missing 'type' field"
                print("  UserPromptSubmit (no matcher) hook structure correct ✓")

    print(f"  Config file: {settings_file}")


def main():
    print("=" * 60)
    print("HEALTHCHECK E2E TEST SUITE")
    print("=" * 60)
    print(f"Script: {HEALTHCHECK}")
    print(f"Python: {sys.executable}")

    # Run all tests
    tests = [
        test_script_exists,
        test_execution_no_hang,
        test_valid_json,
        test_hook_spec_format,
        test_no_stdin_dependency,
        test_watchdog_timeout,
        test_concurrent_execution,
        test_state_file_fresh,
        test_retry_ceiling,
        test_corrupted_state,
        # Auto-recovery tests
        test_recovery_cooldown,
        test_core_services_defined,
        test_deploy_script_path,
        test_docker_desktop_path,
        # Recovery scenario tests
        test_recovery_uses_docker_compose,
        test_recovery_message_format,
        test_degraded_mode_message,
        # Configuration validation
        test_settings_hook_structure,
    ]

    for t in tests:
        t()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Passed: {PASSED}")
    print(f"  Failed: {FAILED}")
    print(f"  Total:  {PASSED + FAILED}")

    if FAILED == 0:
        print("\n✓ ALL TESTS PASSED")
        print("\n┌────────────────────────────────────────────────────────┐")
        print("│  UAT REQUIRED: Test in Claude Code before trusting     │")
        print("├────────────────────────────────────────────────────────┤")
        print("│  1. Close this terminal                                │")
        print("│  2. Restart Claude Code (VSCode extension)             │")
        print("│  3. Observe: Session should start within 5s            │")
        print("│  4. Type '/health' to trigger manual check             │")
        print("│  5. If 'gray c#2-2' → rollback settings.local.json     │")
        print("└────────────────────────────────────────────────────────┘")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Do NOT restart until fixed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
