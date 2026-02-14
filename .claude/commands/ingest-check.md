---
description: Assess rule and task ingestion completeness (TypeDB vs docs)
allowed-tools: mcp__gov-core__rules_query, mcp__gov-tasks__tasks_list, mcp__gov-tasks__workspace_scan_rule_documents, Glob, Read, Bash
---

# Ingestion Gap Assessment

Assess how many rules and tasks are in TypeDB vs what exists in docs/files.

## Steps

### 1. Rule Coverage
- Count leaf docs: `Glob("docs/rules/leaf/*.md")`
- Query TypeDB rules: `rules_query(query="*", limit=200)`
- Compare: which leaf docs have no matching TypeDB rule?
- Flag CRITICAL rules that are missing

### 2. Task Coverage
- Query TypeDB tasks: `tasks_list(limit=200)`
- Scan workspace: `workspace_scan_rule_documents` for TODO items
- Read TODO.md for provisional tasks
- Compare: which documented tasks are not in TypeDB?

### 3. Gap Analysis
- List rules missing from TypeDB (by leaf doc name)
- List tasks missing from TypeDB (by phase)
- Identify test artifacts that should be cleaned up
- Check for TypeDB-only entries with no docs

### 4. Recommendations
- Prioritize CRITICAL missing rules for immediate ingestion
- Suggest batch ingestion commands
- Estimate effort for full sync

## Output Format

```
=== INGESTION GAP REPORT ===

Rules: {typedb_count}/{leaf_count} ({pct}% coverage)
  Missing CRITICAL: {list}
  Missing HIGH: {list}

Tasks: {typedb_count}/{doc_count} ({pct}% coverage)
  Phase gaps: {phases with 0 coverage}

Cleanup: {test artifacts to remove}

Recommended Actions:
1. ...
2. ...
```
