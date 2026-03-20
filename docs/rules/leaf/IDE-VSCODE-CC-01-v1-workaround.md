# IDE-VSCODE-CC-01-v1: Workaround — bypassPermissions in VSCode Extension

> Linked rule: [IDE-VSCODE-CC-01-v1](IDE-VSCODE-CC-01-v1.md)
> Upstream: [anthropics/claude-code#20536](https://github.com/anthropics/claude-code/issues/20536)

---

## Environment

| Component | Version |
|---|---|
| **OS** | Ubuntu 25.10, Linux 6.17.0-19-generic x86_64 |
| **VSCode** | 1.112.0 (x64) |
| **Claude Code Extension** | anthropic.claude-code@2.1.79 |
| **Mode** | VSCode native chat panel (NOT CLI in terminal) |

---

## Problem

`defaultMode: "bypassPermissions"` alone was ignored by the extension. Granular per-command entries like `Bash(curl:*)` worked, but broad wildcards like `Read(*)` did not. MCP tool calls always prompted.

---

## Workaround: Belt-and-Suspenders Config

The key insight: **both** `defaultMode: "bypassPermissions"` AND explicit tool wildcards are needed together. Neither alone is sufficient.

### Step 1 — `~/.claude/settings.json` (global)

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
      "Skill(*)"
    ],
    "defaultMode": "bypassPermissions"
  }
}
```

### Step 2 — `.claude/settings.local.json` (project-level, same permissions block)

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
      "Skill(*)"
    ],
    "defaultMode": "bypassPermissions"
  }
}
```

### Step 3 — VSCode User Settings (`~/.config/Code/User/settings.json`)

```json
{
  "claudeCode.allowDangerouslySkipPermissions": true,
  "claudeCode.initialPermissionMode": "bypassPermissions"
}
```

### Step 4 — Restart VSCode completely (not just reload window)

---

## Verification

After applying, tested 10 tools across all categories — zero permission prompts:

| Tool | Auto-approved? |
|---|---|
| `Bash(echo ...)` | Yes |
| `Bash(podman compose ps)` | Yes |
| `Read(file)` | Yes |
| `Edit(file)` | Yes |
| `Glob(*.md)` | Yes |
| `Grep(pattern)` | Yes |
| MCP tool calls (5 different servers) | Yes |

---

## Extension Logs

Log location: `~/.config/Code/logs/{session}/window1/exthost/Anthropic.claude-code/Claude VSCode.log`

### Permission evaluation (working — not blocked)

```
2026-03-20T20:01:45.045Z [DEBUG] bashToolHasPermission: tree-sitter unavailable, using legacy shell-quote path
```

### Settings loading — 3 locations checked, 2 missing is normal

```
2026-03-20T19:56:42.542Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /project/.claude/settings.json
2026-03-20T19:56:42.544Z [DEBUG] Broken symlink or missing file encountered for settings.json at path: /etc/claude-code/managed-settings.json
```

The extension reads settings from:
1. `~/.claude/settings.json` — global (read successfully)
2. `.claude/settings.local.json` — project-level (read successfully)
3. `/etc/claude-code/managed-settings.json` — enterprise (missing, expected)

> **Note:** `.claude/settings.json` (without `.local`) at project level logs as "Broken symlink" — the extension only looks for `settings.local.json` at project scope.

---

## Notes

- MCP tool wildcards also work with the `mcp__servername__*` pattern in the allow list.
- Previously only `defaultMode: "acceptEdits"` was set with per-command Bash entries — switching to `"bypassPermissions"` + full wildcard list fixed it.
- The `tree-sitter unavailable` log line is cosmetic — permission check falls back to `shell-quote` parser and works fine.

---

*Verified 2026-03-20 | Workaround for upstream bug [#20536](https://github.com/anthropics/claude-code/issues/20536)*
