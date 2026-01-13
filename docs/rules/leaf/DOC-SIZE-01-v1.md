# DOC-SIZE-01-v1: File Size & OOP Standards

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-032
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `architecture`, `files`, `oop`, `standards`

---

## Directive

All source files MUST stay under 300 lines. When exceeded, IMMEDIATELY refactor using OOP/modular design.

---

## Hard Limits

| Lines | Status | Action |
|-------|--------|--------|
| <= 200 | HEALTHY | No action |
| 201-300 | WARNING | Consider splitting |
| >300 | **VIOLATION** | MUST split immediately |

---

## Decomposition Heuristics

| Signal | Action |
|--------|--------|
| File >300 lines | Split by entity |
| Class >200 lines | Extract concerns |
| Function >50 lines | Compose smaller functions |
| Mixed concerns | Separate layers |

---

## Validation

- [ ] All files under 300 lines
- [ ] OOP principles followed
- [ ] Clear layer boundaries

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
