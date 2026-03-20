# SESSION-EVENT-01-v1: Event-Driven Session Data Updates

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `session`, `event-driven`, `ingestion`, `watcher`, `scheduler`

---

## Directive

Session data MUST be updated via event-driven mechanisms (file watcher, webhook, or callback). Periodic scan is a FALLBACK only, not the primary update path. When a CC session JSONL file is modified, the watcher daemon MUST trigger ingestion within 5 seconds. The periodic scheduler (default 5 min) serves as a safety net for missed events, not as the primary data pipeline.

---

## Architecture

```
Primary (event-driven):
  JSONL file modified → Watchdog FileSystemEventHandler
    → 3s debounce → ingest_session()
    → Session entity created/updated in TypeDB
    → Dashboard auto-refreshes (UI-REFRESH-01-v1)

Fallback (periodic):
  IngestionScheduler (every 5 min)
    → Scans ~/.claude/projects/ for new/modified JSONL
    → Catches any files missed by watcher
    → Safety net, NOT primary path
```

### Component Responsibilities

| Component | Role | File |
|-----------|------|------|
| `ClaudeWatcher` | Primary — file change detection | `governance/services/claude_watcher.py` |
| `IngestionScheduler` | Fallback — periodic safety net | `governance/services/ingestion_scheduler.py` |
| `api_startup.py` | Starts both on API boot | `governance/api_startup.py` |

---

## Requirements

| Requirement | Value |
|-------------|-------|
| Watcher response time | ≤5 seconds from file change to ingestion start |
| Debounce interval | 3 seconds (prevents rapid-fire on active sessions) |
| Scheduler interval | Configurable, default 5 minutes |
| Scheduler role | Fallback ONLY — catches missed events |

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Rely solely on periodic scan for session updates | Use file watcher as primary, scheduler as fallback |
| Set scheduler interval <30 seconds | Watcher handles real-time; scheduler is safety net |
| Skip watcher because scheduler "catches everything" | Watcher provides <5s latency; scheduler has 5min gap |
| Run full re-scan on every watcher event | Debounce + incremental ingestion only |

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ingestion/scheduler` | GET | Current scheduler status + last run time |
| `/ingestion/scheduler` | PUT | Configure interval (30s-24h) |
| `/ingestion/scan` | POST | Manual trigger for immediate scan |

---

## Implementation Reference

- Watcher: P2-10a (2026-03-19), `governance/services/claude_watcher.py`
- Scheduler: P2-10 (2026-03-19), `governance/services/ingestion_scheduler.py`
- Both started in `governance/api_startup.py`

---

*Per DATA-INGEST-01-v1: Data Ingestion Pipeline*
*Per UI-REFRESH-01-v1: Smart Dashboard Auto-Refresh*
