"""
Healthcheck output formatters for Claude Code hooks.

Extracted from healthcheck.py to reduce file size per RULE-032.
Platform: Linux (xubuntu) with Podman - migrated 2026-01-09

Per SESSION-DSP-NOTIFY-01-v1: DSP notifications must be prominent.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# DSP Detection per SESSION-DSP-NOTIFY-01-v1
DSP_EVIDENCE_THRESHOLD = 20  # Evidence files threshold
DSP_AGE_THRESHOLD_DAYS = 7   # Days since last DSP


def check_dsp_conditions(project_root: Path = None) -> Dict[str, Any]:
    """
    Check for DSP suggestion conditions per SESSION-DSP-NOTIFY-01-v1.

    Returns:
        Dict with: suggested (bool), alerts (list), override_needed (bool)
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent

    alerts = []

    # Check evidence file count
    evidence_dir = project_root / "evidence"
    try:
        evidence_count = len(list(evidence_dir.glob("SESSION-*.md"))) if evidence_dir.exists() else 0
        if evidence_count > DSP_EVIDENCE_THRESHOLD:
            alerts.append(f"Evidence accumulation: {evidence_count} session files")
    except Exception:
        evidence_count = 0

    # Check last DSP cycle age
    try:
        dsp_files = sorted(evidence_dir.glob("*DSP*.md"), reverse=True)
        if dsp_files:
            # Extract date from filename (SESSION-YYYY-MM-DD-DSP*.md)
            latest_dsp = dsp_files[0].name
            date_parts = latest_dsp.split("-")[1:4]  # YYYY, MM, DD
            if len(date_parts) == 3:
                dsp_date = datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                days_since = (datetime.now() - dsp_date).days
                if days_since > DSP_AGE_THRESHOLD_DAYS:
                    alerts.append(f"No DSP cycle in {days_since} days (threshold: {DSP_AGE_THRESHOLD_DAYS})")
        else:
            alerts.append("No DSP cycle found in evidence")
    except Exception:
        pass

    return {
        "suggested": len(alerts) >= 2,  # Trigger on 2+ conditions
        "alerts": alerts,
        "override_needed": len(alerts) >= 2
    }


