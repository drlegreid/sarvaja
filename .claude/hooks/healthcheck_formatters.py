"""
Healthcheck output formatters for Claude Code hooks.

Extracted from healthcheck.py to reduce file size per RULE-032.
Platform: Linux (xubuntu) with Podman - migrated 2026-01-09
"""

from typing import Any, Dict, List, Optional


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
    stale_process_hours: int = 2
) -> str:
    """Format detailed output with component chain, hashes, AMNESIA detection, entropy, etc."""
    core_services = core_services or ["podman", "typedb", "chromadb"]
    lines = [f"=== MCP DEPENDENCY CHAIN [Hash: {master_hash}] ===", ""]

    required_ok = all(services.get(s, {}).get("ok", False) for s in core_services)

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

    # AMNESIA Detection
    if amnesia and amnesia.get("detected"):
        lines.append("")
        lines.append(f"⚠️ AMNESIA RISK: {int(amnesia['confidence']*100)}% confidence")
        lines.append(f"  Indicators: {', '.join(amnesia['indicators'])}")
        lines.append("  Recovery Protocol (RULE-024):")
        lines.append("    1. Read CLAUDE.md → Document map")
        lines.append("    2. Read docs/DEVOPS.md → Infrastructure (CRITICAL)")
        lines.append("    3. Read .mcp.json → MCP servers")
        lines.append("    4. Query claude-mem → mcp__claude-mem__chroma_query_documents(['sim-ai 2026-01'])")

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

    # Recovery actions or manual hint
    if recovery_actions:
        lines.append("")
        lines.append("Auto-Recovery:")
        for action in recovery_actions:
            lines.append(f"  → {action}")
        lines.append("  (Run /health again in 30-60s to verify)")
    elif not required_ok:
        lines.append("")
        lines.append("Manual Recovery: podman compose --profile cpu up -d")

    return "\n".join(lines)


def format_summary(
    services: Dict,
    master_hash: str,
    reason: str = "",
    recovery_actions: List[str] = None,
    zombies: Dict = None,
    core_services: List[str] = None
) -> str:
    """Format summary output (for unchanged state or retry ceiling)."""
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

    if required_ok:
        return f"[HEALTH OK] Hash: {master_hash} {reason}. MCP chain ready.{zombie_suffix}"
    else:
        failed = [s for s in core_services if not services.get(s, {}).get("ok", False)]
        if recovery_actions:
            recovery_str = " | " + "; ".join(recovery_actions)
            return f"[HEALTH RECOVERING] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{recovery_str}{zombie_suffix}"
        else:
            hint = " | Recovery: podman compose --profile cpu up -d" if failed else ""
            return f"[HEALTH WARN] Hash: {master_hash} {reason}. Down: {', '.join(failed)}{hint}{zombie_suffix}"


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
