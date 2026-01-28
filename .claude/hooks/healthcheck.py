#!/usr/bin/env python3
"""
Session Start Healthcheck - Non-Blocking with Auto-Recovery

Per RULE-021, GAP-MCP-003: Validates MCP dependency chain with:
- 30-second retry ceiling when state unchanged
- 3-second max execution time (never blocks Claude Code)
- Always returns valid JSON (graceful degradation)
- Hash-based incremental checking (Frankel hash)
- Auto-recovery: Starts containers in background

Platform: Linux (xubuntu) with Podman - migrated 2026-01-09

Chain: Claude Code → claude-mem MCP → governance MCP → TypeDB/ChromaDB (Podman)

CORE MCPs (must be running for governance):
- TypeDB (port 1729) - Rule inference engine
- ChromaDB (port 8001) - Semantic search for claude-mem
"""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for shared module imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import shared health check utilities (RULE-032: Shared modules)
try:
    from governance.health import check_amnesia_indicators as shared_amnesia_check
    SHARED_HEALTH_AVAILABLE = True
except ImportError:
    SHARED_HEALTH_AVAILABLE = False

# Import intent checker for session continuity (RD-INTENT Phase 3)
try:
    # Use importlib for reliable import regardless of execution context
    import importlib.util
    _intent_checker_path = Path(__file__).parent / "checkers" / "intent_checker.py"
    _intent_spec = importlib.util.spec_from_file_location("intent_checker", _intent_checker_path)
    _intent_module = importlib.util.module_from_spec(_intent_spec)
    _intent_spec.loader.exec_module(_intent_module)
    get_intent_status = _intent_module.get_intent_status
    detect_amnesia = _intent_module.detect_amnesia  # RD-INTENT Phase 4
    INTENT_CHECKER_AVAILABLE = True
except Exception:
    INTENT_CHECKER_AVAILABLE = False
    detect_amnesia = None

# Import workflow_checker module (RD-WORKFLOW)
try:
    _workflow_checker_path = Path(__file__).parent / "checkers" / "workflow_checker.py"
    _workflow_spec = importlib.util.spec_from_file_location("workflow_checker", _workflow_checker_path)
    _workflow_module = importlib.util.module_from_spec(_workflow_spec)
    _workflow_spec.loader.exec_module(_workflow_module)
    get_workflow_status = _workflow_module.get_workflow_status
    WORKFLOW_CHECKER_AVAILABLE = True
except Exception:
    WORKFLOW_CHECKER_AVAILABLE = False
    get_workflow_status = None

# Import rule_applicability checker module (RD-RULE-APPLICABILITY)
try:
    _applicability_checker_path = Path(__file__).parent / "checkers" / "rule_applicability.py"
    _applicability_spec = importlib.util.spec_from_file_location("rule_applicability", _applicability_checker_path)
    _applicability_module = importlib.util.module_from_spec(_applicability_spec)
    _applicability_spec.loader.exec_module(_applicability_module)
    get_rule_applicability_summary = _applicability_module.get_rule_applicability_summary
    APPLICABILITY_CHECKER_AVAILABLE = True
except Exception:
    APPLICABILITY_CHECKER_AVAILABLE = False
    get_rule_applicability_summary = None

# Add hooks parent to path for package-relative imports (GAP-REFACTOR-001)
_hooks_parent = Path(__file__).parent.parent
if str(_hooks_parent) not in sys.path:
    sys.path.insert(0, str(_hooks_parent))

# Import shared modules (GAP-CODE-001, GAP-REFACTOR-001: Use shared modules)
try:
    from hooks.core.base import HookConfig, HookResult, DEFAULT_CONFIG
    from hooks.checkers.services import ServiceChecker
    from hooks.checkers.zombies import check_zombie_processes as _check_zombies
    from hooks.checkers.entropy import EntropyChecker
    from hooks.checkers.amnesia import AmnesiaDetector
    from hooks.recovery.containers import ContainerRecovery
    SHARED_MODULES_AVAILABLE = True
    CONTAINER_RECOVERY_AVAILABLE = True
    ZOMBIE_CHECKER_AVAILABLE = True
    ENTROPY_CHECKER_AVAILABLE = True
    AMNESIA_DETECTOR_AVAILABLE = True
