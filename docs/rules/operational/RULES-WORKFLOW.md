# Workflow Rules - Sim.ai

Rules governing task sequencing, autonomy, and context recovery.

> **Parent:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `workflow`, `autonomy`, `context`, `dsp`

---

## Rules Summary

| Rule | Name | Priority | Status | Type | Leaf |
|------|------|----------|--------|------|------|
| **SESSION-DSM-01-v1** | Deep Sleep Protocol (DSP) | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/SESSION-DSM-01-v1.md) |
| **WORKFLOW-AUTO-01-v1** | Autonomous Task Sequencing | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/WORKFLOW-AUTO-01-v1.md) |
| **WORKFLOW-RD-01-v1** | R&D Workflow with Human Approval | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/WORKFLOW-RD-01-v1.md) |
| **RECOVER-AMNES-01-v1** | AMNESIA Protocol | CRITICAL | ACTIVE | TECHNICAL | [View](../leaf/RECOVER-AMNES-01-v1.md) |
| **WORKFLOW-AUTO-02-v1** | Autonomous Task Continuation | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/WORKFLOW-AUTO-02-v1.md) |
| **WORKFLOW-SEQ-01-v1** | Multi-Session Task Continuity | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/WORKFLOW-SEQ-01-v1.md) |

---

## Quick Reference

- **SESSION-DSM-01-v1**: DSP phases: AUDIT -> HYPOTHESIZE -> MEASURE -> OPTIMIZE -> VALIDATE -> DREAM -> REPORT
- **WORKFLOW-AUTO-01-v1**: Continue tasks until HALT command (STOP|HALT|STAI|RED ALERT)
- **WORKFLOW-RD-01-v1**: R&D tasks require human approval unless DEEP autonomy
- **RECOVER-AMNES-01-v1**: Recover context autonomously using hierarchical sources
- **WORKFLOW-AUTO-02-v1**: Continue until ALL tasks complete or explicit halt
- **WORKFLOW-SEQ-01-v1**: Multi-session tasks MUST have continuity evidence

---

## Tags

`workflow`, `autonomy`, `dsp`, `context`, `amnesia`, `recovery`, `sequencing`

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
