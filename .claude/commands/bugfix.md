---
description: Execute structured bugfix workflow (TEST-BUGFIX-01-v1)
allowed-tools: mcp__gov-tasks__task_create, mcp__gov-tasks__task_update, mcp__gov-tasks__tasks_list, mcp__gov-sessions__session_start, mcp__gov-sessions__session_end, mcp__gov-tasks__taxonomy_get, Read, Glob, Grep, Edit, Write, Bash
---

# Bugfix Workflow (TEST-BUGFIX-01-v1)

Execute the 7-step structured bugfix workflow: EXPLORE -> DETECT -> REGISTER -> PRIORITIZE -> TEST -> FIX -> VALIDATE.

## Workflow Steps

### Step 1: EXPLORE
- Ask user what bug(s) need fixing, or accept arguments
- Search codebase for related code using Glob/Grep
- Read relevant files to understand current behavior
- Document the observed vs expected behavior

### Step 2: DETECT
- Identify root cause(s) for each bug
- Document which files/functions are affected
- Note any related issues or regressions

### Step 3: REGISTER
- For each bug found, create a task via `task_create`:
  - `task_type`: "bug"
  - `priority`: Based on severity (auto-generates BUG-{NNN} ID)
- Start a governance session via `session_start`

### Step 4: PRIORITIZE
- Rank bugs by severity: CRITICAL > HIGH > MEDIUM > LOW
- Fix in priority order
- Report the prioritized list to user

### Step 5: TEST (TDD)
- Write failing unit tests FIRST for each bug
- Tests should reproduce the exact failure condition
- Run tests to confirm they fail: `.venv/bin/python3 -m pytest {test_file} -v`

### Step 6: FIX
- Implement the minimum fix for each bug
- Follow existing code patterns and conventions
- Keep changes focused (no unrelated cleanup)

### Step 7: VALIDATE (3-Tier per TEST-E2E-01-v1)

| Tier | Action | Command |
|------|--------|---------|
| 1. Unit | Run all unit tests | `.venv/bin/python3 -m pytest tests/unit/ -q` |
| 2. Integration | Test API endpoint | `curl http://localhost:8082/api/{endpoint}` |
| 3. Visual | Verify UI if applicable | Playwright MCP interaction |

### Step 8: CLOSE
- Update each bug task to DONE via `task_update`
- End governance session via `session_end`
- Report summary: bugs fixed, tests added, files changed

## Output Format

```
=== BUGFIX SESSION SUMMARY ===
Bugs Fixed: N
Tests Added: N
Files Changed: N

| Bug ID | Description | Priority | Status |
|--------|-------------|----------|--------|
| BUG-XXX | ... | HIGH | FIXED |

Validation: Tier 1 [PASS] | Tier 2 [PASS] | Tier 3 [PASS/N/A]
```
