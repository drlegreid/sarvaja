# Sessions Management for Claude Code

> Sarvaja's flagship feature — full lifecycle tracking of Claude Code development sessions.

## Overview

Sessions Management transforms Claude Code's JSONL session files into first-class governance entities. Every development conversation is automatically discovered, ingested, linked to rules/tasks/decisions, and made searchable through the dashboard and MCP tools.

## How It Works

### 1. Auto-Discovery

On API startup, Sarvaja scans `~/.claude/projects/` for JSONL session files:

```
~/.claude/projects/
├── sarvaja-platform/    → 42 JSONL files discovered
└── buntu-ger/           → 3 JSONL files discovered
```

Each file is parsed for metadata: `session_uuid`, `project_slug`, `git_branch`, `tool_count`, `thinking_chars`, `compaction_count`.

Session IDs follow the pattern: `SESSION-{YYYY-MM-DD}-{PROJECT-SLUG}-{UUID}`

### 2. Streaming Ingestion

The ingestion pipeline processes arbitrarily large JSONL files with bounded memory:

| Metric | Value |
|--------|-------|
| Peak memory | ~60MB for 612MB files |
| Approach | Generator-based streaming (not buffered) |
| Recovery | Checkpoint/resume on failure |
| Default | `dry_run=True` (preview before commit) |

**MCP tools:**
- `ingest_session_content()` — Index JSONL → ChromaDB chunks
- `mine_session_links()` — Extract entity relations → TypeDB
- `ingest_session_full()` — Combined pipeline
- `ingestion_status()` — Check progress
- `ingestion_estimate()` — Pre-flight size/memory estimate

### 3. Transcript Viewing

Sessions are viewable as full conversation transcripts with a 4-tier fallback:

1. **JSONL** — Parse CC session file for the complete conversation
2. **In-Memory** — Synthetic transcript from `_sessions_store`
3. **Evidence** — Parse evidence `.md` file from `/evidence/`
4. **Empty** — Graceful empty state

The transcript UI renders color-coded cards per entry type:
- Blue — User messages
- Green — Assistant responses
- Orange — Tool calls with inputs/outputs
- Red — Errors

### 4. Zoom-Level Detail

Progressive disclosure reduces bandwidth and load time:

| Level | Content | Size |
|-------|---------|------|
| zoom=0 | Summary metadata | ~100 bytes |
| zoom=1 | + Tool breakdown + thinking summary | ~500 bytes |
| zoom=2 | + Individual tool calls (paginated) | Variable |
| zoom=3 | + Full thinking content (paginated) | Variable |

### 5. Entity Linking

Sessions connect to other governance entities via TypeDB relations:

```
                    ┌──────────┐
                    │  Rules   │
                    └────▲─────┘
                         │ session-applied-rule
┌──────────┐       ┌─────┴─────┐       ┌──────────┐
│  Tasks   │◂──────│  Session  │──────▸│ Evidence │
└──────────┘       └─────┬─────┘       └──────────┘
  completed-in           │ session-decision
                    ┌────▼─────┐
                    │Decisions │
                    └──────────┘
```

### 6. MCP Auto-Tracking

Non-chat MCP tool calls are automatically grouped into sessions via `MCPAutoSessionTracker`:

- Creates `SESSION-{date}-MCP-AUTO-{uuid}` sessions
- Records `tool_name` + `server` per call
- Auto-ends after 5 minutes of inactivity

## REST API

### Core CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List with pagination, sorting, filtering |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/{id}` | Get single session |
| PUT | `/api/sessions/{id}` | Update metadata |
| DELETE | `/api/sessions/{id}` | Soft delete |
| PUT | `/api/sessions/{id}/end` | End session, compute duration |

### Detail & Transcript

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/{id}/detail?zoom=0-3` | Lazy-loaded detail |
| GET | `/api/sessions/{id}/tools` | Paginated tool calls |
| GET | `/api/sessions/{id}/thoughts` | Paginated thinking blocks |
| GET | `/api/sessions/{id}/transcript` | Full conversation transcript |

### Relations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions/{id}/evidence` | Link evidence file |
| GET | `/api/sessions/{id}/tasks` | Tasks completed in session |
| GET | `/api/sessions/{id}/rules` | Rules applied in session |
| GET | `/api/sessions/{id}/decisions` | Decisions made in session |

### Filtering & Pagination

- **Status**: `?status=ACTIVE` or `?status=COMPLETED`
- **Agent**: `?agent_id=code-agent`
- **Date range**: `?start_date=2026-01-01&end_date=2026-03-20`
- **Search**: `?search=keyword` (max 500 chars)
- **Sort**: `?sort_by=started_at&order=desc`
- **Pagination**: `?offset=0&limit=50` (max 200)

## Dashboard Views

The sessions UI comprises 12 view modules:

