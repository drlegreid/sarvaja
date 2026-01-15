# R&D: Agent Platform Testing Strategy (ATEST-001 to ATEST-008)

**Status:** IN_PROGRESS
**Priority:** CRITICAL
**Vision:** Comprehensive test coverage for multi-agent governance platform
**Created:** 2026-01-15

---

## Overview

Systematic testing strategy for the Sarvaja agent platform, covering trust-based governance, task orchestration, handoff workflows, and recovery mechanisms.

**Related R&D:** RD-TESTING-STRATEGY, RD-LACMUS, RD-AGENT-ORCHESTRATION

---

## Current Test Inventory

| Category | Files | Tests | Coverage |
|----------|-------|-------|----------|
| Trust Scoring | test_agent_trust.py, test_trust_dashboard.py | ~40 | **HIGH** |
| Orchestrator | test_orchestrator.py | 32 | **HIGH** |
| Curator Agent | test_curator_agent.py | 22 | **HIGH** |
| Task Routing | test_lacmus.py | 5 | **MEDIUM** |
| Handoff | test_lacmus.py | 3 | **LOW** |
| Recovery | test_lacmus.py | 6 | **MEDIUM** |
| E2E Workflow | test_lacmus.py | 2 (skipped) | **NONE** |
| Kanren Integration | test_kanren_constraints.py | 45 | **HIGH** |

**Total:** ~170 tests across 9 files

---

## Gap Analysis

### High Priority Gaps

| Gap ID | Area | Description | Impact |
|--------|------|-------------|--------|
| ATEST-GAP-001 | E2E Workflow | No working E2E agent chain test | Cannot validate full workflow |
| ATEST-GAP-002 | Multi-Agent | No concurrent agent operation tests | Race conditions undetected |
| ATEST-GAP-003 | Delegation Chain | Limited handoff chain validation | Handoff failures undetected |
| ATEST-GAP-004 | Trust Evolution | No long-running trust change tests | Trust drift unvalidated |
| ATEST-GAP-005 | Performance | No load/stress tests for agents | Scalability unknown |

### Medium Priority Gaps

| Gap ID | Area | Description |
|--------|------|-------------|
| ATEST-GAP-006 | Kanren-Agent | KanrenRAGFilter not tested with agents |
| ATEST-GAP-007 | Error Recovery | Limited failure scenario tests |
| ATEST-GAP-008 | Agent Lifecycle | No agent startup/shutdown tests |

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| ATEST-001 | Design test pyramid for agent platform | 📋 TODO | **CRITICAL** | Unit/Integration/E2E distribution |
| ATEST-002 | Implement E2E agent workflow test | 📋 TODO | **CRITICAL** | RESEARCH → CODING → CURATOR chain |
| ATEST-003 | Create multi-agent concurrency tests | 📋 TODO | **HIGH** | Parallel task execution |
| ATEST-004 | Build delegation chain validator | 📋 TODO | **HIGH** | Handoff A→B→C tracking |
| ATEST-005 | Add trust evolution simulation | 📋 TODO | **HIGH** | Trust changes over time |
| ATEST-006 | Integrate Kanren with agent tests | 📋 TODO | **MEDIUM** | KanrenRAGFilter + AgentContext |
| ATEST-007 | Performance benchmark suite | 📋 TODO | **MEDIUM** | Task throughput, latency |
| ATEST-008 | Agent recovery scenario tests | 📋 TODO | **MEDIUM** | Crash, timeout, reconnect |

---

## Test Pyramid Design (ATEST-001)

```
                    ┌─────────────┐
                    │    E2E      │  5% - Full workflow chains
                    │   Tests     │  Target: 10 scenarios
                    ├─────────────┤
                    │ Integration │  25% - Agent interactions
                    │   Tests     │  Target: 50 tests
                    ├─────────────┤
                    │    Unit     │  70% - Individual components
                    │   Tests     │  Target: 200 tests
                    └─────────────┘
```

### Unit Tests (70%)

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| Trust Scoring | 40 | 50 | +10 |
| Orchestrator | 32 | 40 | +8 |
| Task Routing | 5 | 15 | +10 |
| Handoff Format | 3 | 10 | +7 |
| Kanren Constraints | 45 | 50 | +5 |

### Integration Tests (25%)

| Scenario | Current | Target |
|----------|---------|--------|
| Agent ↔ TypeDB | 10 | 20 |
| Agent ↔ ChromaDB | 5 | 10 |
| Orchestrator ↔ Agents | 12 | 25 |
| Handoff ↔ Evidence | 3 | 10 |

### E2E Tests (5%)

| Workflow | Status | Priority |
|----------|--------|----------|
| RESEARCH → CODING handoff | TODO | **CRITICAL** |
| CODING → CURATOR review | TODO | **HIGH** |
| Full chain with trust check | TODO | **HIGH** |
| AMNESIA recovery workflow | TODO | **HIGH** |
| Governance proposal flow | TODO | **MEDIUM** |

---

## E2E Agent Workflow Test (ATEST-002)

### Test Scenario: Gap Resolution Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   RESEARCH   │────▶│    CODING    │────▶│   CURATOR    │
│    Agent     │     │    Agent     │     │    Agent     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  Context Gather      Implementation      Review & Approve
  Files Examined       Code Changes       Trust Update
  Evidence Created    Tests Written       Gap Resolved
