# IDE-VSCODE-CC-01-v1: VSCode Claude Code Permission Bypass Bug & Mitigations

**Category:** `technical` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** KNOWN-ISSUE

> **Tags:** `ide`, `vscode`, `claude-code`, `permissions`, `bypass`, `workaround`

---

## Linked Documents

- **Workaround (GitHub-ready):** [IDE-VSCODE-CC-01-v1-workaround.md](IDE-VSCODE-CC-01-v1-workaround.md)

---

## Summary

The Claude Code VSCode extension does NOT reliably respect `bypassPermissions` mode or wildcard permissions from `~/.claude/settings.json`. The extension has its own permission handling layer that diverges from the CLI backend. This is an **upstream bug** in `anthropics/claude-code` — tracked across multiple issues since July 2025, still open as of March 2026 (v2.1.79).

---

## Upstream References

| Issue | Title | Status | Key Info |
|-------|-------|--------|----------|
| [#20536](https://github.com/anthropics/claude-code/issues/20536) | bypassPermissions mode not working in VS Code extension | OPEN | Primary report, detailed repro steps |
| [#2933](https://github.com/anthropics/claude-code/issues/2933) | VS Code Extension Ignores Global dangerously-skip-permissions | OPEN | Oldest report (Jul 2025), 20+ comments, regression history |
| [#18191](https://github.com/anthropics/claude-code/issues/18191) | VSCode extension ignores wildcard permissions in settings.json | OPEN | Wildcard inconsistency (Bash(*) works, Read(*) doesn't) |

---

## Root Cause Analysis

The VSCode extension's native webview UI implements **its own permission dialog system** separate from the CLI:

1. **Config is read but mode is ignored** — `model` setting works, `defaultMode: "bypassPermissions"` does not
2. **Wildcard matching diverges from CLI** — `Bash(*)` and `Grep(*)` work, `Read(*)` and `WebFetch(*)` do not
3. **VSCode-specific settings ineffective** — `claudeCode.allowDangerouslySkipPermissions: true` and `claudeCode.initialPermissionMode: "bypassPermissions"` are not reliably applied
4. **Regression pattern** — partially fixed in v2.0.35 (Nov 2025), regressed in subsequent versions
5. **Cross-platform** — confirmed on Linux, macOS, Windows (including Remote SSH)

The extension likely either:
- Does not pass `--dangerously-skip-permissions` to the spawned CLI process
- Overrides the config's permission mode with its own default
- Has a separate permission matcher that handles wildcards differently

---

## Impact on This Project

**STATUS: MITIGATED (2026-03-20)** — W1 applied and verified. All 5 tool categories auto-approve.

Previously our settings used `defaultMode: "acceptEdits"` with granular per-command Bash entries, missing built-in tools (`Read`, `Edit`, `Write`, `Glob`, `Grep`, `WebFetch`, `WebSearch`, `Agent`) and all MCP tools. This caused prompts on every non-Bash tool call in the VSCode panel.

---

## Workarounds (Ordered by Effectiveness)

### W1: Explicit Allow List + bypassPermissions (APPLIED — verified 2026-03-20)

Set `defaultMode: "bypassPermissions"` AND add every tool + MCP wildcard to **both** `~/.claude/settings.json` (global) and `.claude/settings.local.json` (project):

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Edit(*)",
      "Write(*)",
      "Glob(*)",
      "Grep(*)",
      "WebFetch(*)",
      "WebSearch(*)",
      "Agent(*)",
      "NotebookEdit(*)",
      "Skill(*)",
      "mcp__gov-core__*",
      "mcp__gov-agents__*",
      "mcp__gov-sessions__*",
      "mcp__gov-tasks__*",
      "mcp__claude-mem__*",
      "mcp__log-analyzer__*",
      "mcp__playwright__*",
      "mcp__rest-api__*"
    ],
    "defaultMode": "bypassPermissions"
  }
}
```

Also set in VSCode user settings (`~/.config/Code/User/settings.json`):
```json
{
  "claudeCode.allowDangerouslySkipPermissions": true,
  "claudeCode.initialPermissionMode": "bypassPermissions"
}
```

**Verified working** on Claude Code extension v2.1.79 + VSCode 1.110.1 (Linux). All built-in tools and MCP tools auto-approve. The key was combining `defaultMode: "bypassPermissions"` with explicit wildcards — neither alone was sufficient.

**Note**: Earlier reports said `Read(*)` and `WebFetch(*)` were ignored. With the full config above (both defaultMode AND wildcards), they work. MCP wildcards (`mcp__server__*`) also work.

### W2: CLI in Terminal (FULL bypass)

Use the Claude Code CLI directly instead of the VSCode panel:

```bash
# In VSCode integrated terminal
claude --dangerously-skip-permissions
```

Or add a VSCode task (`.vscode/tasks.json`):

```json
{
  "version": "2.0.0",
  "tasks": [{
    "label": "Claude Code (bypass)",
    "type": "shell",
    "command": "claude --dangerously-skip-permissions",
    "presentation": { "reveal": "always", "panel": "dedicated" }
  }]
}
```

**Limitation**: Loses native VSCode inline diff UI, @-mentions, and plan review features.

### W3: Pin Extension Version

If a working version is identified, pin it and disable auto-updates:

```json
// VSCode settings.json
{
  "extensions.autoUpdate": false
}
```

v2.0.35 was reported working (Nov 2025) but is now outdated.

### W4: Community Patcher (USE WITH CAUTION)

[claude-code-extension-patcher](https://github.com/jimmy927/claude-code-extension-patcher) patches the extension JS directly to force bypass mode.

**Risks**: Breaks on every extension update, modifies signed extension code, potential security implications.

---

## Recommended Configuration for This Project

**Belt-and-suspenders** approach (all 3 layers):

1. **Global** `~/.claude/settings.json`: `defaultMode: "bypassPermissions"` + full wildcard allow list (W1)
2. **Project** `.claude/settings.local.json`: same config, duplicated for defense-in-depth
3. **VSCode** `~/.config/Code/User/settings.json`:
   ```json
   {
     "claudeCode.allowDangerouslySkipPermissions": true,
     "claudeCode.initialPermissionMode": "bypassPermissions"
   }
   ```
4. For heavy automation sessions (DSP, orchestrator), prefer CLI in terminal (W2) as additional fallback

---

## Validation

- [x] Explicit allow list covers all frequently-used tools (applied 2026-03-20)
- [x] VSCode settings configured as defense-in-depth (pre-existing)
- [x] CLI fallback documented for automation-heavy sessions
- [x] Tested: Bash, Glob, Grep, Read, MCP tools — all auto-approve (2026-03-20)
- [ ] Upstream issues monitored for resolution

---

## Monitoring

Check upstream status periodically:
```bash
gh issue view 20536 --repo anthropics/claude-code --json state,comments
gh issue view 2933 --repo anthropics/claude-code --json state,comments
```

When upstream is resolved, this rule can be deprecated.

---

*Created 2026-03-20 | Upstream bug, no local code fix possible*
