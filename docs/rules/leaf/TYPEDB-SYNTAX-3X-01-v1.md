---
rule_id: TYPEDB-SYNTAX-3X-01-v1
name: TypeDB 3.x Query Syntax Reference
status: ACTIVE
category: technical
priority: HIGH
applicability: MANDATORY
---

## Rule

When writing TypeDB queries, use **TypeDB 3.x syntax** — not 2.x patterns. Always verify syntax against official docs before assuming "TypeDB doesn't support this".

## Critical Syntax Differences (3.x vs 2.x)

### Delete a relation

**Wrong (2.x — causes REP1 Thing/ThingType conflict):**
```typeql
match
    $t isa task, has task-id "TASK-001";
    $d isa document, has document-path "docs/foo.md";
    $rel (referencing-document: $d, referenced-task: $t) isa document-references-task;
delete $rel;
```

**Correct (3.x — use `links` syntax):**
```typeql
match
    $t isa task, has task-id "TASK-001";
    $d isa document, has document-path "docs/foo.md";
    $rel isa document-references-task,
        links (referencing-document: $d, referenced-task: $t);
delete $rel;
```

### Delete forms (3.x)

| Form | Purpose |
|------|---------|
| `delete $x;` | Delete entire instance (entity, relation, attribute) |
| `delete has $attr of $owner;` | Remove attribute ownership |
| `delete links ($player) of $rel;` | Remove role player from relation |

### Match syntax

| 2.x (WRONG) | 3.x (CORRECT) |
|-------------|---------------|
| `$rel (role: $x) isa type` | `$rel isa type, links (role: $x)` |
| `delete $x isa person;` | `delete $x;` |
| `$x has name $n; delete $x has name $n;` | `delete has $n of $x;` |

## Rationale

**Origin (2026-03-28):** `unlink_task_from_document` used 2.x relation match syntax in the delete query. TypeDB 3.x raised `REP1: variable cannot be declared as both Thing and ThingType`. The bug was invisible to unit tests (mocked TypeDB client) and only surfaced during E2E testing against live TypeDB.

## Driver Version

- Server: TypeDB 3.x (container: `platform_typedb_1`)
- Driver: `typedb-driver>=3.7.0,<4.0.0` (currently 3.8.1)
- Database: `sim-ai-governance` (env: `TYPEDB_DATABASE`)
- Auth: `Credentials('admin', 'password')`, `DriverOptions(is_tls_enabled=False)`

## Do / Don't

| Don't | Do Instead |
|-------|------------|
| Guess at TypeDB syntax | Check official docs or this rule |
| Assume mocked tests prove TypeDB queries work | Run against live TypeDB (per SCHEMA-VERIFY-01-v1) |
| Copy 2.x patterns from old code | Use 3.x `links`/`of` syntax |
