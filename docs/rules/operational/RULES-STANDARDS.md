# Standards Rules

Rules governing development standards, DevOps, and documentation.

> **Parent:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `standards`, `devops`, `documentation`, `safety`

---

## Rules Summary

| Rule | Name | Priority | Status | Type | Leaf |
|------|------|----------|--------|------|------|
| **CONTAINER-RESTART-01-v1** | API Server Restart Protocol | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/CONTAINER-RESTART-01-v1.md) |
| **CONTAINER-DEV-02-v1** | Docker Dev Container Workflow | HIGH | **DISABLED** | LEAF | [View](../leaf/CONTAINER-DEV-02-v1.md) |
| **DOC-SIZE-01-v1** | File Size & OOP Standards | HIGH | ACTIVE | TECHNICAL | [View](../leaf/DOC-SIZE-01-v1.md) |
| **DOC-PARTIAL-01-v1** | PARTIAL Task Handling | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/DOC-PARTIAL-01-v1.md) |
| **DOC-LINK-01-v1** | Relative Document Linking | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/DOC-LINK-01-v1.md) |
| **CONTAINER-SHELL-01-v1** | Shell Command Environment Selection | HIGH | ACTIVE | OPERATIONAL | [View](../leaf/CONTAINER-SHELL-01-v1.md) |
| **TEST-FIX-01-v1** | Fix Validation Protocol | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/TEST-FIX-01-v1.md) |
| **SAFETY-DESTR-01-v1** | Destructive Command Prevention | CRITICAL | ACTIVE | OPERATIONAL | [View](../leaf/SAFETY-DESTR-01-v1.md) |

---

## Quick Reference

- **CONTAINER-RESTART-01-v1**: ALWAYS restart API servers after code changes before testing
- **CONTAINER-DEV-02-v1**: **DISABLED** - Use Podman workflows instead (see CONTAINER-SHELL-01-v1)
- **DOC-SIZE-01-v1**: Files MUST stay under 300 lines
- **DOC-PARTIAL-01-v1**: Mark large tasks as PARTIAL, create subtasks <2 hours
- **DOC-LINK-01-v1**: ALL document references MUST use relative markdown links
- **CONTAINER-SHELL-01-v1**: **ALWAYS use Podman MCP** for container operations
- **TEST-FIX-01-v1**: Fixes MUST include verification test and evidence
- **SAFETY-DESTR-01-v1**: NEVER execute destructive commands without confirmation

---

## Tags

`standards`, `devops`, `documentation`, `safety`, `podman`, `files`, `validation`, `linking`

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
