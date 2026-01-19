# GAP-CONTEXT-EFFICIENCY-001: Session Context Burned on Infrastructure

**Status**: RESOLVED
**Priority**: HIGH
**Discovered**: 2026-01-19
**Resolved**: 2026-01-19
**Owner**: EPIC-STABILITY

## Problem

100% of session context consumed by MCP troubleshooting instead of actual work.

## Evidence

### Session 2026-01-19 Context Breakdown

| Activity | Context % | Notes |
|----------|-----------|-------|
| Debugging MCP failures (duplicate tools discovery) | ~40% | Investigation loop across 4 MCP servers |
| Container vs venv mode investigation | ~20% | Discovered container startup too slow |
| Multiple restart cycles + verification | ~25% | Each fix required restart + verification |
| Creating MCP-HEALTH-01-v1 rule + docs | ~15% | Documentation of fixes |
| **Actual work completed** | **0%** | All context burned on infrastructure |

### Clarification

The health report output itself is now compact (~15 lines). The problem was the **troubleshooting process** that consumed context, not the health report verbosity. The fixes applied address the root causes that triggered the troubleshooting loop.

## Root Causes Identified

1. **MCP startup failures** - No pre-flight validation
2. **Duplicate tool registrations** - No CI lint guard
3. **Container mode default** - Too slow for Claude Code timeout
4. **Verbose health output** - Tables instead of compact status

## Strategic Direction (Approved)

- Pre-flight MCP validation before session work
- CI guards for common issues
- Compact status outputs
- Early context save (before 80% limit)

## Tactical Implementation (Completed 2026-01-19)

### TACTIC-1: Pre-flight MCP Validation

| Item | Implementation | Status |
|------|---------------|--------|
| TACTIC-1-A | SessionStart hook validates MCP modules | DONE |
| File | `.claude/hooks/checkers/mcp_preflight.py` | Created |
| Function | `MCPPreflightChecker.check()` | Implemented |

### TACTIC-2: CI Guards for Duplicate Tools

| Item | Implementation | Status |
|------|---------------|--------|
| TACTIC-2-A | Pre-commit script blocks duplicate tools | DONE |
| TACTIC-2-C | Unit tests for duplicate detection | DONE |
| Script | `scripts/check_mcp_duplicates.sh` | Created |
| Tests | `tests/unit/test_mcp_preflight.py` (8 tests) | Passing |

### TACTIC-3: Early Context Save

| Item | Implementation | Status |
|------|---------------|--------|
| TACTIC-3-A | Document /entropy usage | DONE |
| TACTIC-3-B | Auto-save hook at threshold | DONE |
| TACTIC-3-C | CLAUDE.md context reminder | DONE |
| Doc | `.claude/commands/entropy.md` | Updated |
| Rule | `CONTEXT-SAVE-01-v1` | Created |
| Thresholds | 50/100/150 tool calls | Implemented |

## Fixes Already Applied

| Fix | File | Status |
|-----|------|--------|
| venv mode default | scripts/mcp-runner.sh | DONE |
| Removed duplicate governance_list_agents | governance/mcp_tools/trust.py | DONE |
| Removed duplicate governance_health | governance/mcp_server_core.py | DONE |
| MCP service categories | MCP-HEALTH-01-v1 | DONE |

## Resolution

**GAP RESOLVED**: All tactics implemented successfully.

### Prevention Measures Active

1. **Pre-flight validation** - MCP modules validated before session work
2. **Duplicate detection** - Pre-commit hook blocks duplicate tools
3. **Entropy monitoring** - Thresholds at 50/100/150 tool calls
4. **Context save protocol** - CONTEXT-SAVE-01-v1 rule documented

### Verification

```bash
# Unit tests pass
scripts/pytest.sh tests/unit/test_mcp_preflight.py -v
# 8 passed

# Pre-commit check passes
scripts/check_mcp_duplicates.sh
# OK: No duplicate tools found, 84 tools scanned
```
