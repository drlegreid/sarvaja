#!/usr/bin/env python3
"""
Data Linkage Enrichment Script
==============================
Fixes GAP-LINK-001, GAP-LINK-002, GAP-LINK-003 by enriching entity linkages.

Per RULE-020: LLM-Driven E2E Test Generation (exploratory → fix)
Per GAP-DATA-002: Cross-entity relationships

Created: 2026-01-12
Updated: 2026-01-12 - Uses REST API linking endpoints (TypeDB-backed)
"""

import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

API_BASE = "http://localhost:8082"


def api_get(endpoint: str) -> Optional[List[Dict]]:
    """GET from API."""
    try:
        url = f"{API_BASE}{endpoint}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  [ERROR] GET {endpoint}: {e}")
        return None


def api_post(endpoint: str, data: Dict = None) -> bool:
    """POST to API."""
    try:
        url = f"{API_BASE}{endpoint}"
        body = json.dumps(data).encode('utf-8') if data else b""
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 204)
    except urllib.error.HTTPError as e:
        # Skip 400/409 for already-linked cases
        if e.code in (400, 409):
            return False
        print(f"  [ERROR] POST {endpoint}: {e.code}")
        return False
    except Exception as e:
        print(f"  [ERROR] POST {endpoint}: {e}")
        return False


def extract_rule_references(text: str) -> List[str]:
    """Extract RULE-XXX references from text."""
    if not text:
        return []
    # Match RULE-001, RULE-023, etc.
    pattern = r'RULE-(\d{3})'
    matches = re.findall(pattern, text, re.IGNORECASE)
    return [f"RULE-{m}" for m in matches]


# Keyword → Rule mapping for intelligent rule assignment
KEYWORD_RULES = {
    # Testing keywords → RULE-023 (Test Before Ship)
    "test": ["RULE-023"],
    "tdd": ["RULE-023", "RULE-004"],
    "e2e": ["RULE-020", "RULE-023"],
    "spec": ["RULE-023"],
    "validation": ["RULE-028"],

    # Architecture keywords → RULE-032 (File Size), RULE-002 (Best Practices)
    "refactor": ["RULE-032", "RULE-002"],
    "modular": ["RULE-032"],
    "split": ["RULE-032"],
    "migration": ["RULE-009"],

    # Governance keywords → RULE-011 (Multi-Agent Governance)
    "governance": ["RULE-011"],
    "agent": ["RULE-011"],
    "trust": ["RULE-011"],
    "proposal": ["RULE-011"],

    # Documentation keywords → RULE-001 (Evidence), RULE-034 (Linking)
    "evidence": ["RULE-001"],
    "document": ["RULE-034"],
    "session": ["RULE-001"],

    # DSP keywords → RULE-012 (Deep Sleep Protocol)
    "dsp": ["RULE-012"],
    "audit": ["RULE-012"],
    "optimize": ["RULE-012"],

    # MCP keywords → RULE-007 (MCP Usage), RULE-021 (Healthcheck)
    "mcp": ["RULE-007"],
    "healthcheck": ["RULE-021"],
    "health": ["RULE-021"],

    # UI keywords → RULE-019 (UI/UX)
    "ui": ["RULE-019"],
    "ux": ["RULE-019"],
    "dashboard": ["RULE-019"],
    "view": ["RULE-019"],

    # DevOps keywords → RULE-030 (Docker), RULE-016 (Infrastructure)
    "docker": ["RULE-030"],
    "podman": ["RULE-030"],
    "container": ["RULE-030"],
    "infrastructure": ["RULE-016"],
}


def infer_rules_from_content(text: str) -> List[str]:
    """Infer relevant rules from task content using keywords."""
    if not text:
        return []

    text_lower = text.lower()
    inferred = set()

    for keyword, rules in KEYWORD_RULES.items():
        if keyword in text_lower:
            inferred.update(rules)

    return list(inferred)[:3]  # Max 3 rules per task


def enrich_task_rules(tasks: List[Dict], valid_rule_ids: Set[str]) -> int:
    """
    Enrich tasks with linked_rules based on description text and keyword inference.
    Uses REST API with TypeDB-backed linking.

    Returns: count of tasks updated
    """
    print("\n" + "=" * 60)
    print("PHASE 1: ENRICHING TASK → RULE LINKAGE")
    print("=" * 60)

    updated = 0
    link_count = 0

    for task in tasks:
        task_id = task.get("task_id")
        description = task.get("description") or ""
        body = task.get("body") or ""
        current_rules = task.get("linked_rules") or []

        # Skip if already has rules
        if current_rules:
            continue

        # Combine text for analysis
        text = f"{description} {body}"

        # Try explicit references first
        found_rules = extract_rule_references(text)

        # If no explicit references, infer from keywords
        if not found_rules:
            found_rules = infer_rules_from_content(text)

        # Validate against known rules
        valid_found = [r for r in found_rules if r in valid_rule_ids]

        if valid_found:
            # Link task to each rule via REST API
            task_linked = False
            for rule_id in valid_found:
                if api_post(f"/api/tasks/{task_id}/rules/{rule_id}"):
                    link_count += 1
                    task_linked = True

            if task_linked:
                updated += 1
                print(f"  [OK] {task_id}: linked to {valid_found}")

    print(f"\n  Updated {updated} tasks with {link_count} rule linkages")
    return updated


