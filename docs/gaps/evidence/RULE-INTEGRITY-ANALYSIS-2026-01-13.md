# Rule Integrity Analysis Report

**Date:** 2026-01-13 | **Per:** GOV-RULE-02-v1 (Rule Compliance Verification)

---

## Executive Summary

| Metric | Count | Status |
|--------|-------|--------|
| Total Rules | 38 | - |
| Healthy Rules | 15 | OK |
| MEDIUM Issues | 22 | Orphaned (21) + Over-connected (1) |
| LOW Issues | 20 | Under-documented |
| Conflicts | 18 unique pairs | Review needed |

---

## MEDIUM Severity Issues

### Issue 1: Orphaned Rules (21 rules)

**Problem:** Rules with no dependents (nothing depends on them).

**Analysis:** Most "orphaned" rules are actually **leaf rules** - they're designed to be standalone operational rules that don't need other rules to depend on them. This is a false positive from the analysis tool.

**Proposed Fix:** Introduce a `rule_type` classification in TypeDB:

| Type | Description | Example |
|------|-------------|---------|
| `FOUNDATIONAL` | Base rules, others depend on them | SESSION-EVID-01-v1, GOV-BICAM-01-v1 |
| `OPERATIONAL` | Standalone operational rules | CONTAINER-RESTART-01-v1, DOC-SIZE-01-v1 |
| `LEAF` | Terminal rules, no dependents expected | SAFETY-DESTR-01-v1, RECOVER-CRASH-01-v1 |
| `META` | Rules about rules | META-TAXON-01-v1 |

**Classification of Orphaned Rules:**

| Semantic ID | Legacy | Type | Reason |
|-------------|--------|------|--------|
| GOV-PROP-02-v1 | RULE-019 | LEAF | UI/UX standards - standalone |
| WORKFLOW-RD-01-v1 | RULE-015 | OPERATIONAL | R&D workflow - standalone |
| GOV-PROP-01-v1 | RULE-013 | LEAF | Applicability convention |
| RECOVER-AMNES-01-v1 | RULE-024 | OPERATIONAL | AMNESIA protocol - standalone |
| UI-TRAME-01-v1 | RULE-017 | LEAF | Trame patterns - standalone |
| SAFETY-HEALTH-01-v1 | RULE-021 | OPERATIONAL | MCP health - standalone |
| TEST-COMP-01-v1 | RULE-020 | LEAF | E2E testing - standalone |
| GOV-BICAM-01-v1 | RULE-011 | FOUNDATIONAL | Should have dependents! |
| ARCH-INFRA-01-v1 | RULE-016 | LEAF | Infrastructure - standalone |
| GOV-RULE-02-v1 | RULE-026 | LEAF | Context communication |
| WORKFLOW-AUTO-02-v1 | RULE-031 | OPERATIONAL | Task continuation |
| CONTAINER-RESTART-01-v1 | RULE-027 | LEAF | API restart - standalone |
| DOC-LINK-01-v1 | RULE-034 | LEAF | Document linking - standalone |
| WORKFLOW-SEQ-01-v1 | RULE-028 | LEAF | Change validation |
| RECOVER-CRASH-01-v1 | RULE-041 | LEAF | Crash prevention - standalone |
| GOV-RULE-03-v1 | RULE-029 | LEAF | Executive reporting |
| DOC-SIZE-01-v1 | RULE-032 | LEAF | File size - standalone |
| DOC-PARTIAL-01-v1 | RULE-033 | LEAF | PARTIAL handling |
| CONTAINER-SHELL-01-v1 | RULE-035 | LEAF | Shell selection - standalone |
| ARCH-MCP-02-v1 | RULE-036 | LEAF | MCP separation |
| ARCH-INFRA-02-v1 | RULE-040 | LEAF | Portable config |

**Action Items:**

