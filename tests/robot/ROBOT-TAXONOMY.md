# Robot Framework Test Taxonomy

**Version:** 1.1 | **Created:** 2026-01-21 | **Updated:** 2026-01-27 | **Status:** ACTIVE

Per RF-003: Define tagging taxonomy for Robot Framework tests.

---

## Tag Categories

### 1. Scope Tags (Required - exactly one)

| Tag | Description | Execution Time |
|-----|-------------|----------------|
| `unit` | Single component/function tests | <1s each |
| `component` | Module-level integration | 1-5s each |
| `integration` | Multi-module interaction | 5-30s each |
| `e2e` | Full system validation | 30s+ each |

### 2. Domain Tags (Required - at least one)

| Tag | Description | API Prefix |
|-----|-------------|------------|
| `rules` | Governance rules | /api/rules |
| `tasks` | Task management | /api/tasks |
| `sessions` | Session tracking | /api/sessions |
| `agents` | Agent orchestration | /api/agents |
| `decisions` | Decision records | /api/decisions |
| `evidence` | Evidence files | /api/evidence |
| `health` | Health/status | /api/health |

### 3. Priority Tags (Required - exactly one)

| Tag | Description | CI Inclusion |
|-----|-------------|--------------|
| `critical` | Must pass before merge | Always |
| `high` | Important validation | Daily |
| `medium` | Standard validation | Nightly |
| `low` | Nice-to-have checks | Weekly |

### 4. CI Tags (Optional)

| Tag | Description | When Run |
|-----|-------------|----------|
| `smoke` | Quick sanity check | Every commit |
| `regression` | Full regression suite | Pre-merge |
| `nightly` | Extended validation | Nightly builds |
| `flaky` | Known unstable tests | Manual only |

### 5. GAP Reference Tags (Optional)

Format: `GAP-{ID}` - Link test to gap regression

Examples:
- `GAP-UI-SESSION-TASKS-001` - Session tasks display gap
- `GAP-UI-AUDIT-001` - UI audit gap
- `GAP-TEST-EVIDENCE-001` - Test evidence gap

Run all GAP regression tests: `robot --include GAP-* tests/robot/`
Current coverage: 60 tests tagged across 11 files.

### 6. Rule Reference Tags (Optional)

Format: `{SEMANTIC-ID}` - Link test to governance rule

Examples:
- `TASK-VALID-01-v1` - Task completion validation
- `SESSION-EVID-01-v1` - Session evidence rule
- `TEST-FIX-01-v1` - Fix validation rule

---

## Tag Combinations

### Minimum Required Tags
```
unit/component/integration/e2e + domain + critical/high/medium/low
```

### Example Tag Sets

| Test Type | Tags |
|-----------|------|
| API unit test | `unit`, `rules`, `high` |
| E2E session test | `e2e`, `sessions`, `critical`, `regression` |
| Rule validation | `integration`, `rules`, `high`, `RULE-001` |
| Smoke test | `e2e`, `health`, `critical`, `smoke` |

---

## Execution Commands

```bash
# Run critical tests only
robot --include critical tests/robot/

# Run e2e + rules tests
robot --include e2e --include rules tests/robot/

# Run smoke tests
robot --include smoke tests/robot/

# Exclude flaky tests
robot --exclude flaky tests/robot/

# Run tests for specific rule
robot --include TASK-VALID-01-v1 tests/robot/

# Run all GAP regression tests
robot --include GAP-* tests/robot/

# Run tests by domain
robot --include sessions tests/robot/
robot --include rules tests/robot/

# Run with parallel execution (requires pabot)
pabot --processes 4 tests/robot/
```

---

## Mapping to pytest markers

| pytest marker | Robot tag |
|---------------|-----------|
| `@pytest.mark.rules(...)` | `rules`, rule IDs |
| `@pytest.mark.gaps(...)` | gap IDs as tags |
| `@pytest.mark.intent(...)` | In Documentation |
| `@pytest.mark.slow` | `nightly` |
| `@pytest.mark.e2e` | `e2e` |

---

## Compliance Status (2026-01-28)

**Total:** 139 robot files, 2308 tests

### Required Dimensions (100% compliance)

| Dimension | Coverage | Notes |
|-----------|----------|-------|
| 1. Scope | 139/139 (100%) | unit, integration, e2e, component, benchmark |
| 2. Domain | 139/139 (100%) | rules, agents, sessions, tasks, mcp, ui, dsm, etc. |
| 3. Priority | 139/139 (100%) | critical:92, high:517, medium:683, low:1023 |

### Optional Dimensions

| Dimension | Coverage | Notes |
|-----------|----------|-------|
| 4. Entity | 88/139 (63%) | rule, agent, session, task, trust, decision, gap, commit, evidence-file |
| 5. Action | 139/139 (100%) | validate, read, create, delete, sync, link, monitor, search, trace |
| 6. Rule refs | 137/139 (99%) | 42 unique governance rules across all domains |
| 7. GAP refs | 17/139 (12%) | 52 unique GAP IDs, queryable via `--include GAP-*` |

### Queryable Examples

```bash
# By action
robot --include validate tests/robot/     # Validation tests
robot --include "create AND rules" tests/  # Rule creation tests

# By entity
robot --include session tests/robot/      # All session-related tests
robot --include "task AND link" tests/     # Task linking tests

# By rule
robot --include SESSION-EVID-01-v1 tests/  # Session evidence rule tests
robot --include ARCH-MCP-02-v1 tests/      # MCP architecture tests
```

*Per TEST-TAXON-01-v1: Full taxonomy compliance achieved*
