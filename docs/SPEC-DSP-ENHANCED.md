# SPEC: Enhanced DSP Protocol

**Status:** DRAFT (GitHub integration ON HOLD) | **Date:** 2024-12-24 | **Rule:** RULE-012 Enhancement

---

## Overview

Enhanced Deep Sleep Protocol with comprehensive MCP integration, TypeDB memory linking, test evidence collection, and GitHub workflow integration.

---

## DSP Phases (Enhanced)

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
```

| Phase | Purpose | MCPs Used |
|-------|---------|-----------|
| **AUDIT** | Inventory gaps, orphans, loops | claude-mem, TypeDB |
| **HYPOTHESIZE** | Form improvement theories | sequential-thinking |
| **MEASURE** | Quantify current state | powershell, llm-sandbox |
| **OPTIMIZE** | Apply improvements | filesystem, git |
| **VALIDATE** | Run tests, verify no regression | pytest, llm-sandbox |
| **DREAM** | Explore product, discover issues | playwright, docker |
| **REPORT** | ~~Link to GitHub~~ ON HOLD | git ~~, octocode~~ |

---

## 1. TypeDB Memory MCP Checks

### Health Check Protocol

```yaml
typedb_health:
  connection: Check TypeDB port 1729 reachable
  schema: Verify schema loaded (15 rules, 3 agents, 4 decisions)
  inference: Test 1 inference rule works
  sync: Compare TypeDB entity count vs expected
```

### Orphan Detection

```typeql
# Find orphan rules (no dependencies, not depended on)
match
  $r isa rule-entity, has rule-id $id;
  not { (dependent: $r, dependency: $_) isa rule-dependency; };
  not { (dependent: $_, dependency: $r) isa rule-dependency; };
get $id;

# Find orphan gaps (no rule reference)
match
  $g isa gap, has gap-id $gid;
  not { ($g, $_) isa gap-rule-reference; };
get $gid;
```

### Loop Detection

```typeql
# Detect circular dependencies (A→B→C→A)
match
  $r1 isa rule-entity;
  (dependent: $r1, dependency: $r2) isa rule-dependency;
  (dependent: $r2, dependency: $r3) isa rule-dependency;
  (dependent: $r3, dependency: $r1) isa rule-dependency;
get $r1, $r2, $r3;
```

### Index Quality Evaluation

```yaml
index_quality:
  completeness: All rules have category, priority, status
  consistency: No duplicate rule-ids
  freshness: No items > 30 days without update
  traceability: All gaps reference a rule (RULE-013)
```

---

## 2. Memory Deduplication

### Repetitive Memory Check

```python
# Query recent memories
recent = chroma_query_documents(
    collection_name="claude_memories",
    query_texts=["sim-ai recent session"],
    n_results=10
)

# Check semantic similarity
for i, doc in enumerate(recent):
    for j, other in enumerate(recent[i+1:]):
        similarity = calculate_similarity(doc, other)
        if similarity > 0.85:
            flag_as_duplicate(doc, other)
```

### Custom MCP Augmentation

```yaml
memory_augmentation:
  - deduplicate: Merge similar memories
  - enrich: Add missing metadata
  - cross_link: Link to TypeDB entities
  - archive: Move old memories to cold storage
```

---

## 3. Product Exploration (DREAM Phase)

### Playwright MCP Integration

```yaml
dream_exploration:
  endpoints:
    - http://localhost:7777/health  # Agents
    - http://localhost:4000/health  # LiteLLM
    - http://localhost:8001/api/v2/heartbeat  # ChromaDB

  heuristics:
    - BOUNDARY: Test empty states, limits
    - NAVIGATION: Verify all routes
    - ERROR: Trigger error handlers
    - STATE: Check persistence
```

### Docker MCP Integration

```yaml
container_inspection:
  commands:
    - docker ps --format "table {{.Names}}\t{{.Status}}"
    - docker logs sim-ai-typedb-1 --tail 50
    - docker stats --no-stream

  health_checks:
    - Container running: 4 containers expected
    - Memory usage: < 2GB per container
    - Restart count: 0 expected
```

### PowerShell MCP Integration

```powershell
# System health
Get-Process node | Measure-Object | Select Count
Get-Process python | Measure-Object | Select Count

# Memory check
(Get-Process -Id $PID).WorkingSet64 / 1MB

# Service verification
Test-NetConnection localhost -Port 1729  # TypeDB
Test-NetConnection localhost -Port 8001  # ChromaDB
```

### Python MCP (llm-sandbox)

```python
# Isolated test execution
import pytest
result = pytest.main([
    "tests/",
    "--tb=short",
    "-v",
    "--json-report"
])
```

---

## 4. GitHub Integration

### Session → Issue Linking

```yaml
github_workflow:
  session_start:
    - Create or find existing issue for task
    - Add session ID to issue body
    - Label: in-progress

  session_end:
    - Add commit SHAs to issue
    - Add test results summary
    - If tests pass: close issue
    - If tests fail: label: blocked
