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

## Test Coverage

**7 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/agents_split.robot` | unit |
| `tests/robot/unit/context_preloader_split.robot` | unit |
| `tests/robot/unit/dsm_tracker_split.robot` | unit |
| `tests/robot/unit/embedding_pipeline_split.robot` | unit |
| `tests/robot/unit/mcp_server_split.robot` | unit |
| `tests/robot/unit/routes_chat_split.robot` | unit |
| `tests/robot/unit/ui_infra.robot` | unit |

```bash
# Run all tests validating this rule
robot --include DOC-SIZE-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
