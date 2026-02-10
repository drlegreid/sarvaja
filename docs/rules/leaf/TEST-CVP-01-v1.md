# TEST-CVP-01-v1: Continuous Validation Pipeline

**Category:** `operational` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `validation`, `continuous`, `heuristic`, `automation`

---

## Directive

Validation MUST execute continuously across three tiers: (1) Tier 1 POST-OPERATION inline checks (<100ms, on CRUD), (2) Tier 2 POST-SESSION checks (on session_end, <5s), (3) Tier 3 SCHEDULED full sweeps (periodic, all domains). Each rule directive SHOULD map to at least one validation check. New rules without corresponding checks MUST be flagged as gaps.

---

## Implementation

### Tier 1: Post-Operation (Inline, <100ms)
- `governance/services/tasks.py:create_task()` — auto-links to active session (DATA-LINK-01-v1)
- `governance/services/tasks.py:update_task()` — auto-assigns agent_id for IN_PROGRESS
- Already active in production

### Tier 2: Post-Session (on session_end, <5s)
- `governance/routes/chat/session_bridge.py:_run_post_session_checks()` — validates agent_id, tool_calls, thoughts
- `governance/routes/chat/session_bridge.py:end_chat_session()` — generates evidence, syncs ChromaDB
- Per GAP-GOVSESS-CAPTURE-001: sessions now persist to TypeDB
- 6 pytest tests in `tests/unit/test_chat_session_bridge.py::TestPostSessionChecks`

### Tier 3: Scheduled (Periodic)
- `POST /tests/cvp/sweep` — CVP sweep endpoint, runs all heuristic checks via BackgroundTasks
- `GET /tests/cvp/status` — Pipeline health and recent run summary
- `POST /tests/heuristic/run` — 27 checks across 6 domains
- `POST /tests/regression/run` — Static → Heuristic → Dynamic pipeline
- 6 pytest tests in `tests/unit/test_heuristic_runner.py::TestCVPEndpoints`

### Dynamic Spec Derivation
- Rule directive patterns map to check types:
  - "MUST have X" → `field_not_null`
  - "MUST link to Y" → `relation_exists`
  - "MUST NOT exceed N" → `threshold_check`
- Static heuristic checks complement dynamic rule-derived checks

---

## Validation

- [x] Tier 1 checks execute on every CRUD operation (create_task, update_task)
- [x] Tier 2 checks execute on session_end (_run_post_session_checks)
- [x] Tier 3 heuristic sweep covers all 27 checks (POST /tests/cvp/sweep)
- [ ] Every ACTIVE rule has at least one corresponding validation check
- [x] Test results are persisted and linked to sessions (runner_store.py)

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Run all checks on every operation | Tier by latency budget (100ms/5s/periodic) |
| Validate only on human trigger | Automate via session lifecycle hooks |
| Keep test results in memory only | Persist to evidence files + TypeDB |
| Add rules without validation checks | Flag uncovered rules as gaps |
| Run heuristic checks synchronously in API | Use BackgroundTasks for async execution |

---

*Per TEST-COMP-02-v1: Comprehensive test coverage across all layers.*