except Exception:
    SHARED_MODULES_AVAILABLE = False
    CONTAINER_RECOVERY_AVAILABLE = False
    ZOMBIE_CHECKER_AVAILABLE = False
    ENTROPY_CHECKER_AVAILABLE = False
    AMNESIA_DETECTOR_AVAILABLE = False
    ContainerRecovery = None
    EntropyChecker = None
    AmnesiaDetector = None
    DEFAULT_CONFIG = None
    _check_zombies = None

# Import healthcheck formatters (RULE-032: File size reduction)
try:
    from healthcheck_formatters import format_detailed, format_summary, format_cached
    FORMATTERS_AVAILABLE = True
except ImportError:
    FORMATTERS_AVAILABLE = False

# Configuration - Use shared config if available, else fallback to inline
if SHARED_MODULES_AVAILABLE and DEFAULT_CONFIG:
    _config = DEFAULT_CONFIG
    GLOBAL_TIMEOUT = _config.global_timeout
    SUBPROCESS_TIMEOUT = _config.subprocess_timeout
    SOCKET_TIMEOUT = _config.socket_timeout
    RETRY_CEILING_SECONDS = _config.retry_ceiling_seconds
    RECOVERY_COOLDOWN = _config.recovery_cooldown
    STALE_PROCESS_HOURS = _config.stale_process_hours
    STATE_FILE = _config.state_file
    CORE_SERVICES = _config.core_services
    EXPECTED_MCP_SERVERS = _config.expected_mcp_servers
else:
    # Fallback inline config (backward compatibility)
    GLOBAL_TIMEOUT = 15
    SUBPROCESS_TIMEOUT = 2
    SOCKET_TIMEOUT = 0.5
    RETRY_CEILING_SECONDS = 30
    RECOVERY_COOLDOWN = 60
    STALE_PROCESS_HOURS = 2
    STATE_FILE = Path(__file__).parent / ".healthcheck_state.json"
    CORE_SERVICES = ["podman", "typedb", "chromadb"]
    EXPECTED_MCP_SERVERS = [
        "governance.mcp_server_core",
        "governance.mcp_server_agents",
        "governance.mcp_server_sessions",
        "governance.mcp_server_tasks",
        "claude_mem.mcp_server",
    ]

# GAP-HEALTH-AGGRESSIVE-001: Health mode configuration
# Modes: quiet (minimal), normal (default), aggressive (surgery sessions)
HEALTH_MODE = os.environ.get("SARVAJA_HEALTH_MODE", "normal").lower()
HEALTH_MODE_THRESHOLDS = {
    "quiet": 0.70,      # Only alert on very high confidence
    "normal": 0.50,     # Default threshold
    "aggressive": 0.25  # Alert on any indicators
}
AMNESIA_THRESHOLD = HEALTH_MODE_THRESHOLDS.get(HEALTH_MODE, 0.50)

# GAP-HEALTH-AUTORECOVERY: Consent-based auto-recovery toggle
# Options: enabled (default), disabled, prompt
# - enabled: Auto-recover containers when down (current behavior)
# - disabled: Never auto-recover, show manual command only
# - prompt: Show recovery command as suggestion, don't execute
AUTO_RECOVERY_MODE = os.environ.get("SARVAJA_AUTO_RECOVERY", "enabled").lower()
AUTO_RECOVERY_ENABLED = AUTO_RECOVERY_MODE == "enabled"


def force_exit():
    """Force exit after timeout - Windows safety."""
    output_json("[TIMEOUT] Healthcheck force-exit after 8s")
    sys.stdout.flush()  # Critical: flush before os._exit
    os._exit(0)  # Hard exit, no cleanup