```

### Test Steps

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gap_resolution_workflow():
    """E2E: Gap flows through RESEARCH → CODING → CURATOR."""

    # 1. Create test gap
    gap_id = "GAP-TEST-E2E-001"
    await create_gap(gap_id, priority="HIGH", category="functionality")

    # 2. RESEARCH agent picks up gap
    research_agent = await spawn_agent("RESEARCH", trust_score=0.85)
    context = await research_agent.analyze_gap(gap_id)
    assert context.files_examined > 0
    assert context.evidence_gathered is not None

    # 3. RESEARCH creates handoff to CODING
    handoff = await research_agent.create_handoff(
        to_agent="CODING",
        context=context
    )
    assert handoff.status == "READY_FOR_CODING"

    # 4. CODING agent receives handoff
    coding_agent = await spawn_agent("CODING", trust_score=0.90)
    implementation = await coding_agent.process_handoff(handoff)
    assert implementation.files_modified > 0
    assert implementation.tests_added > 0

    # 5. CODING creates handoff to CURATOR
    review_handoff = await coding_agent.create_handoff(
        to_agent="CURATOR",
        implementation=implementation
    )
    assert review_handoff.status == "READY_FOR_REVIEW"

    # 6. CURATOR reviews and approves
    curator_agent = await spawn_agent("CURATOR", trust_score=0.95)
    approval = await curator_agent.review_implementation(review_handoff)
    assert approval.status == "APPROVED"

    # 7. Verify gap resolved
    gap = await get_gap(gap_id)
    assert gap.status == "RESOLVED"

    # 8. Verify trust updates
    assert research_agent.trust_score >= 0.85  # Maintained
    assert coding_agent.trust_score >= 0.90    # Maintained
```

---

## Multi-Agent Concurrency Tests (ATEST-003)

### Scenarios

| Test | Description | Assertions |
|------|-------------|------------|
| Parallel Task Claim | 3 agents claim same task | Only 1 succeeds |
| Queue Saturation | 100 tasks, 4 agents | All tasks processed |
| Priority Preemption | HIGH task during MEDIUM | HIGH processed first |
| Trust Threshold | Low-trust agent on CRITICAL | Task rejected |

### Implementation

```python
@pytest.mark.asyncio
async def test_parallel_task_claim():
    """Only one agent can claim a task."""
    task = await create_task("TASK-CONCURRENT-001", priority="HIGH")

    agents = [
        spawn_agent("CODING", trust_score=0.85),
        spawn_agent("CODING", trust_score=0.90),
        spawn_agent("CODING", trust_score=0.80),
    ]

    claims = await asyncio.gather(
        *[agent.claim_task(task.id) for agent in agents],
        return_exceptions=True
    )

    successful_claims = [c for c in claims if not isinstance(c, Exception)]
    assert len(successful_claims) == 1
```

---

## Trust Evolution Simulation (ATEST-005)

### Formula Verification

```
Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)
```

### Simulation Scenarios

| Scenario | Initial Trust | Actions | Expected Final |
|----------|---------------|---------|----------------|
| Perfect Compliance | 0.70 | 10 successful tasks | 0.85+ |
| Mixed Results | 0.80 | 5 success, 2 fail | 0.75-0.80 |
| Trust Decay | 0.90 | 3 failures | 0.75-0.85 |
| Recovery Path | 0.50 | 10 supervised success | 0.70+ |

---

## Kanren-Agent Integration (ATEST-006)

### Test: Agent Context Assembly with Kanren

```python
def test_kanren_validates_agent_context():
    """KanrenRAGFilter validates agent-task assignments."""
    from governance.kanren_constraints import KanrenRAGFilter, AgentContext, TaskContext

    rag_filter = KanrenRAGFilter()

    # Expert agent on CRITICAL task - should pass
    expert = AgentContext("AGENT-001", "Expert", 0.95, "claude-code")
    critical_task = TaskContext("GAP-CRITICAL-001", "CRITICAL", True)

    context = rag_filter.search_for_task(
        query_text="governance rules",
        task_context=critical_task,
        agent_context=expert
    )

    assert context["assignment_valid"] is True
    assert context["agent"]["trust_level"] == "expert"

    # Supervised agent on CRITICAL task - should fail
    supervised = AgentContext("AGENT-002", "Supervised", 0.55, "sync-agent")
    context = rag_filter.search_for_task(
        query_text="governance rules",
        task_context=critical_task,
        agent_context=supervised
    )

    assert context["assignment_valid"] is False
```

---

## Success Criteria

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Unit Test Count | 170 | 200 | +30 tests |
| Integration Tests | 30 | 65 | +35 tests |
| E2E Workflows | 0 | 10 | +10 scenarios |
| Test Coverage | ~75% | 85% | +10% |
| Lacmus Pass Rate | 100% | 100% | Maintain |

---

## Implementation Priority

1. **ATEST-002** (E2E workflow) - Validates full agent chain
2. **ATEST-003** (Concurrency) - Ensures safe parallel operation
3. **ATEST-004** (Delegation chain) - Validates handoff integrity
4. **ATEST-005** (Trust evolution) - Validates RULE-011 over time
5. **ATEST-006** (Kanren integration) - Validates constraint enforcement

---

*Per RULE-023: Test Coverage Protocol*
*Per RD-TESTING-STRATEGY: Spec-First TDD Methodology*
*Per RD-LACMUS: Agent Platform PoC Validation*
