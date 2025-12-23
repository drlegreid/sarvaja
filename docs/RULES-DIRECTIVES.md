# Sim.ai Rules Directives

## Overview

This document defines mandatory rules for the Sim.ai PoC agent platform.
Rules are indexed in ChromaDB (`sim_ai_rules` collection) and enforced by agents.

---

## Rule Categories

| Category | Priority | Enforcement |
|----------|----------|-------------|
| `governance` | CRITICAL | Mandatory |
| `architecture` | HIGH | Mandatory |
| `observability` | HIGH | Mandatory |
| `security` | HIGH | Mandatory |
| `performance` | MEDIUM | Advisory |
| `style` | LOW | Advisory |

---

## RULE-001: Session Evidence Logging

**Category:** `governance`  
**Priority:** CRITICAL  
**Status:** ACTIVE  
**Effectiveness Score:** N/A (new)

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale
   - Alternatives considered and why rejected
   - Assumptions made and their basis

2. **Artifact Tracking**
   - Files created/modified with timestamps
   - Dependencies introduced
   - Configuration changes

3. **Session Metadata**
   - Session ID, start/end times
   - Models invoked with token counts
   - Tools used with invocation counts

4. **Export Requirements**
   - Session logs exported to `./docs/SESSION-{date}-{topic}.md`
   - Machine-readable YAML metadata block
   - Human-readable narrative

### Implementation

```python
# Session logging structure
session_log = {
    "session_id": str,
    "timestamp": datetime,
    "thought_chain": [
        {
            "step": int,
            "decision": str,
            "rationale": str,
            "alternatives": list[str],
            "confidence": float  # 0-1
        }
    ],
    "artifacts": [
        {
            "path": str,
            "action": "create|modify|delete",
            "timestamp": datetime
        }
    ],
    "metadata": {
        "models": dict,
        "tools": dict,
        "tokens": int
    }
}
```

### Validation

- [ ] Session log exists in `./docs/`
- [ ] Contains thought chain with ≥3 decision points
- [ ] Metadata block is valid YAML
- [ ] All artifacts are tracked

---

## RULE-002: Architectural & Design Best Practices

**Category:** `architecture`  
**Priority:** HIGH  
**Status:** ACTIVE  
**Effectiveness Score:** N/A (new)

### Directive

All code and system design MUST follow:

1. **Separation of Concerns**
   - Each component has single responsibility
   - Clear boundaries between layers (Agent, Routing, Storage, Observability)
   - No circular dependencies

2. **Configuration Over Code**
   - Environment variables for secrets and endpoints
   - YAML/JSON for model configurations
   - No hardcoded values in source

3. **Observability by Default**
   - All agent calls traced via Opik
   - Health endpoints for every service
   - Structured logging (JSON format)

4. **Graceful Degradation**
   - Fallback models configured in LiteLLM
   - Service health checks with retries
   - Timeout handling for all external calls

5. **Idempotency**
   - Agent operations should be safely retriable
   - Database operations use upsert patterns
   - No side effects on read operations

6. **Documentation**
   - README for every component
   - Inline comments for non-obvious logic
   - API contracts documented

### Implementation Checklist

```yaml
architectural_compliance:
  separation_of_concerns:
    - agent_layer_isolated: true
    - routing_layer_isolated: true
    - storage_layer_isolated: true
  configuration:
    - secrets_in_env: true
    - no_hardcoded_urls: true
    - yaml_configs_validated: true
  observability:
    - opik_tracing_enabled: true
    - health_endpoints_exist: true
    - structured_logging: true
  degradation:
    - fallback_models_configured: true
    - timeouts_configured: true
    - retries_implemented: true
```

### Validation

- [ ] No circular imports detected
- [ ] All secrets in `.env` (not in code)
- [ ] Health endpoint returns 200
- [ ] Opik traces visible in dashboard

---

## RULE-003: Sync Protocol for Skills & Sessions

**Category:** `governance`  
**Priority:** HIGH  
**Status:** DRAFT  
**Effectiveness Score:** N/A (new)

### Directive

Local skills and sessions MUST be syncable to:
- Remote storage (optional cloud backup)
- Team shared repositories
- Cross-device continuity

### Sync Agent Design

See `./docs/SYNC-AGENT-DESIGN.md` for implementation.

---

## Rule Index (ChromaDB Schema)

```json
{
  "collection": "sim_ai_rules",
  "schema": {
    "id": "rule_{number}",
    "document": "Full rule text",
    "metadata": {
      "category": "string",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "status": "ACTIVE|DRAFT|DEPRECATED",
      "effectiveness_score": "float 0-1",
      "created_at": "ISO datetime",
      "updated_at": "ISO datetime",
      "version": "semver"
    }
  }
}
```

---

## Enforcement

Rules are enforced via:
1. **Pre-commit hooks** - Static validation
2. **CI/CD checks** - Test suite includes rule compliance
3. **Runtime guards** - Agent checks rules before execution
4. **Opik metrics** - Track rule violation rates

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2024-12-24 | Initial rules: Session Evidence, Architecture |