# Start watchdog timer immediately (Windows doesn't support SIGALRM)
watchdog = threading.Timer(GLOBAL_TIMEOUT, force_exit)
watchdog.daemon = True
watchdog.start()


def compute_frankel_hash(data: Dict[str, Any]) -> str:
    """Compute Frankel-style hash (first 8 chars of SHA256, uppercase)."""
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8].upper()


def compute_component_hash(status: str, port: int = 0) -> str:
    """Compute hash for individual component (4 chars for drill-down)."""
    data = f"{status}:{port}:{datetime.now().strftime('%Y%m%d%H')}"
    return hashlib.sha256(data.encode()).hexdigest()[:4].upper()


def load_previous_state() -> Dict[str, Any]:
    """Load previous healthcheck state from file."""
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_current_state(state: Dict[str, Any]) -> None:
    """Save current healthcheck state to file with historical tracking."""
    try:
        # Load existing state for history
        existing = load_previous_state()
        history = existing.get("history", [])

        # Add current snapshot to history (keep last 10)
        if state.get("master_hash") != existing.get("master_hash"):
            history.append({
                "timestamp": datetime.now().isoformat(),
                "hash": state.get("master_hash", ""),
                "components": state.get("components", {}),
                "component_hashes": state.get("component_hashes", {})
            })
            history = history[-10:]  # Keep last 10 entries

        state["history"] = history

        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass  # Non-critical


def check_claude_mem_module() -> Dict[str, Any]:
    """
    Check if claude_mem MCP module files exist (RULE-024, RULE-040).

    Prevents crash from ModuleNotFoundError before MCP server starts.
    Only checks file existence, not import (MCP dependencies not available here).

    Returns:
        Dict with: ok (bool), status (str), error (optional)
    """
    try:
        # Check for module files directly (import would fail due to missing mcp package)
        claude_mem_dir = PROJECT_ROOT / "claude_mem"
        init_file = claude_mem_dir / "__init__.py"
        server_file = claude_mem_dir / "mcp_server.py"

        if not claude_mem_dir.exists():
            return {
                "ok": False,
                "status": "DIR_NOT_FOUND",
                "error": "claude_mem directory not found",
                "hint": "Create claude_mem/__init__.py and mcp_server.py"
            }
        if not init_file.exists():
            return {
                "ok": False,
                "status": "INIT_MISSING",
                "error": "claude_mem/__init__.py not found",
                "hint": "Create claude_mem/__init__.py"
            }
        if not server_file.exists():
            return {
                "ok": False,
                "status": "SERVER_MISSING",
                "error": "claude_mem/mcp_server.py not found",
                "hint": "Create claude_mem/mcp_server.py"
            }

        # Files exist - module is available
        return {"ok": True, "status": "OK"}

    except Exception as e:
        return {
            "ok": False,
            "status": "CHECK_ERROR",
            "error": str(e)[:100]
        }


def check_services() -> Dict[str, Dict[str, Any]]:
    """Check all services. Delegates to ServiceChecker."""
    if SHARED_MODULES_AVAILABLE:
        try:
            services = ServiceChecker().check_all()
            # Add claude-mem MCP module check
            cm = check_claude_mem_module()
            services["claude-mem"] = {"status": cm["status"], "ok": cm["ok"],
                                      "error": cm.get("error"), "hint": cm.get("hint"), "optional": False}
            return services
        except Exception:
            pass
    # Minimal fallback - return empty services (will trigger recovery)
    return {"podman": {"status": "UNKNOWN", "ok": False}}


