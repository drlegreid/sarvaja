# GAP-DATA-SYNC-001: TypeDB Data vs Semantic Taxonomy Sync

**Status**: COMPLETE
**Priority**: MEDIUM
**Category**: Data Integrity
**Created**: 2026-01-17
**Completed**: 2026-01-17

## Problem Statement

The TypeDB `data.tql` file contains 25 governance rules (RULE-001 to RULE-025), while the semantic taxonomy in `docs/rules/leaf/` has 60 rule files. This means 35+ rules are documented but not loaded into TypeDB.

## Resolution

Implemented **Option A: Batch Insert Script**

### Scripts Created
- [scripts/sync_rules_to_typedb.py](../../../scripts/sync_rules_to_typedb.py) - Main sync script
- [scripts/sync_rules.sh](../../../scripts/sync_rules.sh) - Wrapper to use python3

### Execution Results (2026-01-17)

```
Found 60 rule files in docs/rules/leaf/
Parsed 58 valid rules (2 missing required fields)
Found 25 existing rules in TypeDB
Inserted: 33 new rules
Skipped (exists): 25
Failed: 0
Total rules in TypeDB: 58
```

### API Verification
- Dashboard API returns 50 rules (some filtered by status)
- All ACTIVE rules visible in UI

## Files with Missing Fields

| File | Issue |
|------|-------|
| TEST-BDD-01-v1.md | Missing required fields |
| TEST-UI-VERIFY-01-v1.md | Missing required fields |

## Final State

| Source | Count | Status |
|--------|-------|--------|
| `governance/data.tql` | 25 rules | Original seed data |
| TypeDB database | 58 rules | Synced from docs |
| API response | 50 rules | Active rules only |
| `docs/rules/leaf/*.md` | 60 files | 2 incomplete |

## Related

- META-TAXON-01-v1: Rule Taxonomy & Management
- GAP-GOVERNANCE-AUDIT-001: Rule compliance audit
- GAP-TYPEDB-INFERENCE-001: TypeDB 3.x inference functions
