# GAP-RULE-DATA-QUALITY-001: TypeDB Rule Data Quality

**Status:** RESOLVED | **Priority:** HIGH | **Type:** DATA_QUALITY

## Summary

18+ rules in TypeDB have `rule_type: null` and most have `semantic_id: null`, degrading holographic memory effectiveness.

## Observations (2026-01-24)

Query `rules_query()` returned 36 rules, analysis shows:

**Rules with `rule_type: null`:**
- SESSION-EVID-01-v1 (CRITICAL)
- ARCH-VERSION-01-v1 (CRITICAL)
- GOV-RULE-01-v1 (CRITICAL)
- GOV-BICAM-01-v1 (CRITICAL)
- WORKFLOW-AUTO-02-v1 (CRITICAL)
- WORKFLOW-RD-02-v1 (CRITICAL)
- ARCH-INFRA-02-v1 (CRITICAL)
- SAFETY-HEALTH-02-v1 (CRITICAL)
- RECOVER-AMNES-02-v1 (CRITICAL)
- ARCH-EBMSF-01-v1 (HIGH)
- GOV-AUDIT-01-v1 (HIGH)
- RECOVER-MEM-01-v1 (HIGH)
- ARCH-MCP-02-v1 (HIGH)
- SESSION-DSM-01-v1 (HIGH)
- UI-TRAME-01-v1 (HIGH)
- REPORT-OBJ-01-v1 (HIGH)
- UI-DESIGN-02-v1 (HIGH)
- REPORT-EXEC-01-v1 (HIGH)

## Impact

1. **Holographic Memory Degradation**: L1 (TypeDB) cannot provide proper rule classification
2. **Agent Wisdom Filtering**: `wisdom_get()` cannot filter by rule_type effectively
3. **Applicability Implementation Blocked**: RD-RULE-APPLICABILITY depends on complete metadata

## Root Cause

Historical migration from legacy RULE-XXX IDs to semantic IDs left metadata incomplete.

## Resolution Plan

1. Batch update all 36 rules with correct `rule_type`:
   - GOVERNANCE: SESSION-*, GOV-*, REPORT-*
   - OPERATIONAL: WORKFLOW-*, CONTAINER-*, DOC-*, TEST-*
   - TECHNICAL: ARCH-*, UI-*
   - META: META-*
   - SAFETY: SAFETY-*, RECOVER-*

2. Set `semantic_id` = `id` for all rules (they already use semantic format)

## Resolution (2026-01-24)

**Fixed by batch rule_update calls:**
- Updated 22 rules with proper `rule_type` (GOVERNANCE, OPERATIONAL, TECHNICAL, SAFETY, META)
- Set `semantic_id` = `id` for all rules
- All 34 ACTIVE rules now have complete metadata

**Rule Type Distribution (post-fix):**
| Type | Count |
|------|-------|
| OPERATIONAL | 14 |
| TECHNICAL | 8 |
| GOVERNANCE | 8 |
| LEAF | 1 |
| META | 1 |
| SAFETY | 1 |

## Related

- RD-RULE-APPLICABILITY: Now unblocked - can proceed with implementation
- META-TAXON-01-v1: Taxonomy now enforced in TypeDB

---
*Per META-TAXON-01-v1: Rule Taxonomy & Management*