def check_zombie_processes(auto_cleanup: bool = True) -> Dict[str, Any]:
    """Check for zombie MCP processes. Delegates to zombies module when available."""
    if ZOMBIE_CHECKER_AVAILABLE and _check_zombies:
        return _check_zombies(
            auto_cleanup=auto_cleanup,
            subprocess_timeout=SUBPROCESS_TIMEOUT,
            stale_process_hours=STALE_PROCESS_HOURS,
            expected_servers=EXPECTED_MCP_SERVERS
        )
    # Minimal fallback - just return empty result
    return {"zombies": [], "duplicates": {}, "stale_count": 0, "memory_pct": 0,
            "action_required": False, "cleanup_command": "", "cleaned": 0}


# Container recovery - uses ContainerRecovery class (backward compat wrappers for tests)
_recovery_instance = None

def _get_recovery() -> Optional["ContainerRecovery"]:
    """Get cached ContainerRecovery instance."""
    global _recovery_instance
    if CONTAINER_RECOVERY_AVAILABLE and ContainerRecovery and _recovery_instance is None:
        _recovery_instance = ContainerRecovery()
    return _recovery_instance

def start_podman_socket() -> bool:
    """Start container runtime socket. Backward compat wrapper."""
    r = _get_recovery()
    return r.start_socket() if r else False

def start_containers() -> bool:
    """Start CORE containers. Backward compat wrapper."""
    r = _get_recovery()
    return r.start_containers(["typedb", "chromadb"]) if r else False

def reset_containers() -> bool:
    """Reset containers after reboot. Backward compat wrapper."""
    r = _get_recovery()
    return r.reset_containers() if r else False

def detect_stale_containers() -> bool:
    """Detect stale containers. Backward compat wrapper."""
    r = _get_recovery()
    return r.detect_stale_containers() if r else False

def attempt_recovery(services: Dict, prev_state: Dict) -> List[str]:
    """
    Attempt auto-recovery. Returns list of recovery actions taken.

    Handles multiple scenarios:
    - Runtime (podman/docker) not running -> start socket
    - Containers down -> start containers
    - Stale containers (post-reboot) -> reset and restart

    Delegates to ContainerRecovery.attempt_recovery() which:
    - Detects stale containers via detect_stale_containers()
    - Resets stale containers via reset_containers()
    - Logs to audit trail for transparency
    """
    if CONTAINER_RECOVERY_AVAILABLE and ContainerRecovery:
        try:
            result = ContainerRecovery().attempt_recovery(services, prev_state)
            return result.recovery_actions if result.recovery_actions else []
        except Exception:
            pass
    return []


def check_entropy_state() -> Dict[str, Any]:
    """
    Check session entropy indicators (EPIC-006).
    Delegates to EntropyChecker when available.

    Returns dict with: entropy level, tool count, session minutes
    """
    # Use EntropyChecker when available (RULE-032: Shared modules)
    if ENTROPY_CHECKER_AVAILABLE and EntropyChecker:
        try:
            checker = EntropyChecker()
            return checker.get_status()
        except Exception:
            pass  # Fall through to fallback

    # Fallback to minimal local implementation
    entropy_file = Path(__file__).parent / ".entropy_state.json"
    try:
        if not entropy_file.exists():
            return {"entropy": "NEW", "tool_count": 0, "minutes": 0}
        with open(entropy_file) as f:
            state = json.load(f)
        tool_count = state.get("tool_count", 0)
        level = "HIGH" if tool_count >= 100 else ("MEDIUM" if tool_count >= 50 else "LOW")
        return {"entropy": level, "tool_count": tool_count, "minutes": 0}
    except Exception:
        return {"entropy": "UNKNOWN", "tool_count": 0, "minutes": 0}


