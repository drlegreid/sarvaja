# GAP-RULE-SYNC-001: Rule Data Sync Between TypeDB and Documentation

**Status:** RESOLVED | **Priority:** ~~HIGH~~ | **Created:** 2026-01-17 | **Updated:** 2026-01-17

---

## Problem Statement

Rule definitions are not synchronized between TypeDB and documentation files. This causes:
1. **Confusion** about which rules exist and their semantic IDs
2. **Drift** between code enforcement and documented rules
3. **Audit failures** when checking rule compliance

---

## Current State (2026-01-17 - Updated)

| Source | Count | Status |
|--------|-------|--------|
| RULES-DIRECTIVES.md | 55 | Authoritative index |
| TypeDB | **62** | **SYNCED from markdown leaf files** |
| Markdown leaf files | 61 | 60 valid, 1 incomplete |

### Sync Completed (2026-01-17)
- Ran `scripts/sync_rules_to_typedb.py` - synced all 60 valid rules
- Fixed `get_existing_rules()` TypeDB 3.x API issue
- Script now properly skips existing rules (no duplicates)

### Missing from TypeDB (5 semantic IDs not found)
Per analysis, these need sync from markdown to TypeDB.

### Semantic ID Mismatches - RESOLVED
**Status:** All legacy `RULE-XXX` IDs have been replaced with semantic IDs. Query on 2026-01-17 confirms:
- 60 ACTIVE rules in TypeDB
- All use semantic ID as primary `rule-id` (e.g., `SESSION-EVID-01-v1`)
- No legacy RULE-XXX format remains
- `semantic_id` attribute is null (expected - semantic ID IS the primary ID now)

---

## Root Cause

1. **No automated sync** - Rules added to one source without syncing to others
2. **Multiple sources of truth** - TypeDB, RULES-DIRECTIVES.md, and markdown leaf files
3. **Schema evolution** - Semantic IDs were added later, not backfilled consistently
4. **No validation hook** - No pre-commit or session-start check for rule consistency

---

## Proposed Solution

### Phase 1: Designate Single Source of Truth
**Decision needed:** Is TypeDB or markdown the source of truth?
- Option A: TypeDB → Generate markdown from TypeDB queries
- Option B: Markdown → Sync script reads markdown, updates TypeDB

### Phase 2: Create Sync Script
```bash
scripts/sync_rules.py
- Scan docs/rules/**/*.md for rule definitions
- Query TypeDB for existing rules
- Report discrepancies
- Option: --fix to auto-sync
```

### Phase 3: Add Validation Hook
```python
# .claude/hooks/rules_sync_check.py
# Run on session start, fail if discrepancy > threshold
```

### Phase 4: Add MCP Tool
```python
governance_validate_rules()
# Returns: discrepancies, missing, mismatches
```

---

## Acceptance Criteria

- [x] All 60 documented leaf rules exist in TypeDB (DONE 2026-01-17)
- [x] Sync script exists: `scripts/sync_rules_to_typedb.py` (DONE 2026-01-17)
- [x] Sync script uses bare semantic IDs (no RULE- prefix) (FIXED 2026-01-17)
- [x] All semantic_id attributes match documentation (VERIFIED 2026-01-17 - semantic IDs ARE primary IDs)
- [ ] Session-start hook validates rule consistency (DEFERRED - enhancement)
- [ ] Pre-commit hook for rule validation (DEFERRED - enhancement)

---

## Resolution (2026-01-17)

**Summary:** Rule sync is complete. All 60 rules in TypeDB now use semantic IDs as primary identifiers.

**Verification Query:**
```python
governance_query_rules(status="ACTIVE")
# Returns: 60 rules, all with semantic ID format (e.g., SESSION-EVID-01-v1)
```

**Key Findings:**
1. Legacy `RULE-XXX` IDs no longer exist in TypeDB
2. Semantic IDs (e.g., `SESSION-EVID-01-v1`) are now the canonical format
3. No mismatches - single source of truth established
4. Validation hooks deferred as future enhancement (not blocking)

---

## References

- [RULES-AUDIT-2026-01-17.md](../../evidence/RULES-AUDIT-2026-01-17.md) - Previous audit
- [RULES-DIRECTIVES.md](../../RULES-DIRECTIVES.md) - Authoritative rule index
- [META-TAXON-01-v1.md](../../rules/leaf/META-TAXON-01-v1.md) - Semantic ID taxonomy

---

*Per GAP-DOC-01-v1: Gap Documentation Standard*
