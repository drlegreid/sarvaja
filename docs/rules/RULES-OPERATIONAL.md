# Operational Rules - Sim.ai

Rules governing testing, stability, maintenance, and task execution.

---

## RULE-004: Exploratory Test Automation with Playwright MCP

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All UI/web components MUST be testable via Playwright MCP with heuristics:

### Test Automation Heuristics

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `BOUNDARY` | Test edge cases, limits, empty states | HIGH |
| `NAVIGATION` | Verify all links, routes, redirects | HIGH |
| `STATE` | Check state transitions, persistence | MEDIUM |
| `ERROR` | Trigger and verify error handling | HIGH |
| `ACCESSIBILITY` | Check a11y compliance | MEDIUM |
| `PERFORMANCE` | Measure load times | LOW |

### Playwright MCP Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URL |
| `browser_screenshot` | Capture current state |
| `browser_click` | Click element |
| `browser_fill` | Fill form field |
| `browser_evaluate` | Run JavaScript |

### Validation
- [ ] Playwright MCP configured
- [ ] At least 3 heuristics applied per test session
- [ ] Screenshots captured for each state

---

## RULE-005: Memory & MCP Stability

**Category:** `stability` | **Priority:** HIGH | **Status:** ACTIVE

### Memory Thresholds

| Memory | Status | Action |
|--------|--------|--------|
| < 500 MB | HEALTHY | Normal operation |
| 500-1000 MB | NORMAL | Active development |
| 1000-1500 MB | WARNING | Monitor closely |
| 1500-2000 MB | HIGH | Consider closing files |
| > 2000 MB | CRITICAL | Restart soon |
| > 3000 MB | EMERGENCY | Restart immediately |

### MCP Stability Tiers

| Tier | MCPs | Risk |
|------|------|------|
| **STABLE** | claude-mem, sequential-thinking, filesystem, git | LOW |
| **PRODUCTIVE** | octocode, powershell, llm-sandbox | LOW |
| **MODERATE** | desktop-commander, playwright | MEDIUM |
| **CONDITIONAL** | godot-mcp | MEDIUM |

### Process Leak Detection

```powershell
# Check node process count
(Get-Process node -EA SilentlyContinue).Count
# Thresholds: 1-3 HEALTHY, 4-7 NORMAL, 8-10 WARNING, >10 LEAK
```

### Recovery Levels
1. **Soft**: Restart Cascade/Claude Code
2. **Medium**: Disable heavy MCPs
3. **Hard**: Kill node processes
4. **Nuclear**: Full system restart

### Validation
- [ ] Memory stays below 2GB
- [ ] Node process count < 10
- [ ] No MCP timeouts > 30 seconds

---

## RULE-012: Deep Sleep Protocol (DSP)

**Category:** `maintenance` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

Periodically invoke DSP for deliberate technical backlog hygiene.

### DSP Phases

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE
```

| Phase | Purpose | Actions |
|-------|---------|---------|
| **AUDIT** | Inventory gaps | Scan TODO.md, TypeDB |
| **HYPOTHESIZE** | Form improvement theories | Propose changes |
| **MEASURE** | Quantify current state | Run tests, metrics |
| **OPTIMIZE** | Apply improvements | Clean backlog |
| **VALIDATE** | Verify improvements | Full test suite |

### When to Invoke DSP

| Trigger | Scope | Cadence |
|---------|-------|---------|
| **Session End** | Quick audit | Every session (5 min) |
| **Milestone** | Full backlog hygiene | Weekly (30 min) |
| **Pre-Release** | Deep technical review | Before releases (2+ hours) |

### Quick DSP Checklist

- [ ] New gaps added to TODO.md?
- [ ] Decisions logged in evidence/?
- [ ] Tests still passing?
- [ ] Session log completed?

### Validation
- [ ] DSP quick audit at each session end
- [ ] DSP full audit at each milestone
- [ ] No stale items > 30 days

---

## RULE-014: Autonomous Task Sequencing

**Category:** `autonomy` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Agents MUST autonomously sequence tasks according to product strategy. Continue until explicit halt command.

### Halt Commands

| Command | Action |
|---------|--------|
| `STOP` | Immediate halt, save state |
| `HALT` | Immediate halt, save state |
| `STAI` | Immediate halt, save state |
| `RED ALERT` | Emergency stop, prioritize stability |
| `ALERT` | Pause and await instructions |

### Task Sequencing Protocol

```
1. ASSESS current task queue
2. PRIORITIZE by product strategy
3. EXECUTE highest-priority task
4. VALIDATE completion (tests pass)
5. CONTINUE to next task
6. REPEAT until HALT or queue empty
```

### Priority Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **P0** | Blocking production | Execute immediately |
| **P1** | Strategic milestone | Execute in sequence |
| **P2** | Technical hygiene | Execute during DSP |
| **P3** | Nice-to-have | Queue for later |

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Ask "should I continue?" | Continue automatically |
| Stop after each task | Batch related tasks |
| Wait for approval on routine | Only halt on HALT commands |
| Prioritize urgent over strategic | Follow product strategy |

### Validation
- [ ] Tasks sequenced by product strategy
- [ ] No unnecessary pauses
- [ ] Halt only on explicit commands

---

*Per RULE-012: Deep Sleep Protocol*
