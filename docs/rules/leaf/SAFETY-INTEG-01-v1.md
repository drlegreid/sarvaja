# SAFETY-INTEG-01-v1: Integrity Verification (Frankel Hash)

**Category:** `security` | **Priority:** HIGH | **Status:** DRAFT | **Type:** TECHNICAL

> **Legacy ID:** RULE-022
> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `security`, `integrity`, `hash`, `verification`

---

## Directive

Critical files MUST have integrity verification via content hashing. Use Frankel Hash for similarity detection.

---

## Use Cases

| Use Case | Hash Type | Purpose |
|----------|-----------|---------|
| Config files | SHA-256 | Detect tampering |
| Rule files | Frankel | Track incremental changes |
| Session logs | SHA-256 | Audit trail |
| TypeDB schema | Frankel | Schema evolution |

---

## Files to Track

| Category | Files | Frequency |
|----------|-------|-----------|
| Governance | `schema.tql`, `data.tql` | On change |
| Rules | `docs/rules/*.md` | On change |
| Config | `docker-compose.yml`, `.env` | Session start |
| Evidence | `evidence/*.md` | On create |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Trust files without verification | Hash critical files at session start |
| Ignore hash mismatches | Investigate and log discrepancies |
| Skip schema version tracking | Track TypeDB schema evolution |
| Commit without hash validation | Verify integrity before push |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