def check_amnesia_indicators(prev_state: Dict, current_services: Dict = None) -> Dict[str, Any]:
    """
    Check for AMNESIA indicators by analyzing state patterns.
    Delegates to AmnesiaDetector when available (RULE-032).

    Per GAP-HEALTH-AGGRESSIVE-001: Threshold adjustable via SARVAJA_HEALTH_MODE.

    Returns dict with: detected (bool), confidence (0-1), indicators (list)
    """
    # Use AmnesiaDetector when available (RULE-032: Shared modules)
    if AMNESIA_DETECTOR_AVAILABLE and AmnesiaDetector:
        try:
            detector = AmnesiaDetector()
            # Override threshold based on health mode
            detector.DETECTION_THRESHOLD = AMNESIA_THRESHOLD
            result = detector.check(prev_state, current_services)
            confidence = result.extra.get("confidence", 0)
            # GAP-HEALTH-AGGRESSIVE-001: Use configurable threshold
            return {
                "detected": confidence >= AMNESIA_THRESHOLD,
                "confidence": confidence,
                "indicators": result.extra.get("indicators", [])
            }
        except Exception:
            pass  # Fall through to fallback

    # Also try shared health module
    if SHARED_HEALTH_AVAILABLE:
        try:
            result = shared_amnesia_check(prev_state, current_services)
            # GAP-HEALTH-AGGRESSIVE-001: Use configurable threshold
            return {
                "detected": result.confidence >= AMNESIA_THRESHOLD,
                "confidence": result.confidence,
                "indicators": result.indicators
            }
        except Exception:
            pass

    # Minimal fallback
    indicators = []
    confidence = 0.0
    prev_hash = prev_state.get("master_hash", "")
    if not prev_hash:
        indicators.append("NO_PREVIOUS_STATE")
        confidence += 0.3
    # GAP-HEALTH-AGGRESSIVE-001: Use configurable threshold
    return {"detected": confidence >= AMNESIA_THRESHOLD, "confidence": min(1.0, confidence), "indicators": indicators}


