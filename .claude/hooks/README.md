# Claude Code Hooks - Detailed Documentation

> **Version**: 1.0.0 | **Updated**: 2026-01-04 | **Per**: EPIC-006
> **Parent Doc**: [../.claude/HOOKS.md](../HOOKS.md)

## Directory Structure

```
hooks/
├── README.md               ← You are here
├── healthcheck.py          ← SessionStart hook (main entry)
├── entropy_monitor.py      ← PostToolUse hook (main entry)
├── recover.py              ← Settings recovery script
├── recover.ps1             ← PowerShell wrapper
├── recover.sh              ← Bash wrapper
│
├── core/                   ← Base classes and utilities
│   ├── __init__.py         ← Exports: HookConfig, HookResult, OutputFormatter, StateManager
│   ├── base.py             ← HookConfig, HookResult dataclasses
│   ├── state.py            ← StateManager, hash functions
│   └── formatters.py       ← OutputFormatter for Claude Code JSON
│
├── checkers/               ← Health check implementations
│   ├── __init__.py         ← Exports: ServiceChecker, EntropyChecker, AmnesiaDetector
│   ├── services.py         ← Docker, TypeDB, ChromaDB checks
│   ├── entropy.py          ← Tool call tracking, context warnings
│   └── amnesia.py          ← Session continuity detection
│
├── recovery/               ← Auto-recovery logic
│   ├── __init__.py         ← Exports: DockerRecovery
│   └── docker.py           ← Docker Desktop and container recovery
│
└── tests/                  ← Level-based test suites
    ├── __init__.py
    ├── test_level1_unit.py      ← 17 tests: Fast, no external deps
    ├── test_level2_integration.py ← 7 tests: Requires Docker running
    └── test_level3_e2e.py       ← 9 tests: Claude Code compatibility
```

## Module Reference

### core/base.py - Configuration and Results

```python
from hooks.core import HookConfig, HookResult

# Configuration with defaults
config = HookConfig(
    global_timeout=3.0,        # Overall hook timeout
    subprocess_timeout=1.0,    # Docker command timeout
    socket_timeout=0.5,        # Port check timeout
    retry_ceiling_seconds=30,  # Stop retrying after 30s unchanged
    recovery_cooldown=60,      # Wait before auto-recovery
    core_services=["docker", "typedb", "chromadb"]
)

# Creating results
result = HookResult.ok("All services running", docker="UP", typedb="UP")
result = HookResult.error("Docker down", resolution_path="Start Docker Desktop")
result = HookResult.warning("High entropy", resolution_path="Run /save")
```

### core/state.py - State Management

```python
from hooks.core import StateManager, compute_frankel_hash, compute_session_hash

# Frankel hash (8-char SHA256) - tracks service state changes
hash = compute_frankel_hash({"docker": "UP", "typedb": "UP"})  # "A1B2C3D4"

# Session hash (4-char MD5) - tracks session identity
hash = compute_session_hash("2026-01-04T10:00:00", 42)  # "F1E2"

# State persistence
manager = StateManager(Path(".healthcheck_state.json"))
state = manager.load()
manager.save(state, add_history=True, history_entry={"event": "CHECK", "hash": "A1B2"})
```

### core/formatters.py - Claude Code Output

```python
from hooks.core import OutputFormatter

# Format for Claude Code injection
json_output = OutputFormatter.to_json(
    context="[HEALTH OK] Hash: A1B2C3D4 | MCP chain ready.",
    hook_event="SessionStart"
)
# {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}
```

### checkers/services.py - Service Health

```python
from hooks.checkers import ServiceChecker

checker = ServiceChecker()
services = checker.check_all()
# {"docker": {"ok": True, "status": "UP"}, "typedb": {"ok": True, ...}, ...}

result = checker.check_core()
# HookResult with overall status
```

### checkers/entropy.py - Context Tracking

```python
from hooks.checkers import EntropyChecker

checker = EntropyChecker()

# Check current entropy level
result = checker.check()

# Increment tool count and check
result = checker.increment_and_check()

# Thresholds:
# - LOW_THRESHOLD = 50 (first warning)
# - HIGH_THRESHOLD = 100 (urgent warning)
# - TIME_THRESHOLD = 60 (minutes before warning)
```

### checkers/amnesia.py - Continuity Detection

```python
from hooks.checkers import AmnesiaDetector

detector = AmnesiaDetector()
result = detector.check(previous_state, current_services)

# Detects:
# - Missing previous state (new session after crash)
# - Large hash changes (service restarts)
# - Missing expected context
```

### recovery/docker.py - Auto-Recovery

