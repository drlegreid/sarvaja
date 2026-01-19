# Testing Rules

Rules governing testing strategies, quality gates, and validation protocols.

> **Parent:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `testing`, `validation`, `quality`, `guardrails`

---

## Rules Summary

| Rule | Name | Priority | Status | Type | Leaf |
|------|------|----------|--------|------|------|
| **TEST-GUARD-01-v1** | Rewrite Guardrails | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/TEST-GUARD-01-v1.md) |
| **TEST-COMP-01-v1** | Comprehensive Testing Protocol | HIGH | ACTIVE | TECHNICAL | [View](../leaf/TEST-COMP-01-v1.md) |
| **TEST-COMP-02-v1** | Test Before Commit | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/TEST-COMP-02-v1.md) |
| **TEST-FIX-01-v1** | Fix Validation Protocol | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/TEST-FIX-01-v1.md) |

---

## Quick Reference

- **TEST-GUARD-01-v1**: NEVER rewrite files >300 lines; work incrementally
- **TEST-COMP-01-v1**: All features MUST have comprehensive test coverage
- **TEST-COMP-02-v1**: Run tests BEFORE commit; no untested code in main
- **TEST-FIX-01-v1**: Fixes MUST include verification test and evidence

---

## Tags

`testing`, `validation`, `quality`, `guardrails`, `coverage`, `verification`

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
