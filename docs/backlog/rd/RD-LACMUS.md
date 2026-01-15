# RD-LACMUS: Agent Benchmark Microproject

**Status:** IN_PROGRESS | **Priority:** LOW | **Complexity:** LOW
**Created:** 2026-01-14 | **Updated:** 2026-01-15 | **Type:** R&D

## Current Status (2026-01-15)

**Test Results:** 23 passed, 5 skipped (2 E2E, 3 TypeDB connectivity)
**Scaffold:** `tests/benchmarks/test_lacmus.py` complete

**All Phases Working:**
- Phase 1: Unit Validation (Trust, Routing, Handoff format) ✓
- Phase 2: Integration (Activity tracking, Trust evolution, Handoff chain) ✓
- Phase 3: Recovery (AMNESIA simulation, Context restore) ✓
- Phase 4: E2E Workflow - skipped (requires multi-workspace setup)

**Key Fixes Applied:**
- Added local helper functions to wrap MCP tools for testability
- Fixed HookResult.details access pattern for AMNESIA indicators
- Corrected task routing expectations (P12+ → CURATOR)
- Added graceful skips for TypeDB connectivity tests

---

## Purpose

"Lacmus" (litmus) test for agent performance - a minimal benchmark suite to validate multi-agent governance capabilities.

---

## PoC Checklist

### Phase 1: Infrastructure
- [x] Define benchmark scenarios (5 min each)
- [x] Create isolated test environment (`tests/benchmarks/`)
- [x] Set up metrics collection (pytest markers)

### Phase 2: Agent Tests
- [x] **Trust Scoring Test**: Verify RULE-011 formula accuracy
  - Input: Agent with known compliance/accuracy history
  - Expected: Trust score matches formula ✓
- [x] **Task Delegation Test**: Verify governance_route_task_to_agent()
  - Input: GAP with known category/priority
  - Expected: Routes to correct agent role ✓
- [x] **Handoff Test**: Verify governance_create_handoff()
  - Input: Task completion with evidence
  - Expected: Handoff file created, status updated ✓

### Phase 3: Recovery Tests
- [x] **AMNESIA Test**: Verify context recovery
  - Input: Simulated context compaction (empty state)
  - Expected: Session context restored from claude-mem ✓
- [x] **Crash Recovery Test**: Verify RECOVER-CRASH-01-v1
  - Input: Simulated memory pressure
  - Expected: Context saved, graceful degradation ✓

### Phase 4: Integration Tests
- [ ] **End-to-End Workflow**: RESEARCH → CODING → CURATOR
  - Input: RD item with research phase
  - Expected: Full handoff chain completes
  - Status: SKIPPED (requires multi-workspace setup)
- [ ] **Governance Loop**: Propose → Vote → Apply rule
  - Input: New rule proposal
  - Expected: Bicameral approval flow works
  - Status: SKIPPED (future implementation)

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Trust Score Accuracy | 95%+ |
| Task Routing Correct | 90%+ |
| AMNESIA Recovery | <30s |
| E2E Workflow | <5 min |

---

## Implementation Notes

```bash
# Run benchmark suite
source ~/.venv/sim-ai/bin/activate
PYTHONPATH=. pytest tests/benchmarks/ -v --benchmark-json=results.json

# View results
python scripts/analyze_benchmark.py results.json
```

---

## Related

- RULE-011: Agent Trust Scoring
- RULE-024: AMNESIA Recovery Protocol
- RD-WORKSPACE: Multi-Agent Workspace Split
- GAP-006: Agent Observability

---

*Per WORKFLOW-RD-01-v1: R&D tasks follow hypothesis-experiment-evidence cycle*