```python
from hooks.recovery import DockerRecovery

recovery = DockerRecovery()

# Get resolution path for failures
path = recovery.get_resolution_path(services)
# "Start Docker Desktop" or "docker compose --profile cpu up -d typedb chromadb"

# Attempt automatic recovery
result = recovery.attempt_recovery(services, previous_state)
```

## Hook Entry Points

### healthcheck.py

**Event**: `SessionStart`
**Timeout**: 3000ms
**Purpose**: Validate MCP dependencies before session

```
Output Format:
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "[HEALTH OK] Hash: A1B2C3D4 | MCP chain ready."
  }
}
```

**States**:
| Hash Change | Time Since | Output |
|-------------|------------|--------|
| Yes | Any | Detailed status of all services |
| No | <30s | Detailed status (still checking) |
| No | >30s | Summary only (stable) |

### entropy_monitor.py

**Event**: `PostToolUse`
**Timeout**: 1000ms
**Purpose**: Track tool calls, warn before context overflow

```
Output Format (when warning):
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "[ENTROPY HIGH] 120 tool calls. Run /save to preserve context."
  }
}

Output Format (silent):
{}
```

**Warning Triggers**:
- 50+ tool calls (first warning)
- Every 20 calls after first warning
- 100+ tool calls (urgent)

## State Files

### .healthcheck_state.json

```json
{
  "master_hash": "A1B2C3D4",
  "last_check": "2026-01-04T10:00:00",
  "check_count": 5,
  "unchanged_since": 1704362400.0,
  "components": {
    "docker": "UP",
    "typedb": "UP",
    "chromadb": "UP"
  },
  "history": [
    {"timestamp": "...", "event": "HASH_CHANGE", "old": "...", "new": "..."}
  ]
}
```

### .entropy_state.json

```json
{
  "session_start": "2026-01-04T10:00:00",
  "session_hash": "F1E2",
  "tool_count": 42,
  "check_count": 42,
  "warnings_shown": 1,
  "last_warning_at": 50,
  "last_save": "2026-01-04T10:30:00",
  "history": [
    {"timestamp": "...", "event": "WARNING", "tool_count": 50}
  ]
}
```

## Audit Trail

Both hooks maintain a `history` array in their state files for debugging, forensics, and session continuity detection. History entries are appended on significant events and capped at 10 entries (oldest removed first via FIFO).

### Healthcheck Audit Events

| Event | Trigger | Data Captured |
|-------|---------|---------------|
| `HASH_CHANGE` | Service state changed | `old` hash, `new` hash, `components` diff |
| `RECOVERY_ATTEMPT` | Auto-recovery started | `services` targeted, `reason` |
| `RECOVERY_SUCCESS` | Recovery completed | New `hash`, `services` restored |
| `RECOVERY_FAILED` | Recovery failed | `error` message, `services` still down |
| `AMNESIA_DETECTED` | Session continuity lost | Previous `hash`, detection `confidence` |

**Example healthcheck history:**
```json
{
  "history": [
    {
      "timestamp": "2026-01-04T10:00:00",
      "event": "HASH_CHANGE",
      "old": "A1B2C3D4",
      "new": "E5F6G7H8",
      "components": {"typedb": "DOWN"}
    },
    {
      "timestamp": "2026-01-04T10:00:05",
      "event": "RECOVERY_ATTEMPT",
      "services": ["typedb"],
      "reason": "container_down"
    },
    {
      "timestamp": "2026-01-04T10:00:30",
      "event": "RECOVERY_SUCCESS",
      "hash": "A1B2C3D4",
      "services": ["typedb"]
    }
  ]
}
```

### Entropy Audit Events

| Event | Trigger | Data Captured |
|-------|---------|---------------|
| `SESSION_START` | New session detected | `session_hash`, initial `tool_count` |
| `SESSION_RESET` | Manual or auto reset | `reason` (save/manual/timeout), previous `tool_count` |
| `WARNING` | Threshold crossed | `tool_count`, `level` (LOW/HIGH), `warnings_shown` |
| `SAVE_DETECTED` | `/save` command run | `tool_count` at save, `session_hash` |

**Example entropy history:**
```json
{
  "history": [
    {
      "timestamp": "2026-01-04T10:00:00",
      "event": "SESSION_START",
      "session_hash": "F1E2",
      "tool_count": 0
    },
    {
      "timestamp": "2026-01-04T10:30:00",
      "event": "WARNING",
      "tool_count": 50,
      "level": "LOW",
      "warnings_shown": 1
    },
    {
      "timestamp": "2026-01-04T11:00:00",
      "event": "WARNING",
      "tool_count": 100,
      "level": "HIGH",
      "warnings_shown": 2
    },
    {
      "timestamp": "2026-01-04T11:05:00",
      "event": "SAVE_DETECTED",
      "tool_count": 105,
      "session_hash": "F1E2"
    },
    {
      "timestamp": "2026-01-04T11:05:00",
      "event": "SESSION_RESET",
      "reason": "save",
      "previous_tool_count": 105
    }
  ]
}
```

