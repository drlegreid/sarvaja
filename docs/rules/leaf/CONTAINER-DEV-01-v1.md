# CONTAINER-DEV-01-v1: DevOps Version Compatibility Protocol

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-009
> **Location:** [RULES-TOOLING.md](../technical/RULES-TOOLING.md)
> **Tags:** `devops`, `versions`, `compatibility`, `dependencies`

---

## Directive

Before installing ANY package:
1. Check container/service version FIRST
2. Use OctoCode to find compatible versions
3. Use llm-sandbox for isolated testing
4. Verify version matrix

---

## Version Check Protocol

| Step | Tool | Command |
|------|------|---------|
| Container version | Bash | `docker logs <container> \| grep version` |
| Client compatibility | OctoCode | Search repo for version matrix |
| Isolated testing | llm-sandbox | Test import before global install |
| Dependency conflicts | pip | `pip check` after install |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `pip install <pkg>` without version | Check server version first |
| Install to global Python | Use venv or llm-sandbox |
| Guess package names | OctoCode search |

---

## Validation

- [ ] Container version checked before client install
- [ ] OctoCode used for version compatibility
- [ ] No global Python pollution

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/claude_hooks.robot` | unit |

```bash
# Run all tests validating this rule
robot --include CONTAINER-DEV-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
