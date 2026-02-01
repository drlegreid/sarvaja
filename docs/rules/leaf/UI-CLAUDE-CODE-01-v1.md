# UI-CLAUDE-CODE-01-v1: Claude Code Integration Patterns

**Category:** `technical` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Tags:** `claude-code`, `hooks`, `mcp`, `settings`, `ide`

---

## Directive

All Claude Code integrations (hooks, MCP servers, slash commands, settings) MUST follow the official Claude Code documentation patterns. Reference the canonical docs before implementing any Claude Code feature.

---

## Key Patterns

### Hooks
- Pre/Post tool use hooks in `.claude/hooks/`
- Hook events: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`
- Hooks receive JSON input on stdin, return JSON on stdout
- Use for validation, logging, and automation gates

### MCP Servers
- Configured in `.mcp.json` at project root
- Servers: governance-core, governance-agents, governance-sessions, governance-tasks, claude-mem
- Each server exposes typed tools via FastMCP
- Health checks via `health_check()` tool per server

### Settings & Configuration
- Project settings in `.claude/settings.json`
- Agent visibility in `.claude/agents/SESSION_VISIBILITY.json`
- CLAUDE.md for project-level instructions (loaded automatically)

### IDE Integration
- VS Code extension: native inline diffs, @-mentions, plan review
- JetBrains plugin: IDE diff viewing, context sharing
- Both connect to same Claude Code CLI backend

---

## References

- [Claude Code Overview](https://code.claude.com/docs/en/overview)
- [GitHub Repository](https://github.com/anthropics/claude-code)
- [MCP Configuration](../../.claude/MCP.md)
- [Hooks Documentation](../../.claude/HOOKS.md)

---

## Validation

- [ ] Hook implementations follow pre/post pattern
- [ ] MCP servers registered in `.mcp.json`
- [ ] Settings documented in CLAUDE.md
- [ ] IDE integrations tested

---

*Per PLAN-UI-OVERHAUL-001 Task R.1*