1. **RULE-011 (GOV-BICAM-01-v1)** - FOUNDATIONAL rule should have dependents
   - Add: RULE-018 (GOV-TRUST-02-v1) depends on RULE-011
   - Add: RULE-025 (GOV-PROP-03-v1) depends on RULE-011

2. **Update TypeDB schema** to support `rule_type` attribute
3. **Classify all rules** by type (already done in leaf files)

---

### Issue 2: Over-Connected Rule (1 rule)

**Rule:** WORKFLOW-RD-01-v1 (RULE-015) - R&D Workflow with Human Approval

**Dependencies (8):**
1. ARCH-MCP-01-v1 (RULE-007) - MCP Usage
2. SESSION-EVID-01-v1 (RULE-001) - Evidence Logging
3. WORKFLOW-AUTO-01-v1 (RULE-014) - Autonomous Sequencing
4. GOV-TRUST-01-v1 (RULE-006) - Decision Logging
5. RECOVER-MEM-01-v1 (RULE-005) - Memory Stability
6. SESSION-DSM-01-v1 (RULE-012) - Deep Sleep Protocol
7. TEST-GUARD-01-v1 (RULE-008) - Rewrite Guardrails
8. GOV-RULE-01-v1 (RULE-010) - Evidence-Based Wisdom

**Analysis:** This is the main R&D workflow rule that orchestrates many aspects:
- MCP usage (tooling)
- Evidence logging (governance)
- Task sequencing (workflow)
- Decision tracking (governance)
- Memory management (stability)
- DSP hygiene (maintenance)
- Rewrite guardrails (quality)
- Wisdom accumulation (strategic)

**Proposed Fix Options:**

| Option | Description | Effort |
|--------|-------------|--------|
| A. Keep as-is | Accept high coupling for orchestration rule | None |
| B. Create abstraction | Add GOV-WORKFLOW-01-v1 intermediate rule | Medium |
| C. Split rule | Break into R&D-APPROVAL and R&D-WORKFLOW | High |

**Recommendation:** **Option A** - Keep as-is. This is an orchestration rule by design. The 8 dependencies represent legitimate integrations for a comprehensive R&D workflow.

---

## LOW Severity Issues

### Issue 3: Under-Documented Rules (20 rules)

**Problem:** Rules not referenced by any document in TypeDB document-references-rule relation.

**Root Cause:** The document linking was done before the semantic ID migration. Need to re-sync.

**Action:** Run `workspace_link_rules_to_documents()` to refresh relations.

**Affected Rules:**
- RULE-015, 016, 017, 018, 019, 020, 023, 024
- RULE-026, 027, 028, 029, 031, 032, 033, 034, 035, 036
- RULE-040, 041

---

## Conflict Analysis

### Governance Cluster (Not True Conflicts)

| Pair | Analysis |
|------|----------|
| RULE-006 ↔ RULE-011 | Both governance - complementary |
| RULE-006 ↔ RULE-029 | Decision logging vs Executive reporting - complementary |
| RULE-006 ↔ RULE-001 | Decision vs Session evidence - complementary |
| RULE-006 ↔ RULE-034 | Decision vs Document linking - complementary |
| RULE-006 ↔ RULE-026 | Decision vs Context communication - complementary |

**Verdict:** These are all governance rules that work together. Not conflicts.

### Technical Pair

| Pair | Analysis |
|------|----------|
| RULE-008 ↔ RULE-017 | Rewrite guardrails vs Cross-workspace patterns |
| RULE-010 ↔ RULE-017 | Wisdom accumulation vs Cross-workspace patterns |

**Verdict:** RULE-017 (UI-TRAME-01-v1) deals with UI patterns while RULE-008/010 deal with code rewrite and wisdom. No actual conflict.

### Stability Pair

| Pair | Analysis |
|------|----------|
| RULE-005 ↔ RULE-021 | Memory stability vs MCP healthcheck |

**Verdict:** Complementary - both deal with system stability. RULE-021 is more specific (MCP health) while RULE-005 is broader (memory thresholds).

