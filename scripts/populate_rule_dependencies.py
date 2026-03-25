#!/usr/bin/env python3
"""
Populate rule-dependency relations in TypeDB from rule document cross-references.

Parses docs/rules/leaf/*.md files for references to other rules (semantic IDs),
then creates rule-dependency relations in TypeDB directly.

Usage:
    .venv/bin/python3 scripts/populate_rule_dependencies.py
    .venv/bin/python3 scripts/populate_rule_dependencies.py --dry-run
    .venv/bin/python3 scripts/populate_rule_dependencies.py --verify
"""

import argparse
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

API_URL = "http://localhost:8082"
RULES_DIR = Path(__file__).parent.parent / "docs" / "rules" / "leaf"

# Regex to find semantic rule IDs like SESSION-EVID-01-v1, ARCH-MCP-02-v1
SEMANTIC_ID_PATTERN = re.compile(
    r'\b([A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d{2}-v\d+)\b'
)


def extract_rule_id_from_filename(filepath: Path) -> str:
    """Extract rule ID from filename: ARCH-MCP-02-v1.md -> ARCH-MCP-02-v1."""
    return filepath.stem


def find_cross_references(filepath: Path) -> set:
    """Find all semantic rule IDs referenced in a markdown file."""
    content = filepath.read_text(encoding="utf-8")
    matches = SEMANTIC_ID_PATTERN.findall(content)
    return set(matches)


def build_dependency_graph(rules_dir: Path) -> dict:
    """
    Build a dependency graph from rule documents.

    Returns:
        dict: {rule_id: set of rule_ids it references}
    """
    graph = {}
    rule_files = sorted(rules_dir.glob("*.md"))

    for filepath in rule_files:
        rule_id = extract_rule_id_from_filename(filepath)
        refs = find_cross_references(filepath)
        # Remove self-references
        refs.discard(rule_id)
        if refs:
            graph[rule_id] = refs

    return graph


def verify_graph(graph: dict) -> dict:
    """Verify graph stats including cycle detection.

    Args:
        graph: Adjacency dict {rule_id: set of dep_ids}

    Returns:
        Dict with nodes, edges, cycles stats.
    """
    from governance.services.dependency_graph import DependencyGraph

    dg = DependencyGraph(graph)
    cycles = dg.detect_cycles()
    return {
        "nodes": dg.node_count,
        "edges": dg.edge_count,
        "cycles": cycles,
        "circular_count": len(cycles),
        "is_acyclic": dg.is_acyclic,
    }


def populate_via_typedb(graph: dict, existing_rules: set, dry_run: bool = False) -> dict:
    """Insert rule-dependency relations directly into TypeDB.

    Idempotent: checks existing dependencies before creating.
    """
    stats = {"scanned": len(graph), "relations_created": 0, "skipped": 0, "errors": 0}

    try:
        from governance.stores import get_typedb_client
        client = get_typedb_client()
        if not client:
            print("TypeDB not connected")
            return stats
    except Exception as e:
        print(f"Cannot connect to TypeDB: {e}")
        return stats

    for rule_id, deps in sorted(graph.items()):
        if rule_id not in existing_rules:
            continue

        # Idempotency: fetch existing deps for this rule
        existing_deps = set(client.get_rule_dependencies(rule_id))

        for dep_id in sorted(deps):
            if dep_id not in existing_rules:
                stats["skipped"] += 1
                continue

            # Skip if relation already exists
            if dep_id in existing_deps:
                stats["skipped"] += 1
                print(f"  [SKIP] {rule_id} -> {dep_id} (already exists)")
                continue

            if dry_run:
                print(f"  [DRY] {rule_id} -> {dep_id}")
                stats["relations_created"] += 1
            else:
                try:
                    if client.create_rule_dependency(rule_id, dep_id):
                        stats["relations_created"] += 1
                        print(f"  Created: {rule_id} -> {dep_id}")
                    else:
                        stats["errors"] += 1
                        print(f"  Failed: {rule_id} -> {dep_id}")
                except Exception as e:
                    stats["errors"] += 1
                    print(f"  Error {rule_id}->{dep_id}: {e}")

    return stats


def get_existing_rules_via_api() -> set:
    """Get existing rule IDs from the API."""
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        resp = client.get("/api/rules?limit=200")
        if resp.status_code == 200:
            data = resp.json()
            rules_list = data.get("items", data) if isinstance(data, dict) else data
            return {r.get("id") for r in rules_list}
    return set()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate rule dependencies in TypeDB")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--verify", action="store_true", help="Report graph stats and cycles")
    args = parser.parse_args()

    if not RULES_DIR.exists():
        print(f"Rules directory not found: {RULES_DIR}")
        sys.exit(1)

    print(f"Scanning {RULES_DIR}...")
    graph = build_dependency_graph(RULES_DIR)

    total_deps = sum(len(deps) for deps in graph.values())
    print(f"Found {len(graph)} rules with cross-references ({total_deps} total refs)")

    # Show top referencing rules
    for rule_id, deps in sorted(graph.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"  {rule_id}: references {len(deps)} rules")

    if args.verify:
        stats = verify_graph(graph)
        print(f"\nGraph verification:")
        print(f"  Nodes: {stats['nodes']}")
        print(f"  Edges: {stats['edges']}")
        print(f"  Acyclic: {stats['is_acyclic']}")
        print(f"  Circular count: {stats['circular_count']}")
        if stats['cycles']:
            for i, cycle in enumerate(stats['cycles'], 1):
                print(f"  Cycle {i}: {' -> '.join(cycle)}")
        sys.exit(0)

    # Get existing rules
    existing_rules = get_existing_rules_via_api()
    print(f"Found {len(existing_rules)} rules in TypeDB")

    result = populate_via_typedb(graph, existing_rules, dry_run=args.dry_run)

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode}Results: {result}")
    sys.exit(0)