| View | Purpose |
|------|---------|
| **List** | Filterable table with metrics row, timeline, and pivot table |
| **Detail** | Single session metadata and status |
| **Content** | Multi-tab navigation (transcript, tools, evidence) |
| **Transcript** | Color-coded conversation cards |
| **Tool Calls** | Paginated tool execution history |
| **Tasks** | Tasks completed during the session |
| **Evidence** | Evidence file links with previews |
| **Evidence Preview** | Markdown → HTML rendering |
| **Timeline** | Chronological event visualization |
| **Session Timeline** | Tool call sequencing view |
| **Form** | Create/edit session dialog |
| **Validation Card** | CVP heuristic check results |

## TypeDB Schema

### Session Entity
```tql
entity work-session:
  owns session-id @key
  owns session-name
  owns session-description
  owns session-file-path
  owns agent-id
  owns started-at       # datetime
  owns completed-at     # datetime
  plays completed-in:hosting-session
  plays has-evidence:evidence-session
  plays session-applied-rule:applying-session
  plays session-decision:deciding-session
```

### Claude Code Attributes
- `cc-session-uuid` — UUID from JSONL header
- `cc-project-slug` — Derived from project directory
- `cc-git-branch` — Active branch during session
- `cc-tool-count` — Number of tool calls
- `cc-thinking-chars` — Total thinking content size
- `cc-compaction-count` — Context compaction events

## Data Resilience

### Persistence Strategy
1. **TypeDB** — Primary store (source of truth)
2. **In-Memory** — Fast fallback (`_sessions_store` dict)
3. **Disk-Backed** — JSON files in `data/session_store/` survive restarts
4. **Sync** — `sync_pending_sessions()` retries memory-only → TypeDB

### Validation (CVP)
- **Tier 1**: Inline checks in `create_task()`, `update_task()` (<100ms)
- **Tier 2**: `_run_post_session_checks()` on session end
- **Tier 3**: `POST /api/tests/cvp/sweep` for pipeline-wide validation

Heuristic checks:
- **H-SESSION-002**: Detects backfilled sessions
- **H-SESSION-005**: Validates session completeness
- **H-SESSION-006**: Checks session-task linkage integrity

### Error Handling
- TypeDB unavailable → graceful fallback to in-memory
- JSONL missing/malformed → fallback schema detection
- Sanitized error messages (no stack traces to HTTP clients)
- Transient failure retry: `@retry_on_transient(max_attempts=2, base_delay=0.5)`

## Key Files

### Services
| File | Lines | Purpose |
|------|-------|---------|
| `governance/services/sessions.py` | 446 | Primary orchestrator |
| `governance/services/sessions_lifecycle.py` | 188 | Lifecycle operations |
| `governance/services/cc_session_ingestion.py` | 405 | CC JSONL ingestion |
| `governance/services/cc_session_scanner.py` | 455 | JSONL discovery & metadata |
| `governance/services/session_evidence.py` | 283 | Evidence compilation |
| `governance/services/session_repair.py` | 310 | Data integrity repairs |
| `governance/services/session_content_validator.py` | 362 | CVP Tier 2 validation |
| `governance/services/cc_transcript.py` | — | Transcript rendering |

### Routes
| File | Purpose |
|------|---------|
| `governance/routes/sessions/crud.py` | Core CRUD endpoints |
| `governance/routes/sessions/detail.py` | Lazy-loaded detail |
| `governance/routes/sessions/transcript.py` | Transcript endpoint |
| `governance/routes/sessions/relations.py` | Entity linkage |
| `governance/routes/sessions/validation.py` | Validation endpoint |

### MCP Tools
| File | Purpose |
|------|---------|
| `governance/mcp_tools/sessions_core.py` | start, end, decision, task |
| `governance/mcp_tools/sessions_linking.py` | Link rules, decisions, evidence |
| `governance/mcp_tools/sessions_intent.py` | Intent/outcome capture |
| `governance/mcp_tools/sessions_evidence.py` | Test evidence push/query |
| `governance/mcp_tools/auto_session.py` | Auto-tracking non-chat calls |

### UI Views
All in `agent/governance_ui/views/sessions/` — 12 modules totaling ~80KB.

### Scripts
| Script | Purpose |
|--------|---------|
| `scripts/ingest_mega_session.py` | CLI for mega-session ingestion |
| `scripts/backfill_claude_sessions.py` | Auto-ingest all CC projects |
| `scripts/repair_backfill_sessions.py` | Session repair CLI |
| `scripts/sync_task_session_relations.py` | Backfill completed-in relations |

## Governing Rules

| Rule | Purpose |
|------|---------|
| SESSION-EVID-01-v1 | Session evidence capture and linkage |
| SESSION-CC-01-v1 | Claude Code JSONL integration spec |
| TEST-CVP-01-v1 | Continuous validation pipeline |
| DATA-LAZY-01-v1 | Zoom-level lazy loading |
| DOC-SIZE-01-v1 | File modularization (max 300 lines) |
| GOV-MCP-FIRST-01-v1 | MCP as single source of truth |

---

*Part of [Sarvaja v1.0-GA](../releases/V1.0-GA.md)*
