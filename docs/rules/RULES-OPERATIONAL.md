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

Periodically invoke DSP for deliberate technical backlog hygiene with MCP integration.

### DSP Phases (Enhanced)

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT
```

| Phase | Purpose | MCPs Required |
|-------|---------|---------------|
| **AUDIT** | Inventory gaps, orphans, loops | claude-mem, TypeDB |
| **HYPOTHESIZE** | Form improvement theories | sequential-thinking |
| **MEASURE** | Quantify current state | powershell, llm-sandbox |
| **OPTIMIZE** | Apply improvements | filesystem, git |
| **VALIDATE** | Run tests (chunked categories) | pytest, llm-sandbox |
| **DREAM** | Explore product, discover issues | playwright, docker |
| **REPORT** | Link to GitHub, close issues | git, octocode |

### MCP Checks (Mandatory)

| Check | MCP | Query |
|-------|-----|-------|
| **TypeDB Health** | TypeDB MCP | Port 1729, schema loaded |
| **Orphan Detection** | TypeDB | Rules/gaps with no references |
| **Loop Detection** | TypeDB | Circular dependencies |
| **Memory Dedup** | claude-mem | Similarity > 85% = duplicate |
| **Index Quality** | TypeDB | Completeness, consistency, freshness |

### Test Evidence (BDD Mode)

```yaml
test_modes:
  ci_mode: minimal output, full on fail
  trace_mode: prestep → action → poststep → substep

test_chunks:
  unit: 30s timeout, P0
  integration: 120s, P1
  bdd: 60s, P1 (Given-When-Then)
```

### When to Invoke DSP

| Trigger | Scope | Cadence |
|---------|-------|---------|
| **Session End** | Quick audit | Every session (5 min) |
| **Milestone** | Full backlog + DREAM | Weekly (30 min) |
| **Pre-Release** | Deep review + Report | Before releases (2+ hours) |

### Quick DSP Checklist

- [ ] New gaps added to TODO.md?
- [ ] Decisions logged in evidence/?
- [ ] Tests still passing (chunked)?
- [ ] Session log completed?
- [ ] MCP usage audited?
- [ ] TypeDB orphans checked?

### Validation
- [ ] DSP quick audit at each session end
- [ ] DSP full audit at each milestone
- [ ] No stale items > 30 days
- [ ] GitHub issue linked/closed on commit
- [ ] All MCP checks passed

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

## RULE-015: R&D Workflow with Human Approval Gate

**Category:** `autonomy` | **Priority:** CRITICAL | **Status:** ACTIVE (GitHub integration ON HOLD)

### Directive

R&D tasks that may impact budget, architecture, or strategic direction MUST require human approval unless DEEP autonomy is mandated.

### Autonomy Levels

| Level | Trigger | Actions | Approval |
|-------|---------|---------|----------|
| **ROUTINE** | Default task | Execute queue | None |
| **STRATEGIC** | P1 milestone | Execute + log | Post-hoc review |
| **R&D** | Research needed | Propose + WAIT | **Human required** |
| **DEEP** | Explicit mandate | Full autonomy | Pre-approved |

### R&D Triggers

Tasks flagged as R&D when they involve:
- New technology evaluation (RULE-008 scorecard)
- Architecture changes affecting multiple components
- External dependency additions
- Budget-impacting decisions (API costs, subscriptions)
- Infrastructure changes (new containers, services)

### R&D Gate Protocol

```
1. Create R&D proposal document
2. Link to relevant rules (RULE-008, RULE-010)
3. Estimate effort/risk
4. PAUSE for human review
5. On approval: proceed with logging
6. On reject: archive proposal
```

### DEEP Autonomy Mandate

When user specifies "DEEP" or grants DEEP autonomy:
- Time-boxed execution (default: 2 hours)
- Full evidence collection
- All decisions logged
- Report on completion

### Budget Flags

| Level | Criteria | Approval |
|-------|----------|----------|
| **LOW** | < 2h effort, no external cost | Auto |
| **MEDIUM** | 2-8h, potential API costs | Review |
| **HIGH** | > 8h, infrastructure changes | Human |
| **CRITICAL** | Procurement/subscription | Executive |

### Integration with DSP

R&D tasks discovered during DSP DREAM phase:
1. Flag as R&D in TODO.md
2. Create proposal in docs/proposals/
3. ~~Link to GitHub issue~~ **ON HOLD** (budget concern)
4. Wait for human approval (via chat/session)
5. On approval: add to task queue

> **DEFERRED:** GitHub issue automation with before/after evidence, pros/cons analysis.
> Reason: Budget uncertainty until next period. Manual approval via session continues.

### Validation
- [ ] R&D tasks properly flagged
- [ ] Proposals created before execution
- [ ] Budget impact assessed
- [ ] Human approval for non-DEEP R&D
- [ ] Evidence collected for DEEP sessions

---

*Per RULE-014: Autonomous Task Sequencing + RULE-012: DSP*
