# Holographic Memory Model
**Per RULE-024 (AMNESIA Protocol) + RULE-022 (Frankel Hash)**

**Last Updated:** 2026-01-02 (DSP Cycle: P11-AUTONOMOUS-BACKLOG)

## Purpose

Prevent context window bloat by structuring rules/evidence in TypeDB for tiered access via governance MCP service.

## Access Hierarchy (Depth Levels)

```
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 0: Hash Summary Only (Minimal Context ~50 tokens)        │
│  ─────────────────────────────────────────────────────────────  │
│  Master Hash: [computed at runtime]                              │
│  Rules: 32 (29 ACTIVE, 3 DRAFT)                                  │
│  Status: HEALTHY                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓ /health or governance_health
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 1: CORE Rules Index (~250 tokens)                        │
│  ─────────────────────────────────────────────────────────────  │
│  CRITICAL (11): RULE-001,008,009,010,011,014,015,016,021,023,   │
│                 024,031                                          │
│  HIGH (19):     RULE-002,003,004,005,007,012,017,018,019,020,   │
│                 022,025,026,027,028,029,030,032                  │
│  MEDIUM (2):    RULE-006,013                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓ governance_query_rules
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 2: Rule Directives (~500 tokens per category)            │
│  ─────────────────────────────────────────────────────────────  │
│  governance_query_rules(category="governance")                   │
│  → RULE-001: Session Evidence Logging                           │
│  → RULE-006: Decision Logging                                   │
│  → RULE-011: Multi-Agent Governance                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓ governance_get_rule + evidence
┌─────────────────────────────────────────────────────────────────┐
│  LEVEL 3: Full Rule + Linked Evidence (~2000+ tokens)           │
│  ─────────────────────────────────────────────────────────────  │
│  governance_get_rule("RULE-001")                                │
│  → Full directive text                                          │
│  → Linked sessions (56)                                         │
│  → Linked tasks (17)                                            │
│  → Evidence files                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Rule Classification

### CORE Rules (Always Available in CLAUDE.md)
These are referenced in CLAUDE.md for immediate access without MCP calls:

| Rule | Name | Why CORE |
|------|------|----------|
| RULE-001 | Session Evidence Logging | Every session needs this |
| RULE-007 | MCP Usage Protocol | Every MCP call needs this |
| RULE-011 | Multi-Agent Governance | Agent coordination |
| RULE-012 | Deep Sleep Protocol | Workflow structure |
| RULE-014 | Autonomous Task Sequencing | Task execution |
| RULE-021 | MCP Healthcheck Protocol | Service integrity |
| RULE-024 | AMNESIA Protocol | Context recovery |

### UTILITY Rules (Query via MCP)
These are accessed on-demand via governance MCP:

| Category | Rules | Access Pattern |
|----------|-------|----------------|
| governance | 001,003,006,011,026,029 | governance_query_rules(category="governance") |
| testing | 004,020,025,027,028 | governance_query_rules(category="testing") |
| stability | 005,021 | governance_query_rules(category="stability") |
| strategic | 008,010,017 | governance_query_rules(category="strategic") |
| devops | 009,016 | governance_query_rules(category="devops") |
| autonomy | 014,015 | governance_query_rules(category="autonomy") |
| operational | 030,031,032 | governance_query_rules(category="operational") |
| reporting | 018,019 | governance_query_rules(category="reporting") |
| other | 002,007,012,013,022,023,024 | Various specialized categories |

## Hash-Based Change Detection

```
Master Hash: SHA256(sorted_rules)[:8]
Per-Rule Hash: SHA256(rule_id + directive)[:8]

Change Tree:
  MASTER: 7A5DCDFC
  ├── governance: A1B2C3D4
  │   ├── RULE-001: E5F6G7H8
  │   ├── RULE-006: I9J0K1L2
  │   └── RULE-011: M3N4O5P6
  ├── testing: Q7R8S9T0
  │   └── ...
  └── ...
```

## MCP Access Patterns

### Pattern 1: Session Start (Minimal)
```python
# Level 0 only - just verify hash
governance_health()
→ {"status": "healthy", "master_hash": "7A5DCDFC", "rules": 26}
```

### Pattern 2: Task Context (Targeted)
```python
# Level 2 - get relevant rules for task
governance_query_rules(category="testing")
→ [RULE-004, RULE-020, RULE-025] with directives
```

### Pattern 3: Deep Investigation (Full)
```python
# Level 3 - full rule + evidence chain
governance_get_rule("RULE-001")
governance_get_dependencies("RULE-001")
governance_evidence_search("session logging")
```

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| TypeDB Rules | ✅ 32 rules | 29 ACTIVE, 3 DRAFT |
| Hash Computation | ✅ Healthcheck | Master hash via governance_health |
| Per-Rule Hashes | ❌ TODO | Need to add to TypeDB schema |
| Category Index | ✅ Working | governance_query_rules(category=...) |
| Evidence Links | ✅ Working | governance_evidence_search |
| Rule Sync | ✅ Complete | TypeDB aligned with markdown docs |
| Conflict Detection | ✅ Working | 6 pairs detected (all false positives) |

## Next Steps

1. **Per-Rule Hash** (TOOL-022 related): Add `rule-hash` attribute to TypeDB schema
2. **Category Hash Index**: Compute category-level hashes for change detection
3. **Change Tree Visualization**: Add to healthcheck output for quick diffs
4. **Directive Compression**: Long directives → summary + hash for context efficiency

## Governance MCP Restructure Status (TOOL-007)

**Status:** DEFERRED (stability priority)

The governance MCP currently has 40+ tools. Split candidates identified:
- governance-core: Rules, agents, health, proposals (~15 tools)
- governance-session: Sessions, decisions, evidence (~10 tools)
- governance-dsm: DSM cycles, checkpoints, findings (~8 tools)
- governance-workspace: Tasks, documents, gap sync (~10 tools)

**Decision:** Defer split until rule inventory stabilizes. Current focus on rule-markdown sync and holographic access patterns.

---

*Updated per DSP cycle P11-AUTONOMOUS-BACKLOG (2026-01-02)*