def format_detailed(
    services: Dict,
    master_hash: str,
    recovery_actions: List[str] = None,
    amnesia: Dict = None,
    component_hashes: Dict = None,
    entropy: Dict = None,
    zombies: Dict = None,
    intent: Dict = None,
    intent_amnesia: Dict = None,
    workflow: Dict = None,
    core_services: List[str] = None,
    stale_process_hours: int = 2,
    dsp_info: Dict = None,
    recovery_hint: str = None,
    auto_recovery_enabled: bool = True,
    applicability: Dict = None,
    mcp_usage: Dict = None,
) -> str:
    """Format detailed output with component chain, hashes, AMNESIA detection, entropy, etc."""
    core_services = core_services or ["podman", "typedb", "chromadb"]
    lines = [f"=== MCP DEPENDENCY CHAIN [Hash: {master_hash}] ===", ""]

    required_ok = all(services.get(s, {}).get("ok", False) for s in core_services)

    # DSP Notification (FIRST - most prominent per SESSION-DSP-NOTIFY-01-v1)
    if dsp_info is None:
        dsp_info = check_dsp_conditions()
    if dsp_info.get("suggested"):
        lines.append("╔═══════════════════════════════════════════════════════════╗")
        lines.append("║  🔴 DSP REQUIRED - Document entropy high                  ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        for alert in dsp_info.get("alerts", []):
            lines.append(f"║  • {alert:<55} ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║  Options:                                                 ║")
        lines.append("║    1. Run /deep-sleep to initiate DSP cycle               ║")
        lines.append("║    2. Type OVERRIDE to continue without DSP               ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")
        lines.append("")

    # Check for services in starting state
    starting_services = [s for s in core_services if services.get(s, {}).get("is_starting", False)]
    if starting_services:
        lines.append("⏳ SERVICES STARTING - Please wait...")
        lines.append(f"   Starting: {', '.join(starting_services)}")
        lines.append("   Action: Retry /health in 15-30 seconds")
        lines.append("")

    # Per-component hashes for drill-down
    lines.append("Required Services (CORE MCPs):")
    for name in core_services:
        data = services.get(name, {})
        status = data.get("status", "UNKNOWN")
        port = data.get("port", "")
        port_str = f" (:{port})" if port else ""
        icon = "✓" if data.get("ok") else "✗"
        comp_hash = component_hashes.get(name, "????") if component_hashes else "????"
        lines.append(f"  {icon} {name.upper()}{port_str}: {status} [{comp_hash}]")

    # Claude-mem MCP (RULE-024: AMNESIA recovery)
    lines.append("")
    lines.append("MCP Modules:")
    claude_mem = services.get("claude-mem", {})
    claude_mem_ok = claude_mem.get("ok", False)
    claude_mem_icon = "✓" if claude_mem_ok else "✗"
    claude_mem_hash = component_hashes.get("claude-mem", "????") if component_hashes else "????"
    lines.append(f"  {claude_mem_icon} CLAUDE-MEM: {claude_mem.get('status', 'UNKNOWN')} [{claude_mem_hash}]")
    if not claude_mem_ok and claude_mem.get("error"):
        lines.append(f"    ⚠️ {claude_mem.get('error')}")
        if claude_mem.get("hint"):
            lines.append(f"    Hint: {claude_mem.get('hint')}")

    lines.append("")
    lines.append("Optional Services:")
    for name in ["litellm", "ollama"]:
        data = services.get(name, {})
        status = data.get("status", "UNKNOWN")
        port = data.get("port", "")
        port_str = f" (:{port})" if port else ""
        icon = "✓" if data.get("ok") else "○"
        comp_hash = component_hashes.get(name, "????") if component_hashes else "????"
        lines.append(f"  {icon} {name.upper()}{port_str}: {status} [{comp_hash}]")

    # Session Entropy (EPIC-006)
    if entropy:
        lines.append("")
        lines.append("Session Entropy:")
        tool_count = entropy.get("tool_count", 0)
        minutes = entropy.get("minutes", 0)
        level = entropy.get("entropy", "UNKNOWN")
        last_save = entropy.get("last_save")

        if level == "HIGH":
            lines.append(f"  ⚠️ Tools: {tool_count} | Duration: {minutes}m | Level: {level}")
            lines.append("  Action: Run /save before complex tasks")
        elif level == "MEDIUM":
            lines.append(f"  Tools: {tool_count} | Duration: {minutes}m | Level: {level}")
            lines.append("  Consider: /save at next milestone")
        else:
            lines.append(f"  Tools: {tool_count} | Duration: {minutes}m | Level: {level}")

        if last_save:
            lines.append(f"  Last save: {last_save[:19]}")

    # MCP Usage (GOV-MCP-FIRST-01-v1)
    if mcp_usage:
        cats = mcp_usage.get("mcp_categories", {})
        tw = mcp_usage.get("todowrite_count", 0)
        parts = [f"{k}={v}" for k, v in sorted(cats.items())]
        parts.append(f"TodoWrite={tw}")
        lines.append("")
        lines.append(f"MCP Usage: {' | '.join(parts)}")
        warns = mcp_usage.get("warnings_issued", 0)
        if warns > 0:
            lines.append(f"  ⚠️ {warns} MCP-first warning(s) issued this session")

    # AMNESIA Detection
    if amnesia and amnesia.get("detected"):
        lines.append("")
        lines.append(f"⚠️ AMNESIA RISK: {int(amnesia['confidence']*100)}% confidence")
        lines.append(f"  Indicators: {', '.join(amnesia['indicators'])}")
        lines.append("  Recovery Protocol (RULE-024):")
        lines.append("    1. Read CLAUDE.md → Document map")
        lines.append("    2. Read docs/DEVOPS.md → Infrastructure (CRITICAL)")
        lines.append("    3. Read .mcp.json → MCP servers")
        lines.append("    4. Query claude-mem → mcp__claude-mem__chroma_query_documents(['sarvaja 2026-01'])")

    # Zombie Process Detection
    if zombies:
        cleaned = zombies.get("cleaned", 0)
        if cleaned > 0:
            lines.append("")
            lines.append(f"✓ AUTO-CLEANUP: Killed {cleaned} duplicate MCP processes")

        if zombies.get("action_required"):
            lines.append("")
            lines.append("⚠️ ISSUES REMAINING:")
            if zombies.get("stale_count", 0) > 10:
                lines.append(f"  • Stale python processes: {zombies['stale_count']} (>{stale_process_hours}h old)")
            if zombies.get("memory_pct", 0) > 85:
                lines.append(f"  • Memory pressure: {zombies['memory_pct']}% used")
            lines.append("  Action: Restart VS Code or run cleanup command")
        else:
            mem_pct = zombies.get("memory_pct", 0)
            if mem_pct > 70:
                lines.append("")
                lines.append(f"Memory: {mem_pct}% used")

    # Session Continuity (RD-INTENT Phase 3)
    if intent and intent.get("has_continuity"):
        lines.extend(intent.get("lines", []))

    # RD-INTENT Phase 4: AMNESIA Detection Alerts
    if intent_amnesia and intent_amnesia.get("detected"):
        lines.extend(intent_amnesia.get("alert_lines", []))

    # RD-WORKFLOW: Workflow Compliance
    if workflow:
        lines.extend(workflow.get("lines", []))

    # RD-RULE-APPLICABILITY: Rule Enforcement Status
    if applicability:
        lines.extend(applicability.get("lines", []))
        # If blocked, add prominent warning
        if applicability.get("blocked"):
            lines.append("")
            lines.append("╔═══════════════════════════════════════════════════════════╗")
            lines.append("║  ⛔ FORBIDDEN ACTION BLOCKED                              ║")
            lines.append("╚═══════════════════════════════════════════════════════════╝")

    # Recovery actions or manual hint (GAP-HEALTH-AUTORECOVERY)
    if recovery_actions:
        lines.append("")
        lines.append("Auto-Recovery:")
        for action in recovery_actions:
            lines.append(f"  → {action}")
        lines.append("  (Run /health again in 30-60s to verify)")
    elif not required_ok:
        lines.append("")
        if not auto_recovery_enabled:
            lines.append("⚠️ Auto-Recovery DISABLED (SARVAJA_AUTO_RECOVERY=disabled)")
            lines.append("  Enable: export SARVAJA_AUTO_RECOVERY=enabled")
        if recovery_hint:
            lines.append(f"Manual Recovery: {recovery_hint}")
        else:
            lines.append("Manual Recovery: podman compose --profile cpu up -d")

    return "\n".join(lines)


def format_summary(
    services: Dict,
    master_hash: str,
    reason: str = "",
    recovery_actions: List[str] = None,
    zombies: Dict = None,
    amnesia: Dict = None,
    core_services: List[str] = None,
    dsp_info: Dict = None,
    recovery_hint: str = None,
    auto_recovery_enabled: bool = True
) -> str:
    """Format summary output (for unchanged state or retry ceiling).

    Per GAP-AMNESIA-OUTPUT-001: Now includes AMNESIA warnings in summary mode.
    Per SESSION-DSP-NOTIFY-01-v1: Now includes DSP warnings in summary mode.
    """
    core_services = core_services or ["podman", "typedb", "chromadb"]
    required_ok = all(services.get(s, {}).get("ok", False) for s in core_services)

    # Add zombie info suffix
    zombie_suffix = ""
    if zombies:
        zombie_parts = []
        if zombies.get("cleaned", 0) > 0:
            zombie_parts.append(f"✓ cleaned {zombies['cleaned']} zombies")
        if zombies.get("stale_count", 0) > 10:
            zombie_parts.append(f"{zombies['stale_count']} stale procs")
        if zombies.get("memory_pct", 0) > 85:
            zombie_parts.append(f"mem {zombies['memory_pct']}%")
        if zombie_parts:
            zombie_suffix = f" | {', '.join(zombie_parts)}"

    # GAP-AMNESIA-OUTPUT-001: Add AMNESIA warning to summary output
    amnesia_suffix = ""
    if amnesia and amnesia.get("detected"):
        confidence = int(amnesia.get("confidence", 0) * 100)
        amnesia_suffix = f" | AMNESIA RISK {confidence}%"

    # SESSION-DSP-NOTIFY-01-v1: Add DSP warning to summary output
    dsp_suffix = ""
    if dsp_info is None:
        dsp_info = check_dsp_conditions()
    if dsp_info.get("suggested"):
        dsp_suffix = " | 🔴 DSP REQUIRED - run /deep-sleep or OVERRIDE"

    if required_ok:
        return f"[HEALTH OK] Hash: {master_hash} {reason}. MCP chain ready.{zombie_suffix}{amnesia_suffix}{dsp_suffix}"
    else:
        failed = [s for s in core_services if not services.get(s, {}).get("ok", False)]
        if recovery_actions:
            recovery_str = " | " + "; ".join(recovery_actions)
            return f"[HEALTH RECOVERING] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{recovery_str}{zombie_suffix}{amnesia_suffix}{dsp_suffix}"
        else:
            # GAP-HEALTH-AUTORECOVERY: Use specific hint or default
            if recovery_hint:
                hint = f" | Recovery: {recovery_hint}"
            elif failed:
                hint = " | Recovery: podman compose --profile cpu up -d"
            else:
                hint = ""
            auto_status = "" if auto_recovery_enabled else " [AUTO-RECOVERY DISABLED]"
            return f"[HEALTH WARN] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{auto_status}{hint}{zombie_suffix}{amnesia_suffix}{dsp_suffix}"


def format_cached(prev_state: Dict, core_services: List[str] = None) -> str:
    """Format cached response when retry ceiling reached."""
    core_services = core_services or ["podman", "typedb", "chromadb"]
    master_hash = prev_state.get("master_hash", "????????")
    components = prev_state.get("components", {})

    failed = [s for s, status in components.items() if status not in ("OK", "OFF") and s in core_services]

    if failed:
        return f"[CACHED] Hash: {master_hash} (retry ceiling reached). Down: {', '.join(failed)} | Recovery: podman compose --profile cpu up -d"
    else:
        return f"[CACHED] Hash: {master_hash} (retry ceiling reached). MCP chain ready."
