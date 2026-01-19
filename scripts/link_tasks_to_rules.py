#!/usr/bin/env python3
"""
Task→Rule Auto-Linker Script (REST API version).

Per GAP-UI-AUDIT-001: Rules→tasks linkage at 0%.
Uses REST API for reliability.

Usage:
    python3 scripts/link_tasks_to_rules.py --dry-run
    python3 scripts/link_tasks_to_rules.py
"""

import argparse
import re
import httpx

API_BASE = "http://localhost:8082"


def extract_rule_refs(text: str) -> list[str]:
    """Extract rule IDs from text."""
    if not text:
        return []
    rules = []
    # Legacy: RULE-XXX
    rules.extend(re.findall(r'\bRULE-\d{3}\b', text, re.IGNORECASE))
    # Semantic: PREFIX-NAME-NN-vN
    rules.extend(re.findall(r'\b[A-Z]+-[A-Z]+-\d{2}-v\d+\b', text, re.IGNORECASE))
    return list(set([r.upper() for r in rules]))


def infer_rules(desc: str) -> list[str]:
    """Infer rules from keywords."""
    keywords = {
        "evidence": ["SESSION-EVID-01-v1"],
        "session": ["SESSION-EVID-01-v1"],
        "trust": ["GOV-BICAM-01-v1"],
        "test": ["TEST-COMP-02-v1"],
        "container": ["CONTAINER-DEV-01-v1"],
        "typedb": ["CONTAINER-TYPEDB-01-v1"],
        "workflow": ["WORKFLOW-AUTO-01-v1"],
        "mcp": ["ARCH-MCP-01-v1"],
        "safety": ["SAFETY-HEALTH-01-v1"],
        "governance": ["GOV-RULE-01-v1"],
    }
    found = []
    desc_lower = (desc or "").lower()
    for kw, rule_ids in keywords.items():
        if kw in desc_lower:
            found.extend(rule_ids)
    return list(set(found))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    print("=" * 50)
    print("Task→Rule Linker (GAP-UI-AUDIT-001)")
    print("=" * 50)

    with httpx.Client(timeout=30.0) as client:
        # Get rules
        resp = client.get(f"{API_BASE}/api/rules?limit=100")
        data = resp.json()
        rules = data.get("items", data) if isinstance(data, dict) else data
        rule_ids = set(r.get("id") or r.get("rule_id") for r in rules)
        print(f"Loaded {len(rule_ids)} rules")

        # Get tasks
        resp = client.get(f"{API_BASE}/api/tasks?limit={args.limit}")
        tasks = resp.json().get("items", [])
        print(f"Processing {len(tasks)} tasks")

        created = 0
        for task in tasks:
            task_id = task.get("task_id")
            text = f"{task.get('name', '')} {task.get('description', '')}"

            # Find rules
            found = extract_rule_refs(text)
            if not found:
                found = infer_rules(text)

            # Filter to existing rules
            found = [r for r in found if r in rule_ids]

            for rule_id in found:
                if args.dry_run:
                    print(f"  [DRY] {task_id} → {rule_id}")
                    created += 1
                else:
                    try:
                        resp = client.post(
                            f"{API_BASE}/api/tasks/{task_id}/rules/{rule_id}"
                        )
                        if resp.status_code in (200, 201):
                            print(f"  ✓ {task_id} → {rule_id}")
                            created += 1
                        else:
                            print(f"  ✗ {task_id}: {resp.status_code}")
                    except Exception as e:
                        print(f"  ✗ {task_id}: {e}")

        print("=" * 50)
        print(f"Links {'would be ' if args.dry_run else ''}created: {created}")


if __name__ == "__main__":
    main()