### Operations Cluster

| Pair | Analysis |
|------|----------|
| RULE-031 ↔ RULE-033 | Task continuation vs PARTIAL handling |
| RULE-031 ↔ RULE-035 | Task continuation vs Shell selection |
| RULE-033 ↔ RULE-041 | PARTIAL handling vs Crash prevention |
| RULE-035 ↔ RULE-041 | Shell selection vs Crash prevention |

**Verdict:** Operational rules in same domain. Complementary, not conflicting.

---

## Recommended Actions

### Immediate (This Session)

1. **Add `rule_type` to TypeDB schema**
   - FOUNDATIONAL, OPERATIONAL, LEAF, META

2. **Fix RULE-011 dependencies**
   - Make GOV-TRUST-02-v1 depend on GOV-BICAM-01-v1
   - Make GOV-PROP-03-v1 depend on GOV-BICAM-01-v1

3. **Re-sync document relations**
   - Run `workspace_link_rules_to_documents()`

### MCP Update - GAP-MCP-008 (RESOLVED)

**GAP ID:** GAP-MCP-008
**Priority:** HIGH
**Status:** RESOLVED (2026-01-13)

#### Solution Implemented

Updated `governance/rule_linker.py` with:

1. **Dual pattern matching**: `extract_rule_ids()` function matches both legacy and semantic patterns
2. **Recursive scanning**: `scan_rule_documents()` now scans subdirectories (leaf/, governance/, etc.)
3. **ID normalization**: `normalize_rule_id()` converts semantic IDs to legacy for TypeDB compatibility
4. **Mapping table**: `SEMANTIC_TO_LEGACY` dict with 43 rule ID mappings

**Implementation:**
```python
# governance/rule_linker.py
LEGACY_RULE_PATTERN = r'RULE-\d{3}'
SEMANTIC_RULE_PATTERN = r'[A-Z]+-[A-Z]+-\d{2}-v\d+'

def extract_rule_ids(content: str) -> List[str]:
    # Matches both patterns, converts semantic to legacy
    ...
```

**Results:**
- 54 documents scanned (up from 9)
- 203 document-rule relations created
- TypeDB now has 41 rules (RULE-001 to RULE-043)

#### Files Requiring Update

| File | Function | Change |
|------|----------|--------|
| `governance_mcp/workspace/scanner.py` | `_extract_rule_refs()` | Dual pattern matching |
| `governance_mcp/typedb/rules.py` | `get_rule()` | Accept semantic IDs |
| `governance_mcp/typedb/schema.typeql` | - | Add `legacy_id` attribute |

#### Acceptance Criteria

1. `workspace_link_rules_to_documents()` finds rules referenced by semantic ID
2. `governance_get_rule("SESSION-EVID-01-v1")` returns rule data
3. `governance_query_rules()` can filter by `rule_type` (FOUNDATIONAL, OPERATIONAL, LEAF, META)
4. Legacy IDs still work (backward compatible)

#### Implementation Steps

1. **Add legacy ID field to TypeDB**
   - `legacy_id` attribute for backward compatibility

2. **Update MCP tools to support semantic IDs**
   - Accept both RULE-XXX and DOMAIN-SUB-NN-vN formats

3. **Add rule_type to governance_query_rules**

---

## Conclusion

The rule integrity issues are mostly **structural/organizational** rather than **true defects**:

| Issue Type | Root Cause | Fix Complexity |
|------------|------------|----------------|
| Orphaned | Missing rule_type classification | LOW |
| Over-connected | Orchestration rule by design | NONE |
| Under-documented | Post-migration sync needed | LOW |
| Conflicts | Same-domain complementary rules | NONE |

**No CRITICAL or HIGH severity issues found.**

---

*Per GOV-RULE-02-v1: Rule Compliance Verification*
*Per META-TAXON-01-v1: Rule Taxonomy & Management*
