# GOV-MODE-01-v1: Governance Mode Configuration

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** META

> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `governance`, `mode`, `configuration`, `hybrid`

---

## Directive

Governance rules support hybrid enforcement modes. Mode selection determines whether rules are self-enforced (single agent) or externally validated (auditor agent).

---

## Modes

### 1. Single Agent Mode (Default)
```yaml
mode: single
enforcement: self-check
validation: inline
overhead: minimal
```

**Characteristics:**
- Agent self-enforces rules via checkpoints
- No external validation required
- Lower latency, lower cost
- Suitable for routine tasks

**Rules with self-enforcement:**
- FEEDBACK-LOGIC-01-v1 (anti-sycophancy)
- INTENT-CHECK-01-v1 (intent verification)
- REPORT-HUMOR-01-v1 (session humor)

### 2. Auditor Agent Mode
```yaml
mode: auditor
enforcement: external
validation: handoff
overhead: moderate
```

**Characteristics:**
- Primary agent submits work for review
- Auditor agent validates against rules
- Higher assurance, higher cost
- Suitable for critical decisions

**Rules benefiting from auditor:**
- GOV-BICAM-01-v1 (bicameral decisions)
- FEEDBACK-LOGIC-01-v1 (blind spot detection)
- INTENT-CHECK-01-v1 (independent verification)

### 3. Hybrid Mode (Recommended)
```yaml
mode: hybrid
enforcement: adaptive
validation: risk-based
overhead: optimized
```

**Characteristics:**
- Mode switches based on task risk/complexity
- Low-risk: single agent
- High-risk: auditor validation
- Best of both worlds

---

## Configuration

### Workspace Config (workspaces/{role}/config.yaml)
```yaml
governance:
  mode: hybrid  # single | auditor | hybrid

  # Mode triggers for hybrid
  triggers:
    auditor_required:
      - rule_creation
      - rule_modification
      - gap_closure_critical
      - security_decisions

    single_sufficient:
      - documentation
      - test_execution
      - routine_queries
      - gap_closure_low
```

### Runtime Override
```python
# In MCP tool call
governance_set_mode(mode="auditor", scope="session")
```

---

## Mode Selection Matrix

| Task Type | Risk | Recommended Mode |
|-----------|------|------------------|
| Rule creation | HIGH | auditor |
| Rule modification | HIGH | auditor |
| Gap closure (CRITICAL) | HIGH | auditor |
| Gap closure (LOW) | LOW | single |
| Documentation | LOW | single |
| Test execution | MEDIUM | single |
| Security decisions | HIGH | auditor |
| Routine queries | LOW | single |

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Single agent checkpoints | ACTIVE | Built into rules |
| Auditor handoff protocol | PLANNED | RD-WORKSPACE Phase 5 |
| Hybrid mode router | PLANNED | Needs implementation |
| Mode config schema | ACTIVE | This document |

---

## Integration Points

1. **Rule Loading:** Mode determines which checkpoints activate
2. **Task Routing:** Mode influences workspace selection
3. **Evidence Collection:** Mode affects audit trail depth
4. **Trust Scoring:** Auditor mode increases trust weight

---

## Validation

- [ ] Mode specified in workspace config
- [ ] Triggers defined for hybrid mode
- [ ] Rules implement mode-specific enforcement
- [ ] Handoff protocol documented for auditor mode

---

*Per GOV-RULE-01-v1: Governance Rule Supremacy*
*Per ARCH-MCP-02-v1: MCP Server Architecture*
