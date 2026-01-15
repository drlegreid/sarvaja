# MCP Server Configuration

> **Version**: 1.1.0 | **Updated**: 2026-01-10 | **Per**: R&D TOOL-009, xubuntu migration

## Overview

This project uses multiple MCP (Model Context Protocol) servers to extend Claude Code capabilities. MCP configs are split between global (user) and project-local settings.

## Configuration Locations

| File | Scope | Purpose |
|------|-------|---------|
| `~/.claude.json` | Global (user) | MCP servers available in all projects |
| `.mcp.json` | Project | Project-specific MCP servers |
| `.claude/mcp-backup.json` | Backup | Disabled MCPs with restore metadata |

## MCP Classification

MCPs are classified by criticality and always-on requirements:

### CORE MCPs (Always Required)

These MCPs are **essential for project operation**. Session health depends on them.

| Server | Purpose | Source | Dependency |
|--------|---------|--------|------------|
| `claude-mem` | Memory via ChromaDB | Global | ChromaDB :8001 |
| `gov-core` | Rules, decisions, health | Project | TypeDB :1729 |
| `gov-agents` | Agents, trust, proposals | Project | TypeDB :1729 |
| `gov-sessions` | Sessions, DSM, evidence | Project | TypeDB :1729 |
| `gov-tasks` | Tasks, workspace, gaps | Project | TypeDB :1729 |
| `sequential-thinking` | Reasoning chains for complex tasks | Global | None |
| `desktop-commander` | Desktop interaction, exploratory testing | Global | None |
| `playwright` | Browser automation | Global | Node.js (nvm) |
| `podman` | Container management | Project | Podman daemon |
| `rest-api` | REST API calls | Project | None |
| `git` | Git operations (via Bash on Linux) | Bash | None |

> **xubuntu Note**: Node.js installed via nvm (v20.19.6). Playwright MCP now available.
> Python `playwright` library also available as fallback in ~/.venv/sarvaja.

**Health Check**: `governance_health` validates CORE dependencies at session start.

### UTILITY MCPs (Optional)

These MCPs provide **convenience features** but aren't required for core operation.

| Server | Purpose | Source | When Needed |
|--------|---------|--------|-------------|
| `llm-sandbox` | Python code execution | Global | Code sandbox tasks |

### DISABLED MCPs (in mcp-backup.json)

These MCPs were disabled due to resource or stability concerns.

| Server | Reason | Risk | Re-enable When |
|--------|--------|------|----------------|
| `filesystem` | Redundant with Read/Write tools | LOW | Never |
| `godot-mcp` | Game dev specific | LOW | Godot projects |
| `octocode` | Rate limits, external API crashes | HIGH | Never |
| `powershell` | xubuntu migration (use Bash) | LOW | Never |

### HIGH-RISK MCPs (Never Enable)

| Server | Issue | Removed Date |
|--------|-------|--------------|
| `context7` | NPX cold start, external API | 2024-12-14 |
| `octocode` | Rate limits, crashes | 2026-01-01 |

## Backup & Restore

### Backup Current Config

```powershell
# PowerShell
.\.claude\scripts\mcp-backup.ps1

# Bash
./.claude/scripts/mcp-backup.sh

# Python directly
python .claude/scripts/mcp-backup.py
```

### Restore from Backup

```powershell
# List available backups
.\.claude\scripts\mcp-backup.ps1 -List

# Restore specific backup
.\.claude\scripts\mcp-backup.ps1 -Restore mcp-backup.20260104_120000.json
```

### Re-enable Disabled MCP

1. Open `.claude/mcp-backup.json`
2. Find the MCP entry in `disabled_mcps`
3. Copy the config (without `disabled_date` and `reason`)
4. Add to `~/.claude.json` under `mcpServers`
5. Restart Claude Code

**Example:**
```json
// From mcp-backup.json
"playwright": {
  "type": "stdio",
  "command": "npx",
  "args": ["-y", "@playwright/mcp@latest", "--browser", "msedge"],
  "env": {}
}

// Add to ~/.claude.json mcpServers section
```

## Backup File Format

```json
{
  "_comment": "Backup of disabled MCP servers - YYYY-MM-DD",
  "_reason": "Why these were disabled",
  "_restore": "Instructions for restoration",

  "disabled_mcps": {
    "server-name": {
      "type": "stdio",
      "command": "...",
      "args": [...],
      "env": {},
      "disabled_date": "YYYY-MM-DD",
      "reason": "Why this was disabled"
    }
  }
}
```

## Backup Directory

Backups are stored in `.claude/backups/mcp/`:
```
.claude/backups/mcp/
├── mcp-backup.20260104_100000.json
├── mcp-backup.20260104_110000.json
└── mcp-backup.20260104_120000.json
```

## Memory Optimization History

| Date | Event | RAM Impact |
|------|-------|------------|
| 2026-01-01 | 9 MCPs active | 93% RAM spike |
| 2026-01-01 | Disabled 5 MCPs | Stable ~60% |
| 2026-01-02 | Fixed playwright package | N/A |
| 2026-01-03 | Split governance into 4 servers | Improved modularity |
| 2026-01-09 | xubuntu migration | Removed PowerShell MCP |
| 2026-01-10 | Containerized MCP servers | TypeDB driver Python 3.12 |
| 2026-01-10 | Node.js via nvm, Playwright MCP enabled | Browser automation restored |
| 2026-01-14 | Renamed governance-* → gov-* | Shorter tool names |

## Related Documentation

- **Hooks**: [HOOKS.md](HOOKS.md) - Claude Code lifecycle hooks
- **Main Config**: [../CLAUDE.md](../CLAUDE.md) - Project rules and architecture
- **Deployment**: [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) - Docker setup

---

*Per R&D TOOL-009: MCP optimization for memory management*
