# GAP-TYPEDB-INFERENCE-001: Migrate Inference Rules to TypeDB 3.x Functions

**Status**: COMPLETE
**Priority**: HIGH
**Category**: Infrastructure
**Created**: 2026-01-17
**Completed**: 2026-01-17

## Problem Statement

TypeDB 3.x replaces inference rules (`rule ... when ... then ...`) with functions (`fun ... -> ... : match ... return ...`). Our governance schema has 5 disabled inference rules that need migration.

## Affected Rules

| Original Rule | Purpose | New Function |
|---------------|---------|--------------|
| `transitive-dependency` | If A→B and B→C, then A→C | `transitive_dependencies()` |
| `cascade-supersede` | Decision supersession cascades to rules | `cascaded_decision_affects()` |
| `priority-conflict` | Detect conflicting rules in same category | `priority_conflicts()` |
| `escalation-required` | Mark proposals needing human review | `escalated_proposals()` |
| `proposal-cascade` | Proposal affects cascade through dependencies | `proposal_cascade_affects()` |

## Key Differences: Rules vs Functions

| Aspect | Rules (2.x) | Functions (3.x) |
|--------|-------------|-----------------|
| Syntax | `rule name: when {...} then {...}` | `fun name() -> type: match {...} return {...}` |
| Execution | Automatic inference | Explicit call via `let...in` |
| Materialization | Silent data completion | Separate query construct |
| Schema impact | Infers type instances | Returns computed results |

## Implementation

Functions defined in: `governance/schema/31_inference_functions.tql`

### Usage Pattern

```typeql
# Get all transitive dependencies
match
  let $dep, $rule in transitive_dependencies();
  $dep has rule-id $depId;
  $rule has rule-id $ruleId;
```

## References

- [TypeDB Functions Documentation](https://typedb.com/docs/typeql-reference/functions/)
- [Functions vs Rules](https://typedb.com/docs/typeql-reference/functions/functions-vs-rules/)
- [TypeDB 2.x to 3.x Migration](https://typedb.com/docs/reference/typedb-2-vs-3/process/)

## Evidence

- Schema file: `governance/schema/30_inference_rules.tql` (disabled rules)
- New functions: `governance/schema/31_inference_functions.tql`
- Test: `tests/integration/test_typedb_functions.py`

### Verification Results (2026-01-17)

| Function | Results | Notes |
|----------|---------|-------|
| `transitive_dependencies()` | 54 results | 34 direct + 20 transitive via recursion |
| `priority_conflicts()` | 10 results | Rules in same category with different priorities |
| `cascaded_decision_affects()` | 3 results | Decision→rule relationships |
| `escalated_proposals()` | 0 results | No disputes with escalation (expected) |
| `proposal_cascade_affects()` | 0 results | No proposal-affects relations (expected) |

## Related

- GAP-TYPEDB-UPGRADE-001: TypeDB 3.x migration
- GAP-TYPEDB-DRIVER-001: Driver API changes
