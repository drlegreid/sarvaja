# WORKFLOW-AUTO-01-v1: Autonomous Task Sequencing

**Category:** `autonomy` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-014
> **Location:** [RULES-WORKFLOW.md](../operational/RULES-WORKFLOW.md)
> **Tags:** `autonomy`, `sequencing`, `halt`, `priority`

---

## Directive

Agents MUST autonomously sequence tasks according to product strategy. Continue until explicit halt command.

---

## Halt Commands

| Command | Action |
|---------|--------|
| `STOP` | Immediate halt, save state |
| `HALT` | Immediate halt, save state |
| `STAI` | Immediate halt, save state |
| `RED ALERT` | Emergency stop |
| `ALERT` | Pause and await |

---

## Priority Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **P0** | Blocking production | Execute immediately |
| **P1** | Strategic milestone | Execute in sequence |
| **P2** | Technical hygiene | Execute during DSP |
| **P3** | Nice-to-have | Queue for later |

---

## Validation

- [ ] Tasks sequenced by priority
- [ ] Halt commands recognized
- [ ] State saved on halt

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
