# EPIC-ISSUE-EVIDENCE: Resolution Evidence Trail — Architecture Design

**Status**: RD (Research & Design)
**Created**: 2026-03-24
**Author**: EPIC-TASK-QUALITY-V3 Phase 17
**Session**: SESSION-2026-03-24-EPIC-TASK-QUALITY-V3-P17-RESOLUTION-EVIDENCE

---

## 1. Problem Statement

When examining a completed task, users cannot answer:
- What was the root cause?
- What approaches were tried and failed?
- What files were changed and why?
- What test evidence proves the fix works?

This information **exists** in linked sessions (thoughts, tool calls, decisions, test
results) but is scattered across multiple entities — never collated into the issue view.

## 2. Current State Analysis

### What Exists

| Data Source | Location | Access Pattern |
|-------------|----------|----------------|
| `resolution` enum | `task-resolution` TypeDB attr | NONE/DEFERRED/IMPLEMENTED/VALIDATED/CERTIFIED |
| `evidence` text | `task-evidence` TypeDB attr | Free-text, often "[Verification: L1/L2/L3]" |
| Session metadata | `GET /api/sessions/{id}` | Topic, agent, duration, status |
| Session tool calls | `GET /api/sessions/{id}/tools` | Tool names, counts, latency |
| Session thoughts | `GET /api/sessions/{id}/thoughts` | Thinking content (CC sessions) |
| Session transcript | `GET /api/sessions/{id}/transcript` | Full JSONL-based transcript |
| Evidence rendered | `GET /api/sessions/{id}/evidence/rendered` | Markdown -> HTML |
| Linked sessions | `task.linked_sessions` | Session IDs via `completed-in` relation |
| Linked commits | `task.linked_commits` | Commit SHAs via `task-commit` relation |
| Linked documents | `task.linked_documents` | File paths via `document-references-task` |
| Execution log | `GET /api/tasks/{id}/execution` | Lifecycle events (created, claimed, completed) |

### What's Missing

1. **`resolution_notes`** — A free-text field for structured resolution narrative
2. **Auto-collation** — Automatic assembly of resolution context from linked sessions
3. **Rich resolution UI** — Markdown-rendered resolution section in task detail
4. **Manual edit** — Ability to edit resolution notes via the task edit form

## 3. Data Model Extensions

### TypeDB Schema Change

```tql
# New attribute (P17 MVP)
attribute resolution-notes value string;

# Already defined on task entity via schema evolution
# task owns resolution-notes;
```

### Python Model Changes

```python
# governance/models/task.py
class TaskUpdate(BaseModel):
    resolution_notes: Optional[str] = None  # P17: resolution narrative

class TaskResponse(BaseModel):
    resolution_notes: Optional[str] = None  # P17: resolution narrative

# governance/typedb/entities.py
@dataclass
class Task:
    resolution_notes: Optional[str] = None  # P17
```

## 4. Collation Algorithm Design

### `_build_resolution_summary(task_id) -> str`

On DONE transition, if `resolution_notes` is empty, auto-generate from linked data:

```
## Resolution Summary

### Sessions
- SESSION-2026-03-24-TOPIC: "Session description" (45m, 23 tool calls)

### Files Changed
- governance/services/tasks_mutations.py
- agent/governance_ui/views/tasks/detail.py

### Linked Documents
- docs/backlog/specs/EPIC-ISSUE-EVIDENCE-RD.md
- evidence/SESSION-2026-03-24-TOPIC.md

### Commits
- abc1234: "Fix resolution notes persistence"

### Evidence
[Verification: L1] Unit tests pass (12/12)
```

**Data sources** (fetched from in-memory stores + TypeDB):
1. `linked_sessions` -> session metadata (description, duration via REST)
2. `linked_documents` -> file paths (already on task)
3. `linked_commits` -> commit SHAs (already on task)
4. `evidence` field -> existing evidence text

**Performance**: All data is already loaded by the DONE gate validation
(`_preload_task_from_typedb`), so no additional TypeDB queries needed.

## 5. UI Wireframe

### Resolution Section (task detail view)

```
+--------------------------------------------------+
| Resolution                              [Expand] |
+--------------------------------------------------+
| ## Resolution Summary                            |
|                                                  |
| ### Sessions                                     |
| - SESSION-2026-03-24-TOPIC (45m, 23 tools)      |
|                                                  |
| ### Files Changed                                |
| - governance/services/tasks_mutations.py         |
|                                                  |
| ### Evidence                                     |
| [Verification: L1] Unit tests pass               |
+--------------------------------------------------+
```

- Positioned below execution log, above bottom of card
- Only visible when `resolution_notes` is non-empty
- Markdown rendered via `<pre>` with `white-space: pre-wrap`
- Collapsible via `VExpansionPanels`

### Edit Form Addition

```
+--------------------------------------------------+
| Resolution Notes                                 |
| +----------------------------------------------+ |
| | ## Root Cause                                 | |
| | Race condition in on_view_change...           | |
| |                                               | |
| +----------------------------------------------+ |
+--------------------------------------------------+
```

- `VTextarea` with `auto_grow=True`, `rows=4`
- Pre-populated from `selected_task.resolution_notes`
- Only shown for tasks with status DONE/CLOSED/CANCELED

## 6. Phase Breakdown — Full EPIC

### Phase 17 (MVP) — This Phase
- `resolution_notes` field end-to-end (TypeDB -> API -> UI)
- Auto-populate on DONE transition
- Rich resolution section in task detail
- Resolution notes in edit form

### Phase 18 (Future) — Multi-Session Timeline Merge
- Chronological merge of tool calls across linked sessions
- "What happened" timeline view in task detail
- Session-aware evidence drill-down

### Phase 19 (Future) — Resolution Comments
- Comment thread on task (like GitHub issue comments)
- TypeDB `task-comment` entity with author, timestamp, body
- Real-time updates via WebSocket

### Phase 20 (Future) — Collaborative Editing
- Multi-agent resolution notes (each agent contributes)
- Conflict resolution for concurrent edits
- Version history for resolution_notes

### Phase 21 (Future) — AI-Assisted Resolution
- LLM summarization of session transcripts into resolution
- "Generate Resolution" button that analyzes linked sessions
- Quality scoring for resolution completeness

## 7. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage | TypeDB attribute | Consistent with evidence, body, summary |
| Format | Markdown string | Matches existing evidence/body patterns |
| Auto-generate | On DONE if empty | User can override; no data loss |
| UI position | Below execution log | Natural reading flow: lifecycle -> resolution |
| Edit access | Via edit form | Consistent with other editable fields |
| Rendering | Pre-wrap monospace | Matches tech docs section pattern |

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large resolution_notes | TypeDB string size limits | Cap at 10KB in validation |
| Session API unavailable | Empty auto-summary | Graceful fallback: just list IDs |
| Stale session data | Inaccurate summary | Re-fetch on DONE, not cached |

---

*This document scopes EPIC-ISSUE-EVIDENCE as the next body of work after EPIC-TASK-QUALITY-V3.*
