#!/usr/bin/env python3
"""
TypeDB Data Export Script
=========================
Export all TypeDB data for migration warranty.

Per GAP-TYPEDB-UPGRADE-001: Warranty mechanism for Phase 3 migration.
Per SAFETY-DESTR-01-v1: Data backup before destructive operations.

Creates:
- data/exports/typedb_export_YYYYMMDD_HHMMSS.json (full export)
- data/exports/typedb_export_YYYYMMDD_HHMMSS_2x.tql (2.x compatible)
- data/exports/typedb_export_YYYYMMDD_HHMMSS_3x.tql (3.x compatible)

Usage:
    python scripts/typedb_export.py              # Dry run
    python scripts/typedb_export.py --execute   # Export to files
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
API_URL = os.getenv("GOVERNANCE_API_URL", "http://localhost:8082")
EXPORTS_DIR = Path(__file__).parent.parent / "data" / "exports"


def fetch_json(endpoint: str) -> Optional[List[Dict]]:
    """Fetch JSON from API endpoint. Handles paginated responses."""
    try:
        url = f"{API_URL}{endpoint}"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            # Handle paginated responses
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            return data
    except urllib.error.HTTPError as e:
        print(f"  [WARN] {endpoint}: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  [ERROR] {endpoint}: {e}")
        return None


def fetch_all_paginated(endpoint: str, entity_name: str) -> List[Dict]:
    """Fetch all items from paginated endpoint."""
    all_items = []
    offset = 0
    limit = 100

    while True:
        url = f"{endpoint}?limit={limit}&offset={offset}"
        items = fetch_json(url)
        if not items:
            break
        all_items.extend(items)
        print(f"  Fetched: {len(all_items)} {entity_name}...")
        if len(items) < limit:
            break
        offset += limit

    return all_items


def export_rules() -> List[Dict]:
    """Export all rules from TypeDB."""
    print("[1/5] Exporting rules...")
    rules = fetch_json("/api/rules") or []
    print(f"  Found: {len(rules)} rules")
    return rules


def export_tasks() -> List[Dict]:
    """Export all tasks from TypeDB."""
    print("[2/5] Exporting tasks...")
    tasks = fetch_json("/api/tasks") or []
    print(f"  Found: {len(tasks)} tasks")
    return tasks


def export_sessions() -> List[Dict]:
    """Export all sessions from TypeDB."""
    print("[3/5] Exporting sessions...")
    sessions = fetch_json("/api/sessions") or []
    print(f"  Found: {len(sessions)} sessions")
    return sessions


def export_agents() -> List[Dict]:
    """Export all agents from TypeDB."""
    print("[4/5] Exporting agents...")
    agents = fetch_json("/api/agents") or []
    print(f"  Found: {len(agents)} agents")
    return agents


def export_decisions() -> List[Dict]:
    """Export all decisions from TypeDB."""
    print("[5/5] Exporting decisions...")
    decisions = fetch_json("/api/decisions") or []
    print(f"  Found: {len(decisions)} decisions")
    return decisions


def escape_typeql(value: str) -> str:
    """Escape string for TypeQL."""
    if value is None:
        return ""
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def generate_2x_tql(data: Dict) -> str:
    """Generate TypeDB 2.x compatible TypeQL insert statements."""
    lines = [
        "# TypeDB 2.x Data Export",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Rules: {len(data['rules'])}, Tasks: {len(data['tasks'])}, Sessions: {len(data['sessions'])}",
        "",
        "insert",
        ""
    ]
    
    # Rules
    lines.append("# === RULES ===")
    for i, rule in enumerate(data['rules']):
        var = f"$rule{i:03d}"
        lines.append(f"{var} isa rule-entity,")
        lines.append(f'    has rule-id "{escape_typeql(rule.get("rule_id", ""))}",')
        lines.append(f'    has rule-name "{escape_typeql(rule.get("name", ""))}",')
        lines.append(f'    has category "{escape_typeql(rule.get("category", "governance"))}",')
        lines.append(f'    has priority "{escape_typeql(rule.get("priority", "MEDIUM"))}",')
        lines.append(f'    has status "{escape_typeql(rule.get("status", "ACTIVE"))}",')
        directive = escape_typeql(rule.get("directive", ""))
        lines.append(f'    has directive "{directive}";')
        lines.append("")
    
    # Tasks
    lines.append("# === TASKS ===")
    for i, task in enumerate(data['tasks']):
        var = f"$task{i:03d}"
        lines.append(f"{var} isa task,")
        lines.append(f'    has task-id "{escape_typeql(task.get("task_id", ""))}",')
        lines.append(f'    has task-description "{escape_typeql(task.get("description", ""))}",')
        lines.append(f'    has task-status "{escape_typeql(task.get("status", "TODO"))}",')
        if task.get("phase"):
            lines.append(f'    has task-phase "{escape_typeql(task.get("phase"))}",')
        if task.get("resolution"):
            lines.append(f'    has task-resolution "{escape_typeql(task.get("resolution"))}",')
        if task.get("agent_id"):
            lines.append(f'    has agent-id "{escape_typeql(task.get("agent_id"))}",')
        lines[-1] = lines[-1].rstrip(",") + ";"
        lines.append("")
    
    # Sessions
    lines.append("# === SESSIONS ===")
    for i, session in enumerate(data['sessions']):
        var = f"$session{i:03d}"
        lines.append(f"{var} isa session,")
        lines.append(f'    has session-id "{escape_typeql(session.get("session_id", ""))}",')
        if session.get("topic"):
            lines.append(f'    has session-topic "{escape_typeql(session.get("topic"))}",')
        if session.get("status"):
            lines.append(f'    has session-status "{escape_typeql(session.get("status"))}",')
        lines[-1] = lines[-1].rstrip(",") + ";"
        lines.append("")
    
    # Agents
    lines.append("# === AGENTS ===")
    for i, agent in enumerate(data['agents']):
        var = f"$agent{i:03d}"
        lines.append(f"{var} isa agent,")
        lines.append(f'    has agent-id "{escape_typeql(agent.get("agent_id", ""))}",')
        lines.append(f'    has agent-name "{escape_typeql(agent.get("name", ""))}",')
        lines.append(f'    has agent-type "{escape_typeql(agent.get("agent_type", "claude-code"))}",')
        if agent.get("trust_score") is not None:
            lines.append(f'    has trust-score {agent.get("trust_score", 0.85)};')
        else:
            lines[-1] = lines[-1].rstrip(",") + ";"
        lines.append("")
    
    # Decisions
    lines.append("# === DECISIONS ===")
    for i, decision in enumerate(data['decisions']):
        var = f"$decision{i:03d}"
        lines.append(f"{var} isa decision,")
        lines.append(f'    has decision-id "{escape_typeql(decision.get("decision_id", ""))}",')
        lines.append(f'    has decision-title "{escape_typeql(decision.get("title", ""))}",')
        if decision.get("rationale"):
            lines.append(f'    has decision-rationale "{escape_typeql(decision.get("rationale"))}",')
        lines[-1] = lines[-1].rstrip(",") + ";"
        lines.append("")
    
    return "\n".join(lines)


def generate_3x_tql(data: Dict) -> str:
    """Generate TypeDB 3.x compatible TypeQL insert statements."""
    # Note: TypeDB 3.x insert syntax is same as 2.x for data
    # The schema syntax changed, but insert statements are compatible
    lines = [
        "# TypeDB 3.x Data Export",
        f"# Generated: {datetime.now().isoformat()}",
        f"# Rules: {len(data['rules'])}, Tasks: {len(data['tasks'])}, Sessions: {len(data['sessions'])}",
        "# Note: Insert syntax is compatible between 2.x and 3.x",
        "",
        "insert",
        ""
    ]
    
    # Reuse 2.x generation (insert syntax is the same)
    content_2x = generate_2x_tql(data)
    # Skip header lines and use rest
    lines_2x = content_2x.split("\n")[6:]  # Skip first 6 header lines
    return "\n".join(lines) + "\n".join(lines_2x)


def create_export(dry_run: bool = True) -> Dict:
    """Create full TypeDB export."""
    print("=" * 60)
    print("TypeDB Data Export Tool")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print("-" * 60)
    
    # Export all entities
    data = {
        "timestamp": datetime.now().isoformat(),
        "api_url": API_URL,
        "rules": export_rules(),
        "tasks": export_tasks(),
        "sessions": export_sessions(),
        "agents": export_agents(),
        "decisions": export_decisions(),
    }
    
    # Summary
    print("-" * 60)
    print("EXPORT SUMMARY:")
    print(f"  Rules:     {len(data['rules'])}")
    print(f"  Tasks:     {len(data['tasks'])}")
    print(f"  Sessions:  {len(data['sessions'])}")
    print(f"  Agents:    {len(data['agents'])}")
    print(f"  Decisions: {len(data['decisions'])}")
    total = sum(len(data[k]) for k in ['rules', 'tasks', 'sessions', 'agents', 'decisions'])
    print(f"  TOTAL:     {total} entities")
    
    if not dry_run:
        # Create export directory
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON export
        json_file = EXPORTS_DIR / f"typedb_export_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"\n[SAVED] JSON: {json_file}")
        
        # Save 2.x TypeQL
        tql_2x_file = EXPORTS_DIR / f"typedb_export_{timestamp}_2x.tql"
        with open(tql_2x_file, "w", encoding="utf-8") as f:
            f.write(generate_2x_tql(data))
        print(f"[SAVED] 2.x TQL: {tql_2x_file}")
        
        # Save 3.x TypeQL
        tql_3x_file = EXPORTS_DIR / f"typedb_export_{timestamp}_3x.tql"
        with open(tql_3x_file, "w", encoding="utf-8") as f:
            f.write(generate_3x_tql(data))
        print(f"[SAVED] 3.x TQL: {tql_3x_file}")
        
        data["files"] = {
            "json": str(json_file),
            "tql_2x": str(tql_2x_file),
            "tql_3x": str(tql_3x_file),
        }
        
        # Verification hash
        import hashlib
        content_hash = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]
        print(f"\n[VERIFY] Content hash: {content_hash}")
        data["content_hash"] = content_hash
    else:
        print("\n[!] Run with --execute to save export files")
    
    return data


if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    export_data = create_export(dry_run=dry_run)
    
    if dry_run:
        print("\n" + "=" * 60)
        print("WARRANTY VERIFICATION CHECKLIST:")
        print("=" * 60)
        print("[ ] Export script tested (dry run complete)")
        print("[ ] Run with --execute to create backup files")
        print("[ ] Verify JSON contains all expected entities")
        print("[ ] Verify TypeQL can be loaded (test on separate instance)")
        print("[ ] Only then proceed with TypeDB 3.x upgrade")
