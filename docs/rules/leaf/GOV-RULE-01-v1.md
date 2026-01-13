# GOV-RULE-01-v1: Evidence-Based Wisdom Accumulation

**Category:** `strategic` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** FOUNDATIONAL

> **Legacy ID:** RULE-010
> **Location:** [RULES-STRATEGY.md](../technical/RULES-STRATEGY.md)
> **Tags:** `evidence`, `wisdom`, `learning`, `hypothesis`

---

## Directive

Every experiment MUST produce traceable evidence:
1. Use MCPs for detailed evidence
2. Hypothesis-based approach
3. Logical decision making
4. Test-caught failures = learning opportunities

---

## Evidence Pipeline

```mermaid
flowchart LR
    MCP[MCP Output] --> E[Evidence]
    E --> A[Analysis]
    A --> D[Decision]
    D --> R[TypeDB Rule]
```

---

## MCP Usage for Evidence

| Evidence Type | MCP Tool |
|---------------|----------|
| API exploration | llm-sandbox |
| Version checks | powershell |
| Code patterns | OctoCode |
| Memory storage | claude-mem |

---

## Validation

- [ ] MCPs used instead of manual operations
- [ ] Hypothesis documented before testing
- [ ] Evidence collected in structured format

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