def output_json(context: str) -> None:
    """Output valid JSON for Claude Code context injection."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }
    print(json.dumps(output))


def main():
    """Main healthcheck logic with non-blocking guarantees and auto-recovery."""
    try:
        # Load previous state
        prev_state = load_previous_state()
        prev_hash = prev_state.get("master_hash", "")
        unchanged_since = prev_state.get("unchanged_since") or 0

        # GAP-HEALTH-003 FIX: ALWAYS check current state to detect changes
        # The retry ceiling now only affects OUTPUT verbosity, not state checking
        retry_ceiling_reached = unchanged_since > 0 and (time.time() - unchanged_since) > RETRY_CEILING_SECONDS

        # Run service checks (ALWAYS - this fixes GAP-HEALTH-003)
        services = check_services()

        # Compute master hash
        state_for_hash = {name: data["status"] for name, data in services.items()}
        master_hash = compute_frankel_hash(state_for_hash)

        # GAP-HEALTH-004: Compute per-component hashes for drill-down
        component_hashes = {}
        for name, data in services.items():
            port = data.get("port", 0)
            component_hashes[name] = compute_component_hash(data["status"], port)

        # Determine if state changed
        hash_changed = master_hash != prev_hash
        check_count = prev_state.get("check_count", 0) + 1

        # Update unchanged_since tracking
        if hash_changed:
            new_unchanged_since = time.time()  # Reset timer on change
        else:
            new_unchanged_since = unchanged_since if unchanged_since and unchanged_since > 0 else time.time()

        # Attempt auto-recovery if CORE services are down (GAP-HEALTH-AUTORECOVERY)
        recovery_actions = []
        recovery_hint = None
        required_ok = all(services.get(s, {}).get("ok", False) for s in CORE_SERVICES)
        if not required_ok:
            if AUTO_RECOVERY_ENABLED:
                # Consent granted via settings - auto-recover
                recovery_actions = attempt_recovery(services, prev_state)
            else:
                # Consent not granted - provide manual command instead
                if CONTAINER_RECOVERY_AVAILABLE and ContainerRecovery:
                    recovery = ContainerRecovery()
                    recovery_hint = recovery.get_resolution_path(services)
                else:
                    recovery_hint = "podman compose --profile cpu up -d typedb chromadb"

        # Save current state (include recovery tracking and component hashes)
        current_state = {
            "master_hash": master_hash,
            "check_count": check_count,
            "last_check": datetime.now().isoformat(),
            "unchanged_since": new_unchanged_since,
            "components": state_for_hash,
            "component_hashes": component_hashes  # GAP-HEALTH-004: Per-component hashes
        }
        if recovery_actions:
            current_state["last_recovery"] = time.time()
            current_state["recovery_actions"] = recovery_actions
        save_current_state(current_state)

        # Check for AMNESIA indicators (pass services for recovery detection)
        amnesia = check_amnesia_indicators(prev_state, services)

        # Check session entropy (EPIC-006)
        entropy = check_entropy_state()

        # Check for zombie/duplicate processes (GAP-ZOMBIE-001)
        zombies = check_zombie_processes()

        # Check session intent continuity (RD-INTENT Phase 3)
        intent = None
        intent_amnesia = None
        if INTENT_CHECKER_AVAILABLE:
            try:
                intent = get_intent_status(PROJECT_ROOT / "evidence")
                # RD-INTENT Phase 4: AMNESIA detection
                if detect_amnesia:
                    intent_amnesia = detect_amnesia(PROJECT_ROOT / "evidence")
            except Exception:
                pass  # Non-critical, don't block healthcheck

        # Check workflow compliance (RD-WORKFLOW)
        workflow = None
        if WORKFLOW_CHECKER_AVAILABLE:
            try:
                workflow = get_workflow_status(PROJECT_ROOT)
            except Exception:
                pass  # Non-critical, don't block healthcheck

        # Check rule applicability (RD-RULE-APPLICABILITY Phase 3)
        applicability = None
        if APPLICABILITY_CHECKER_AVAILABLE:
            try:
                # Build context from current services and entropy state
                applicability_context = {
                    "services": services,
                    "entropy_high": entropy.get("entropy") in ("HIGH", "CRITICAL"),
                    "halt_requested": False,  # Could be set by user input
                }
                applicability = get_rule_applicability_summary(applicability_context)
            except Exception:
                pass  # Non-critical, don't block healthcheck

        # Format output based on state (retry ceiling affects verbosity only, not checking)
        # GAP-HEALTH-AGGRESSIVE-001: Always use detailed output in aggressive mode
        use_detailed = hash_changed or check_count == 1 or HEALTH_MODE == "aggressive"

        if use_detailed:
            context = format_detailed(
                services, master_hash, recovery_actions, amnesia, component_hashes,
                entropy, zombies, intent, intent_amnesia, workflow,
                core_services=CORE_SERVICES, stale_process_hours=STALE_PROCESS_HOURS,
                recovery_hint=recovery_hint, auto_recovery_enabled=AUTO_RECOVERY_ENABLED,
                applicability=applicability
            )
        elif retry_ceiling_reached:
            # Brief output when unchanged for >30s (but we still checked current state!)
            # GAP-AMNESIA-OUTPUT-001: Pass amnesia to show warnings in summary mode
            context = format_summary(services, master_hash, "(stable)", recovery_actions, zombies, amnesia,
                                    core_services=CORE_SERVICES, recovery_hint=recovery_hint,
                                    auto_recovery_enabled=AUTO_RECOVERY_ENABLED)
        else:
            unchanged_duration = time.time() - new_unchanged_since
            # GAP-AMNESIA-OUTPUT-001: Pass amnesia to show warnings in summary mode
            context = format_summary(services, master_hash, f"(unchanged {int(unchanged_duration)}s)", recovery_actions, zombies, amnesia,
                                    core_services=CORE_SERVICES, recovery_hint=recovery_hint,
                                    auto_recovery_enabled=AUTO_RECOVERY_ENABLED)

        output_json(context)

    except Exception as e:
        output_json(f"[ERROR] Healthcheck failed: {str(e)[:100]}")
    finally:
        # Cancel watchdog timer on successful completion
        watchdog.cancel()


if __name__ == "__main__":
    main()
    sys.exit(0)  # Always exit 0 - never block Claude Code