```

### Issue Template

```markdown
## Session Link

**Session ID:** DSP-2024-12-24-HYGIENE
**Type:** DSP
**Commits:** cbb3198, 0ceeaf6

## Evidence

- [x] Session log: docs/SESSION-2024-12-24-DSP-HYGIENE.md
- [x] Tests: 5 passed, 10 skipped
- [x] No regressions

## Auto-Close

Closes on: All tests pass + manual review (if R&D)
```

---

## 5. Test Evidence Collection

### BDD Substep Trace Mode

```yaml
test_modes:
  ci_mode:
    output: minimal
    on_pass: status only
    on_fail: full trace

  trace_mode:
    output: full
    prestep: capture state before
    action: capture action taken
    poststep: capture state after
    substep: technical details (logs, API calls)
```

### Chunked Test Categories

```yaml
test_chunks:
  unit:
    pattern: "tests/test_*.py::Test*Unit*"
    timeout: 30s
    priority: P0

  integration:
    pattern: "tests/test_*.py::Test*Integration*"
    timeout: 120s
    priority: P1

  bdd:
    pattern: "tests/test_*.py::Test*BDD*"
    timeout: 60s
    priority: P1

  stubs:
    pattern: "tests/test_*.py::Test*Stubs*"
    skip: true
    reason: TDD deferred to Phase 2.6
```

### Failure Cluster Detection

```python
# Group failures by file/class
def detect_failure_clusters(results):
    clusters = {}
    for test in results.failed:
        file = test.nodeid.split("::")[0]
        cls = test.nodeid.split("::")[1] if "::" in test.nodeid else "root"
        key = f"{file}::{cls}"
        clusters.setdefault(key, []).append(test)
    return clusters
```

---

## 6. R&D Workflow (Human Approval Gate)

### Autonomy Levels

| Level | Trigger | Actions | Approval |
|-------|---------|---------|----------|
| **ROUTINE** | Default | Execute task queue | None |
| **STRATEGIC** | P1 milestone | Execute with logging | Post-hoc review |
| **R&D** | Research needed | Propose + wait | **Human required** |
| **DEEP** | Explicit mandate | Full autonomy | Pre-approved |

### R&D Gate Protocol

```yaml
rd_workflow:
  trigger:
    - New technology evaluation
    - Architecture change
    - Budget-impacting decision
    - External dependency addition

  steps:
    1. Create R&D proposal document
    2. Link to relevant rules (RULE-008)
    3. Estimate effort/risk
    4. PAUSE for human review
    5. On approval: proceed
    6. On reject: archive proposal

  deep_autonomy:
    trigger: "DEEP" keyword in task
    scope: Time-boxed (e.g., 2 hours)
    reporting: Full evidence on completion
```

### Budget Consideration

```yaml
budget_flags:
  low: < 2 hours effort, no external cost
  medium: 2-8 hours, potential API costs
  high: > 8 hours, infrastructure changes
  critical: Requires procurement/subscription
```

---

## 7. Governance System Update

### New Inference Rules (TypeDB)

```typeql
# Rule: DSP session requires MCP audit
rule dsp-requires-mcp-audit:
when {
  $s isa session, has session-type "DSP";
  not { (session: $s, mcp: $_) isa mcp-usage; };
} then {
  (flagged: $s) isa audit-flag, has flag-type "missing-mcp-usage";
};

# Rule: R&D requires human approval
rule rd-requires-approval:
when {
  $t isa task, has task-type "R&D";
  not { (task: $t, approver: $_) isa human-approval; };
} then {
  (blocked: $t) isa approval-gate, has gate-type "rd-human-review";
};
```

### Session Entity (TypeDB)

```typeql
session sub entity,
    owns session-id,
    owns session-type,  # DSP, ROUTINE, STRATEGIC, R&D
    owns session-date,
    owns github-issue,
    owns commit-shas,
    owns test-results,
    plays session-evidence:logged-session,
    plays mcp-usage:session;

mcp-usage sub relation,
    relates session,
    relates mcp,
    owns invocation-count;
```

---

## Implementation Priority

| Item | Priority | Effort | Dependency |
|------|----------|--------|------------|
| Session log template | P0 | 1h | None |
| TypeDB health checks | P1 | 2h | TypeDB running |
| Memory deduplication | P2 | 4h | claude-mem analysis |
| Playwright DREAM | P2 | 4h | Playwright MCP |
| GitHub issue linking | P1 | 2h | octocode MCP |
| BDD trace mode | P2 | 4h | pytest config |
| R&D approval gate | P1 | 2h | Governance MCP |

---

*Spec-driven per RULE-008: In-House Rewrite Principle*
