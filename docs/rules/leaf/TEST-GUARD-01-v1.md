# TEST-GUARD-01-v1: In-House Rewrite Principle

**Category:** `strategic` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** FOUNDATIONAL

> **Legacy ID:** RULE-008
> **Location:** [RULES-STRATEGY.md](../technical/RULES-STRATEGY.md)
> **Tags:** `strategy`, `technology`, `rewrite`, `evaluation`

---

## Directive

When selecting technologies, prefer solutions with:
1. Comprehensive test suites (rewrite warranty)
2. Open-source with permissive licenses
3. Active development and community
4. Can be ported/rewritten in-house

---

## Technology Scorecard

| Criteria | Scale | Weight |
|----------|-------|--------|
| Test Coverage | 1-5 | HIGH |
| License Freedom | 1-5 | HIGH |
| Active Development | 1-5 | MEDIUM |
| Documentation | 1-5 | MEDIUM |
| Rewrite Feasibility | 1-5 | HIGH |

**Recommendation**: Total >= 20 = ADOPT | 15-19 = EVALUATE | <15 = REJECT

---

## Validation

- [ ] Technology scorecard completed before adoption
- [ ] Test suite reviewed and understood
- [ ] License verified compatible

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
