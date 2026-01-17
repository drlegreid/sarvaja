# WORKFLOW-SHELL-01-v1: Shell Command Portability

**Category:** `operational` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-NEW
> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `shell`, `python`, `devops`, `portability`, `wrappers`

---

## Directive

Agents MUST use portable shell commands. Never use bare `python` - always use `python3` or project wrapper scripts.

---

## Problem Statement

On many Linux systems (including xubuntu), `python` is not linked to any Python version:
```bash
$ python --version
bash: python: command not found

$ python3 --version
Python 3.13.1
```

This causes repeated failures in Claude Code sessions when scripts use bare `python`.

---

## Required Patterns

### Python Execution

| Pattern | Command | When to Use |
|---------|---------|-------------|
| **Direct execution** | `python3 script.py` | Quick one-off scripts |
| **Module execution** | `python3 -m pytest` | Python modules |
| **Project wrapper** | `scripts/python.sh -m module` | Container-based execution |
| **pytest wrapper** | `scripts/pytest.sh tests/` | All test runs |

### Shell Wrappers Available

| Wrapper | Purpose |
|---------|---------|
| `scripts/python.sh` | Run Python in governance container |
| `scripts/pytest.sh` | Run pytest in container |
| `scripts/mcp-runner.sh` | Run MCP commands |
| `scripts/load-schema.sh` | Load TypeDB schema |

---

## Anti-Patterns (NEVER DO)

```bash
# WRONG - fails on systems without python symlink
python script.py
python -m pytest
python -c "import foo"

# CORRECT - explicit python3
python3 script.py
python3 -m pytest
python3 -c "import foo"

# ALSO CORRECT - use wrapper for container
scripts/python.sh script.py
scripts/pytest.sh tests/
```

---

## Enforcement

Claude Code agents should:
1. Always use `python3` instead of `python`
2. Use wrapper scripts when executing in containers
3. Update documentation that shows bare `python` commands

---

## Related

- CONTAINER-DEV-01-v1: Container-first development
- ARCH-INFRA-02-v1: Infrastructure patterns

---

*Per META-TAXON-01-v1: Semantic rule naming*
*Created: 2026-01-17 after repeated python command failures*