def enrich_session_evidence(sessions: List[Dict], evidence_dir: Path) -> int:
    """
    Enrich sessions with evidence_files based on filename patterns.

    Returns: count of sessions updated
    """
    print("\n" + "=" * 60)
    print("PHASE 2: ENRICHING SESSION → EVIDENCE LINKAGE")
    print("=" * 60)

    # Find all evidence files
    evidence_files = list(evidence_dir.glob("*.md"))
    print(f"  Found {len(evidence_files)} evidence files")

    # Build date → files mapping
    date_files: Dict[str, List[str]] = {}
    for ef in evidence_files:
        # Extract date from filename: SESSION-2024-12-24-*.md, DSM-2026-01-01-*.md
        match = re.search(r'(\d{4}-\d{2}-\d{2})', ef.name)
        if match:
            date = match.group(1)
            if date not in date_files:
                date_files[date] = []
            date_files[date].append(f"evidence/{ef.name}")

    updated = 0

    for session in sessions:
        session_id = session.get("session_id")
        start_time = session.get("start_time") or ""
        current_evidence = session.get("evidence_files") or []

        # Skip if already has evidence
        if current_evidence:
            continue

        # Extract date from session start_time
        match = re.search(r'(\d{4}-\d{2}-\d{2})', start_time)
        if not match:
            continue

        session_date = match.group(1)

        # Find matching evidence files
        matching_files = date_files.get(session_date, [])

        if matching_files:
            # Link evidence via API
            for ef_path in matching_files[:3]:  # Limit to 3 per session
                try:
                    url = f"{API_BASE}/api/sessions/{session_id}/evidence"
                    body = json.dumps({"evidence_source": ef_path}).encode('utf-8')
                    req = urllib.request.Request(
                        url,
                        data=body,
                        headers={"Content-Type": "application/json"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        if resp.status in (200, 201):
                            updated += 1
                            print(f"  [OK] {session_id}: linked to {ef_path}")
                except Exception as e:
                    print(f"  [FAIL] {session_id}: {e}")

    print(f"\n  Linked {updated} evidence files to sessions")
    return updated


def enrich_task_sessions(tasks: List[Dict], sessions: List[Dict]) -> int:
    """
    Enrich tasks with linked_sessions based on phase/date matching.
    Uses REST API with TypeDB-backed linking.

    Returns: count of tasks updated
    """
    print("\n" + "=" * 60)
    print("PHASE 3: ENRICHING TASK → SESSION LINKAGE")
    print("=" * 60)

    # Build session lookup by date
    date_sessions: Dict[str, List[str]] = {}
    for session in sessions:
        session_id = session.get("session_id")
        start_time = session.get("start_time") or ""

        match = re.search(r'(\d{4}-\d{2}-\d{2})', start_time)
        if match:
            date = match.group(1)
            if date not in date_sessions:
                date_sessions[date] = []
            date_sessions[date].append(session_id)

    updated = 0

    for task in tasks:
        task_id = task.get("task_id")
        created_at = task.get("created_at") or ""
        current_sessions = task.get("linked_sessions") or []

        # Skip if already has sessions
        if current_sessions:
            continue

        # Extract date from created_at
        match = re.search(r'(\d{4}-\d{2}-\d{2})', created_at)
        if not match:
            continue

        task_date = match.group(1)

        # Find matching sessions
        matching_sessions = date_sessions.get(task_date, [])

        # Filter out test sessions
        real_sessions = [
            s for s in matching_sessions
            if "test-agent" not in s.lower() and "end-test" not in s.lower()
        ]

        if real_sessions:
            # Link task to first matching session via REST API
            if api_post(f"/api/tasks/{task_id}/sessions/{real_sessions[0]}"):
                updated += 1
                print(f"  [OK] {task_id}: linked to {real_sessions[0]}")

    print(f"\n  Updated {updated} tasks with session linkages")
    return updated


def main():
    print("=" * 70)
    print("DATA LINKAGE ENRICHMENT")
    print("=" * 70)
    print(f"API Base: {API_BASE}")
    print(f"Started: {datetime.now().isoformat()}")

    # Fetch current data
    print("\nFetching data...")
    tasks = api_get("/api/tasks?limit=200") or []
    sessions = api_get("/api/sessions?limit=100") or []
    rules = api_get("/api/rules?limit=100") or []

    print(f"  Tasks: {len(tasks)}")
    print(f"  Sessions: {len(sessions)}")
    print(f"  Rules: {len(rules)}")

    # Build valid rule IDs set
    valid_rule_ids = {r.get("id") for r in rules if r.get("id")}

    # Evidence directory
    evidence_dir = Path(__file__).parent.parent / "evidence"

    # Run enrichment phases
    rules_updated = enrich_task_rules(tasks, valid_rule_ids)
    evidence_updated = enrich_session_evidence(sessions, evidence_dir)
    sessions_updated = enrich_task_sessions(tasks, sessions)

    # Summary
    print("\n" + "=" * 70)
    print("ENRICHMENT SUMMARY")
    print("=" * 70)
    print(f"  Task → Rule linkages added: {rules_updated}")
    print(f"  Session → Evidence links added: {evidence_updated}")
    print(f"  Task → Session linkages added: {sessions_updated}")
    print(f"\nTotal updates: {rules_updated + evidence_updated + sessions_updated}")


if __name__ == "__main__":
    main()
