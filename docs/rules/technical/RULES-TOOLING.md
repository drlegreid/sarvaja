# Tooling Rules - Sim.ai

Rules governing MCP usage, version compatibility, and tooling protocols.

> **Parent:** [RULES-TECHNICAL.md](../RULES-TECHNICAL.md)
> **Rules:** RULE-007, RULE-009, RULE-040

---

## RULE-007: MCP Usage Protocol

**Category:** `productivity` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** RECOMMENDED

### Directive

All sessions MUST actively leverage available MCPs according to task type.

### MCP Usage Matrix

| Task Type | Required MCPs | Optional MCPs |
|-----------|---------------|---------------|
| Session Start | claude-mem, filesystem | sequential-thinking |
| Code Research | octocode, filesystem | claude-mem |
| Implementation | filesystem, powershell | llm-sandbox, git |
| Testing | playwright, powershell | desktop-commander |
| Complex Analysis | sequential-thinking | claude-mem |

### Active MCPs

| MCP | Purpose |
|-----|---------|
| **claude-mem** | Memory persistence (ChromaDB) |
| **sequential-thinking** | Structured reasoning |
| **filesystem** | File operations |
| **git** | Version control |
| **powershell** | Windows automation |
| **llm-sandbox** | Code execution |

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Manual GitHub search | Use octocode MCP |
| Copy-paste context | Query claude-mem |
| Ad-hoc decisions | Use sequential-thinking |

### Validation
- [ ] Session starts with claude-mem context query
- [ ] Research tasks use octocode
- [ ] Complex decisions use sequential-thinking

---

## RULE-009: DevOps Version Compatibility Protocol

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

Before installing ANY package:
1. Check container/service version FIRST
2. Use OctoCode to find compatible versions
3. Use llm-sandbox for isolated testing
4. Verify version matrix

### Version Check Protocol

| Step | Tool | Command |
|------|------|---------|
| Container version | Bash | `docker logs <container> \| grep version` |
| Client compatibility | OctoCode | Search repo for version matrix |
| Isolated testing | llm-sandbox | Test import before global install |
| Dependency conflicts | pip | `pip check` after install |

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `pip install <pkg>` without version | Check server version first |
| Install to global Python | Use venv or llm-sandbox |
| Guess package names | OctoCode search |

### Validation
- [ ] Container version checked before client install
- [ ] OctoCode used for version compatibility
- [ ] No global Python pollution

---

## RULE-040: Portable Configuration Patterns

**Category:** `tooling` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

All configuration files MUST use portable patterns that work across environments.

### Required Patterns

| Pattern | Implementation | Rationale |
|---------|---------------|-----------|
| **Relative paths** | `scripts/runner.sh` not `/home/user/...` | Works across systems |
| **Wrapper scripts** | `mcp-runner.sh` handles venv | Abstracts environment |
| **LF line endings** | `sed -i 's/\r$//'` | Cross-platform compat |
| **Env variables** | `${workspaceFolder}`, `$HOME` | IDE/shell portability |

### MCP Configuration Pattern

```json
{
  "command": "bash",
  "args": ["scripts/mcp-runner.sh", "module.name"],
  "cwd": "${workspaceFolder}"
}
```

### Wrapper Script Template

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
[ -f "$HOME/.venv/sim-ai/bin/activate" ] && source "$HOME/.venv/sim-ai/bin/activate"
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
exec python -m "$1"
```

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `/home/user/.venv/python` | Wrapper script with `$HOME` |
| Windows CRLF in scripts | Always use LF, fix with `sed` |
| Hardcoded `python3.x` | Let venv provide `python` |

### Validation
- [ ] No absolute paths in .mcp.json
- [ ] All scripts have LF line endings
- [ ] Wrapper script tested after creation

### Evidence
- DECISION-006: Portable MCP Configuration Patterns (2026-01-09)

---

*Per RULE-012: DSP Semantic Code Structure*
