# META-TAXON-02-v1: Task Type Taxonomy

**Category:** `meta` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** META

> **Location:** [RULES-GOVERNANCE.md](../RULES-GOVERNANCE.md)
> **Tags:** `meta`, `taxonomy`, `task-type`, `task-management`, `governance`
> **Supersedes:** Inline task type definitions in META-TAXON-01-v1 comments

---

## Directive

All tasks MUST use one of the **6 canonical task types** defined below. Deprecated type names are accepted at the API boundary and normalized via alias mapping. The orthogonal tag dimensions (layer, concern, method) replace the old subtype system.

## Canonical Task Types (6)

| Type | Prefix | Absorbs | Definition | When to Use |
|------|--------|---------|-----------|-------------|
| `bug` | BUG | + gap | Defect or deficiency. Something wrong, broken, or missing. | Fix it. |
| `feature` | FEAT | + story, epic | New capability or enhancement. User-facing or system-level. | Build it. |
| `chore` | CHORE | — | Maintenance: tech debt, refactor, cleanup, dependency upgrades. | Clean it up. |
| `research` | RD | — | Investigation: spike, scan, architecture exploration, vendor eval. | Explore it. |
| `spec` | SPEC | + specification | Documentation: requirements, design contracts, Gherkin scenarios. | Document it. |
| `test` | TEST | — | Verification: write, fix, or improve automated/exploratory tests. | Verify it. |

## Deprecated Type Aliases

Accepted on write, normalized to canonical type:

```python
TASK_TYPE_ALIASES = {
    'gap': 'bug',
    'story': 'feature',
    'specification': 'spec',
    'epic': 'feature',
}
```

## Orthogonal Tag Dimensions

Three independent dimensions replace the old subtype system. All optional, free-form with autocomplete.

| Dimension | TypeDB Attribute | Tags | Purpose |
|-----------|-----------------|------|---------|
| **Layer** (where) | `task-layer` | ui, api, data, infra, schema, monitoring, ci-cd | System layer |
| **Concern** (what aspect) | `task-concern` | security, performance, reliability, usability, data-integrity, compliance | Quality attribute |
| **Method** (how) | `task-method` | spike, exploratory, automated, ai-generated, gherkin, manual, draft | Work approach |

## Status Workflow (6 states)

```
TODO → OPEN → IN_PROGRESS → DONE | BLOCKED | CANCELED
```

CLOSED is removed. `normalize_status("CLOSED")` returns `"DONE"`.

## Type-Specific Quality Gates (DoD)

| Type | Required for DONE |
|------|------------------|
| `bug` | summary, agent_id, linked_sessions, evidence |
| `feature` | summary, agent_id, linked_sessions, linked_documents |
| `chore` | summary, agent_id |
| `research` | summary, agent_id, evidence (findings) |
| `spec` | summary, agent_id, linked_documents |
| `test` | summary, agent_id, evidence (test results) |

## Implementation

- Pydantic Literals: `governance/models/task.py`
- Type aliases: `agent/governance_ui/state/constants.py`
- Status enum: `governance/task_lifecycle.py`
- DoD rules: `governance/services/task_rules.py`
- Resolution templates: `governance/services/resolution_collator.py`
- Migration script: `scripts/migrate_task_taxonomy_v2.py`

---

*Per EPIC-TASK-TAXONOMY-V2 Session 4 (2026-03-24)*
