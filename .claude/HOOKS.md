# Claude Code Hooks System

> **Version**: 1.0.0 | **Updated**: 2026-01-04 | **Per**: EPIC-006

## Overview

This project uses Claude Code hooks to maintain system health, track session entropy, and provide automated recovery. Hooks execute at specific lifecycle events and inject context into the conversation.

## Quick Reference

| Hook | Event | Purpose |
|------|-------|---------|
| `healthcheck.py` | SessionStart | Validates MCP dependencies (Docker, TypeDB, ChromaDB) |
| `entropy_monitor.py` | PostToolUse | Tracks tool calls, warns before context overflow |

## Architecture

```
.claude/
├── HOOKS.md              ← You are here (overview)
├── settings.local.json   ← Hook configuration
├── backups/              ← Settings backups (auto-created)
└── hooks/
    ├── README.md         ← Detailed documentation
    ├── healthcheck.py    ← SessionStart hook
    ├── entropy_monitor.py← PostToolUse hook
    ├── recover.py        ← Settings recovery script
    ├── recover.ps1       ← PowerShell wrapper
    ├── recover.sh        ← Bash wrapper
    ├── core/             ← Base classes, state, formatters
    ├── checkers/         ← Service, entropy, amnesia checkers
    ├── recovery/         ← Auto-recovery logic
    └── tests/            ← Level-based test suites
```

## Hook Configuration

Hooks are configured in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python .claude/hooks/healthcheck.py",
        "timeout": 3000
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/entropy_monitor.py",
            "timeout": 1000
          }
        ]
      }
    ]
  }
}
```

## Recovery

If hooks cause startup failures:

```powershell
# PowerShell
.\.claude\hooks\recover.ps1

# Bash
./.claude/hooks/recover.sh

# Python directly
python .claude/hooks/recover.py
```

### Recovery Options

| Option | Description |
|--------|-------------|
| (none) | Backup current + restore minimal |
| `--backup-only` | Only create timestamped backup |
| `--list` | Show available backups |
| `--restore FILE` | Restore from specific backup |

## Health States

| State | Meaning | Action |
|-------|---------|--------|
| `[HEALTH OK]` | All services running | None needed |
| `DOCKER: DOWN` | Docker Desktop not running | Start Docker Desktop |
| `typedb: DOWN` | TypeDB container stopped | `docker compose up -d typedb` |
| `chromadb: DOWN` | ChromaDB container stopped | `docker compose up -d chromadb` |
| `AMNESIA DETECTED` | Session context lost | Run `/remember` |
| `ENTROPY HIGH` | Many tool calls, context filling | Run `/save` |

## Audit Trail

Both hooks maintain a history array in their state files for debugging and session continuity:

| Hook | State File | Events Tracked |
|------|------------|----------------|
| healthcheck | `.healthcheck_state.json` | HASH_CHANGE, RECOVERY_ATTEMPT, RECOVERY_SUCCESS |
| entropy | `.entropy_state.json` | SESSION_START, WARNING_*, CHECKPOINT, SAVE_DETECTED, SESSION_RESET |

**Entropy checkpoints** are recorded every 10 tool calls for continuous audit trail.

History is capped at 50 entries (FIFO). See [hooks/README.md](hooks/README.md#audit-trail) for format details.

### Test Audit Trails

Test runs create Given/When/Then structured evidence:

```
evidence/tests/claude/YYYY-MM-DD_HHMMSS/
├── summary.json         # Run overview, success rate, duration
├── unit/               # Unit test results
├── integration/        # Integration test results
└── e2e/                # E2E test results
```

Each test record includes:
- **Business intent**: What the test verifies
- **GIVEN**: Preconditions and fixtures
- **WHEN**: Test action executed
- **THEN**: Outcome with duration

## Testing

```powershell
# All hook tests (legacy location)
python -m pytest tests/test_claude_hooks.py -v

# Level-based tests in hooks directory (recommended)
python -m pytest .claude/hooks/tests/test_level1_unit.py -v        # Fast, no deps
python -m pytest .claude/hooks/tests/test_level2_integration.py -v # Requires Docker
python -m pytest .claude/hooks/tests/test_level3_e2e.py -v         # Claude Code compat

# All hooks tests with audit trail
python -m pytest .claude/hooks/tests/ -v
# Audit trail: evidence/tests/claude/YYYY-MM-DD_HHMMSS/
```

### Claude Code CLI vs VS Code Extension

The E2E tests verify hooks work with Claude Code. Note the distinction:

| Component | Description | Test Impact |
|-----------|-------------|-------------|
| **VS Code Extension** | Integrated Claude experience in VS Code | Hooks work via extension |
| **Claude Code CLI** | Standalone terminal tool (`claude`) | Requires separate install |

**For full E2E testing**, install CLI separately:
```powershell
npm install -g @anthropic-ai/claude-code
claude --version  # Verify installation
```

Reference: [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup)

## Related Rules

- **RULE-021**: MCP healthcheck at session start
- **RULE-024**: AMNESIA recovery protocol
- **RULE-012**: Deep Sleep Protocol (entropy tracking)

---

**Detailed Documentation**: [hooks/README.md](hooks/README.md)
