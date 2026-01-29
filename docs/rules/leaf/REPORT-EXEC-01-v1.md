# REPORT-EXEC-01-v1: Integrity Verification (Frankel Hash)

**Category:** `safety` | **Priority:** HIGH | **Status:** DRAFT | **Type:** OPERATIONAL

> **Tags:** `safety`, `integrity`, `frankel-hash`, `verification`

---

## Directive

Critical governance operations MUST be verified using the Frankel Hash integrity mechanism. The hash provides a deterministic fingerprint of system state for audit trail integrity.

---

## Frankel Hash Specification

| Property | Value |
|----------|-------|
| **Algorithm** | SHA-256 truncated to 8 uppercase hex characters |
| **Inputs** | Service health, rule count, agent count, memory usage |
| **Display** | Infrastructure view, status bar, executive reports |
| **Update** | On each healthcheck cycle |

---

## Usage

```python
# Hash computation
hash_input = f"{typedb_ok}:{chromadb_ok}:{rules_count}:{agents_count}:{memory_pct}"
frankel_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
```

---

## Executive Report Integration

Executive reports MUST include:
1. Current Frankel hash for verification
2. Generated timestamp for temporal context
3. Session ID for traceability

---

## Tool Bindings (GOV-BIND-01-v1)

| Verification | Tool | Example |
|-------------|------|---------|
| Hash check | Bash | `curl -s localhost:8082/api/health \| jq .frankel_hash` |
| Infrastructure | `mcp__playwright__browser_navigate` | Check Infrastructure view |
| Report | `mcp__rest-api__test_request` | `GET /api/reports/executive` |

---

## Validation

- [ ] Frankel hash displayed in Infrastructure view
- [ ] Hash changes when system state changes
- [ ] Executive report includes verification data
- [ ] Hash is deterministic (same state = same hash)

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per GOV-BIND-01-v1: Tool bindings specified*
