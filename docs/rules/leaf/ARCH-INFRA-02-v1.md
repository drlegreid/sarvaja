# ARCH-INFRA-02-v1: Portable Configuration Patterns

**Category:** `tooling` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Legacy ID:** RULE-040
> **Location:** [RULES-TOOLING.md](../technical/RULES-TOOLING.md)
> **Tags:** `configuration`, `portability`, `cross-platform`, `scripts`

---

## Directive

All configuration files MUST use portable patterns that work across environments.

---

## Required Patterns

| Pattern | Implementation | Rationale |
|---------|---------------|-----------|
| **Relative paths** | `scripts/runner.sh` not `/home/user/...` | Works across systems |
| **Wrapper scripts** | `mcp-runner.sh` handles venv | Abstracts environment |
| **LF line endings** | `sed -i 's/\r$//'` | Cross-platform compat |
| **Env variables** | `${workspaceFolder}`, `$HOME` | IDE/shell portability |

---

## MCP Configuration Pattern

```json
{
  "command": "bash",
  "args": ["scripts/mcp-runner.sh", "module.name"],
  "cwd": "${workspaceFolder}"
}
```

---

## Wrapper Script Template

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[ -f "$HOME/.venv/sim-ai/bin/activate" ] && source "$HOME/.venv/sim-ai/bin/activate"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
exec python -m "$1"
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `/home/user/.venv/python` | Wrapper script with `$HOME` |
| Windows CRLF in scripts | Always use LF, fix with `sed` |
| Hardcoded `python3.x` | Let venv provide `python` |

---

## Validation

- [ ] No absolute paths in .mcp.json
- [ ] All scripts have LF line endings
- [ ] Wrapper script tested after creation

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