### Using Audit Trail for Debugging

```powershell
# View recent healthcheck events
Get-Content .claude/hooks/.healthcheck_state.json | ConvertFrom-Json | Select-Object -ExpandProperty history

# View recent entropy events
Get-Content .claude/hooks/.entropy_state.json | ConvertFrom-Json | Select-Object -ExpandProperty history

# Check for AMNESIA indicators
Get-Content .claude/hooks/.healthcheck_state.json | ConvertFrom-Json |
  Select-Object -ExpandProperty history |
  Where-Object { $_.event -eq "AMNESIA_DETECTED" }
```

## Recovery Script

### Usage

```powershell
# PowerShell
.\.claude\hooks\recover.ps1                    # Backup + restore minimal
.\.claude\hooks\recover.ps1 -BackupOnly        # Only backup
.\.claude\hooks\recover.ps1 -List              # List backups
.\.claude\hooks\recover.ps1 -Restore <file>    # Restore specific

# Bash
./.claude/hooks/recover.sh                     # Backup + restore minimal
./.claude/hooks/recover.sh --backup-only       # Only backup
./.claude/hooks/recover.sh --list              # List backups
./.claude/hooks/recover.sh --restore <file>    # Restore specific

# Python
python .claude/hooks/recover.py [options]
```

### Backup Location

Backups are stored in `.claude/backups/` with timestamp suffix:
```
.claude/backups/
├── settings.local.json.20260104_100000.bak
├── settings.local.json.20260104_110000.bak
└── settings.local.json.20260104_120000.bak
```

### Minimal Settings

Recovery restores to minimal safe configuration:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "python .claude/hooks/healthcheck.py",
        "timeout": 3000
      }
    ]
  }
}
```

## Testing

### Test Levels

| Level | File | Count | Requirements | Speed |
|-------|------|-------|--------------|-------|
| 1 | `level1_unit.py` | 17 | None | Fast (<5s) |
| 2 | `level2_integration.py` | 7 | Docker running | Medium (~15s) |
| 3 | `level3_e2e.py` | 9 | Docker + Claude Code | Slow (~30s) |

### Running Tests

```powershell
# All levels
python -m pytest .claude/hooks/tests/ -v

# Specific level
python -m pytest .claude/hooks/tests/level1_unit.py -v

# With coverage
python -m pytest .claude/hooks/tests/ -v --cov=.claude/hooks

# Main test file (includes additional tests)
python -m pytest tests/test_claude_hooks.py -v
```

### Test Categories

- **Unit Tests**: Hash functions, state management, formatters
- **Integration Tests**: Docker detection, container status, state persistence
- **E2E Tests**: Claude Code JSON format, concurrent execution, CLI compatibility
- **Negative Tests**: Service down scenarios, resolution path injection

## Troubleshooting

### Hook Not Running

1. Check settings.local.json exists and is valid JSON
2. Verify hook file exists at specified path
3. Check Python is in PATH
4. Run hook manually: `python .claude/hooks/healthcheck.py`

### Hook Causes Startup Failure

```powershell
# Quick recovery
.\.claude\hooks\recover.ps1

# Manual recovery
Rename-Item .claude/settings.local.json settings.local.json.bak
# Create minimal: { "hooks": {} }
```

### State File Corrupted

```powershell
# Delete state files (will regenerate)
Remove-Item .claude/hooks/.healthcheck_state.json
Remove-Item .claude/hooks/.entropy_state.json
```

### Docker Detection Fails

1. Verify Docker Desktop is running
2. Check Docker CLI works: `docker info`
3. Check containers: `docker ps`
4. Manual start: `docker compose --profile cpu up -d`

## Related Documentation

- **Parent**: [HOOKS.md](../HOOKS.md) - Overview and quick reference
- **Rules**: [RULES-OPERATIONAL.md](../../docs/rules/RULES-OPERATIONAL.md) - RULE-021, RULE-024
- **Deployment**: [DEPLOYMENT.md](../../docs/DEPLOYMENT.md) - Docker setup
- **Workflows**: [workflows.md](../../.windsurf/workflows.md) - Session protocols

---

*Per EPIC-006: Sleep Mode Automation - Hooks for health monitoring and recovery*
