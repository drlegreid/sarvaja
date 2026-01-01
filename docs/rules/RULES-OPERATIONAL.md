# Operational Rules - Sim.ai

Rules governing testing, stability, maintenance, and task execution.

---

## RULE-004: Exploratory Test Automation & Executable Specification

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All components MUST be testable via domain-specific heuristics. Exploratory testing complements TDD cycle to ensure proper coverage and evidence capture for audit.

### Workflow Principles (CRITICAL)

| Principle | Directive | Gate |
|-----------|-----------|------|
| **Gaps Before Implementation** | Document all gaps BEFORE coding | No PR without GAP-* references |
| **Page Object Model (POM)** | All UI tests use OOP page objects | Code review check |
| **Test What You Ship** | RULE-023 compliance | CI/CD gate |
| **Insight Capture** | Document insights during task execution | Task description updated |

### Insight Capture Protocol (CRITICAL)

```
DURING every task execution, capture and document:

1. DISCOVERIES
   └── New patterns, behaviors, or edge cases found
   └── Update task description with findings

2. GAPS IDENTIFIED
   └── Missing features → GAP-UI-XXX or GAP-XXX
   └── Link gap ID in task description

3. DECISIONS MADE
   └── Why approach X was chosen over Y
   └── Evidence/rationale recorded

4. ARTIFACTS CREATED
   └── Tests, screenshots, API responses
   └── Store in evidence/ folder

Format in task/gap description:
---
## Insights Captured
- [DISCOVERY] Found that X behaves as Y when Z
- [GAP] GAP-UI-006: Missing validation message on form
- [DECISION] Used polling over WebSocket due to simplicity
- [ARTIFACT] evidence/screenshots/rules-list-2024-12-25.png
---

This enables:
• Knowledge accumulation across sessions
• Audit trail for decisions
• Reproducibility of discoveries
• Pattern recognition over time
```

### Test Strategy Integration

```
EXPLORE (Gaps) → DOCUMENT (GAP-*) → PRIORITIZE → TDD (RED→GREEN→REFACTOR)
       ↓                                              ↓
  Gap Discovery                               Page Object Tests
```

### Page Object Model Requirements

```python
# Required structure for UI tests
tests/
├── pages/                    # Page Objects (OOP)
│   ├── base_page.py         # BasePage with common methods
│   ├── rules_page.py        # RulesPage(BasePage)
│   ├── sessions_page.py     # SessionsPage(BasePage)
│   └── components/          # Reusable UI components
│       ├── navbar.py
│       ├── table.py
│       └── form.py
├── locators/                 # Centralized selectors
│   └── locators.py          # All element selectors
└── e2e/                      # Robot Framework tests
    └── *.robot              # Uses page object keywords
```

### Legacy Test Strategy Integration

```
TDD Spec (What) ←→ Exploratory (How) ←→ Executable Spec (Verify)
     ↓                    ↓                      ↓
  Coverage Map    Heuristic Discovery      Healthcheck Suite
```

---

### Domain Heuristics

#### UI Testing (Playwright MCP)

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `BOUNDARY` | Edge cases, limits, empty states, max input | HIGH |
| `NAVIGATION` | All links, routes, redirects, back button | HIGH |
| `STATE` | State transitions, persistence, refresh | MEDIUM |
| `ERROR` | Error handling, validation messages | HIGH |
| `ACCESSIBILITY` | a11y compliance, keyboard nav, screen reader | MEDIUM |
| `PERFORMANCE` | Load times, LCP, FID, CLS metrics | LOW |
| `RESPONSIVE` | Breakpoints, mobile/tablet/desktop views | MEDIUM |
| `INTERRUPTIBLE` | Mid-action cancellation, timeout recovery | HIGH |

#### API Testing (PowerShell/llm-sandbox)

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `CONTRACT` | Schema validation, required fields | HIGH |
| `IDEMPOTENCY` | Repeated calls same result | HIGH |
| `AUTH` | Token validation, expiry, refresh | CRITICAL |
| `RATE_LIMIT` | Throttling, 429 handling | MEDIUM |
| `PAYLOAD` | Empty, malformed, oversized requests | HIGH |
| `VERSIONING` | API version compatibility | MEDIUM |
| `TIMEOUT` | Long-running request handling | HIGH |

#### Shell/CLI Testing (PowerShell MCP)

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `EXIT_CODE` | Proper return codes (0=success) | HIGH |
| `STDERR` | Error output to correct stream | HIGH |
| `PIPE` | Piping and chaining behavior | MEDIUM |
| `ENCODING` | UTF-8, special characters | MEDIUM |
| `PATH_SAFETY` | Spaces, special chars in paths | HIGH |
| `PRIVILEGE` | Admin/elevated permission handling | CRITICAL |

#### Docker Testing (Container Inspection)

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `HEALTHCHECK` | Container health endpoint responds | CRITICAL |
| `RESTART` | Restart policy works correctly | HIGH |
| `VOLUME` | Data persistence across restarts | HIGH |
| `NETWORK` | Inter-container communication | HIGH |
| `RESOURCE` | Memory/CPU limits respected | MEDIUM |
| `LOG` | Logs accessible, not overflowing | MEDIUM |
| `GRACEFUL` | Clean shutdown, signal handling | HIGH |

#### Safety & Security Heuristics

| Heuristic | Description | Priority |
|-----------|-------------|----------|
| `INJECTION` | SQL, command, XSS prevention | CRITICAL |
| `SECRETS` | No hardcoded credentials | CRITICAL |
| `AUDIT_TRAIL` | Actions logged with timestamp | HIGH |
| `ISOLATION` | Process/container isolation | HIGH |
| `ROLLBACK` | Failure recovery, state restore | HIGH |
| `TIMEOUT_SAFE` | No hanging processes | HIGH |

---

### Executable Specification

```yaml
executable_spec:
  purpose: Living documentation that runs as tests
  components:
    - healthcheck_suite: Quick smoke tests (< 30s)
    - contract_tests: API schema validation
    - integration_probes: Cross-service verification

  healthcheck_endpoints:
    - GET /health → 200 {"status": "ok"}
    - GET /ready → 200 when dependencies up
    - GET /metrics → Prometheus format

  execution:
    on_deploy: healthcheck_suite (P0)
    on_commit: contract_tests (P1)
    on_release: full_suite (P0+P1+P2)
```

### MCP Tools by Domain

| Domain | MCP | Tools |
|--------|-----|-------|
| **UI** | playwright | browser_navigate, browser_click, browser_screenshot |
| **API** | powershell, llm-sandbox | Invoke-WebRequest, pytest |
| **Shell** | powershell | Start-Process, Get-Process |
| **Docker** | desktop-commander | docker ps, docker logs, docker stats |
| **Evidence** | filesystem, claude-mem | Write results, store findings |

### Evidence Capture Protocol

```yaml
evidence_capture:
  per_test:
    - timestamp: ISO 8601
    - heuristic: Which heuristic applied
    - domain: UI/API/Shell/Docker
    - input: What was tested
    - expected: What should happen
    - actual: What happened
    - screenshot: If UI test
    - logs: Relevant log snippet

  on_failure:
    - full_trace: Stack trace or error
    - reproduction: Steps to reproduce
    - context: Environment state

  audit_log:
    location: evidence/test-runs/
    retention: 30 days
    format: JSON + screenshots
```

### DevOps Wisdom Capture (RULE-010)

```yaml
wisdom_capture:
  on_discovery:
    - Pattern identified → Document in session log
    - Failure cluster → Create GAP entry
    - Workaround found → Add to knowledge base

  encoding:
    - Successful patterns → TypeDB rule
    - Common failures → Checklist item
    - Tool quirks → MCP notes
```

### Validation
- [ ] At least 3 heuristics per domain tested
- [ ] Evidence captured for all test runs
- [ ] Healthcheck suite runs in < 30 seconds
- [ ] Executable spec updated when API changes
- [ ] Safety heuristics applied to all external inputs
- [ ] Audit trail maintained for 30 days

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

### Semantic Code Structure (DSP Hygiene)

**Principle:** Files >300 lines MUST be restructured during DSP night cycles.

**Paradigm Alignment:**
- **Functional Programming:** Pure functions, immutability, composition
- **Digital Twin:** Entity-centric modules mirroring domain reality

**Semantic Decomposition Pattern:**

```
BEFORE (monolithic):
  governance_ui.py (800 lines)

AFTER (semantic):
  ui/
  ├── __init__.py
  ├── entities/           # BY DOMAIN (noun)
  │   ├── rules_view.py   # Rule entity UI
  │   ├── decisions_view.py
  │   ├── sessions_view.py
  │   └── tasks_view.py
  ├── concerns/           # BY ACTION (verb)
  │   ├── navigation.py   # Nav logic
  │   ├── forms.py        # CRUD forms
  │   ├── filters.py      # Filter/sort
  │   └── state.py        # State management
  └── components/         # BY STRUCTURE (reusable)
      ├── table.py
      ├── detail_card.py
      └── dialog.py
```

**Decomposition Heuristics:**

| Signal | Action |
|--------|--------|
| File >300 lines | Split by entity |
| Class >200 lines | Extract concerns |
| Function >50 lines | Compose smaller functions |
| Repeated patterns | Extract to component |
| Mixed concerns (UI + logic) | Separate layers |

**Functional Programming Principles:**

```python
# ✅ DO: Pure functions, composition
def get_rule_color(status: str) -> str:
    return STATUS_COLORS.get(status, "grey")

# ✅ DO: Immutable data transforms
rules_filtered = [r for r in rules if r.status == "ACTIVE"]

# ❌ DON'T: Side effects in transforms
def process_rules(rules):
    for r in rules:
        r["processed"] = True  # Mutation!
```

**Digital Twin Alignment:**

```yaml
domain_entities:
  Rule:
    views: [list, detail, form]
    concerns: [crud, filter, validate]

  Decision:
    views: [list, detail]
    concerns: [timeline, impact]

  Session:
    views: [list, timeline, evidence]
    concerns: [search, export]
```

### Quick DSP Checklist

- [ ] New gaps added to TODO.md?
- [ ] Decisions logged in evidence/?
- [ ] Tests still passing (chunked)?
- [ ] Session log completed?
- [ ] MCP usage audited?
- [ ] TypeDB orphans checked?
- [ ] Documents structured (evidence/, tests/)?
- [ ] TypeDB document links synced?
- [ ] **Files >300 lines flagged for restructure?**
- [ ] **Semantic decomposition applied?**

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

## RULE-020: LLM-Driven E2E Test Generation

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

E2E tests MUST be generated via LLM-driven exploratory sessions using Playwright MCP. LLM is used ONLY for:
1. **Exploration phase** - Discover UI paths via heuristics
2. **Test generation** - Convert exploration to deterministic Robot Framework tests
3. **Failure analysis** - Analyze why deterministic tests failed

LLM is NOT used during test execution.

### Related Rules & Workflows

| Related | Purpose |
|---------|---------|
| **RULE-004** | Exploratory heuristics library (domain-specific) |
| **RULE-023** | Test Before Ship (quality gate) |
| **[UI-FIRST-SPRINT-WORKFLOW](../workflows/UI-FIRST-SPRINT-WORKFLOW.md)** | DSM + TDD + EXPLORATORY fusion |

### Integration with UI-First Sprint (P10)

```
DSM (Domain Model)     → Define what UI SHOULD show
     ↓
TDD (Robot Tests)      → Write failing tests for expected behavior
     ↓
EXPLORATORY (Playwright) → Discover gaps, validate, generate tests
     ↓
ROBOT EXECUTION        → Deterministic test runs
```

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    E2E Test Generation Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: EXPLORATION (LLM + Playwright MCP)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  LLM Agent                                                       │    │
│  │     │                                                            │    │
│  │     ├── Apply heuristic (page_structure, form_discovery, etc)   │    │
│  │     ├── mcp__playwright__browser_snapshot                        │    │
│  │     ├── mcp__playwright__browser_click                           │    │
│  │     ├── mcp__playwright__browser_type                            │    │
│  │     └── Record successful paths                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Phase 2: GENERATION (Deterministic conversion)                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  ExplorationSession → Robot Framework test cases                │    │
│  │     • Click → Click keyword                                      │    │
│  │     • Type → Fill Text keyword                                   │    │
│  │     • Assert → Wait For Elements State                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Phase 3: EXECUTION (No LLM, deterministic)                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  robot --include smoke task_ui.robot                            │    │
│  │     • Run generated tests                                        │    │
│  │     • Capture screenshots on failure                             │    │
│  │     • Generate JUnit XML                                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Phase 4: ANALYSIS (LLM only on failure)                                │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  IF test fails:                                                  │    │
│  │     • Load failure screenshot                                    │    │
│  │     • Load error message                                         │    │
│  │     • LLM analyzes: app bug vs test issue                       │    │
│  │     • Generate fix recommendation                                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Exploration Heuristics

| Heuristic | Purpose | MCP Calls |
|-----------|---------|-----------|
| `page_structure` | Discover page layout and elements | browser_snapshot |
| `form_discovery` | Find and test form validation | browser_type, browser_click |
| `navigation_flow` | Test all navigation paths | browser_navigate, browser_click |
| `error_handling` | Trigger and verify error states | browser_type (invalid data) |
| `accessibility_quick` | Basic a11y compliance | browser_evaluate (tab through) |

### Exploration Session Schema

```yaml
exploration_session:
  name: "Task Console Smoke Test"
  url: "http://localhost:7777/ui"
  heuristics_applied:
    - page_structure
    - form_discovery
  steps:
    - action: navigate
      target: "http://localhost:7777/ui"
      description: "Open Task Console"
    - action: snapshot
      target: ""
      description: "Capture initial page state"
    - action: assert_visible
      target: "form, .task-form"
      description: "Verify task form is visible"
    - action: type
      target: "textarea#prompt"
      value: "Test task"
      description: "Fill in task prompt"
    - action: click
      target: "button:has-text('Submit')"
      description: "Submit the task"
    - action: assert_visible
      target: ".task-item"
      description: "Verify task appears in list"
  findings:
    - "Form validation missing for empty prompt"
    - "No loading indicator during submission"
```

### Generated Test Format

```robot
*** Test Cases ***
Task Console Smoke Test
    [Documentation]    Auto-generated from exploration session
    [Tags]    generated    exploratory    smoke
    Go To    http://localhost:7777/ui
    # Capture initial page state
    Wait For Elements State    form, .task-form    visible
    Fill Text    textarea#prompt    Test task
    Click    button:has-text('Submit')    # Submit the task
    Wait For Elements State    .task-item    visible    # Verify task appears
```

### Failure Analysis Protocol

```yaml
on_failure:
  capture:
    - screenshot: "failure_{test_name}_{timestamp}.png"
    - html: Page source at failure point
    - logs: Browser console errors
    - trace: Playwright trace file

  llm_analysis:
    prompt: |
      Analyze this test failure:
      Test: {test_name}
      Step: {failed_step}
      Error: {error_message}
      Screenshot: [attached]

      Determine:
      1. Is this an app bug or test issue?
      2. Root cause analysis
      3. Suggested fix

    output:
      - classification: "app_bug" | "test_issue" | "environment"
      - root_cause: "string"
      - fix: "string"
      - confidence: 0.0-1.0
```

### MCP Tool Matrix

| Phase | MCP | Tools |
|-------|-----|-------|
| **Explore** | playwright | browser_navigate, browser_snapshot, browser_click, browser_type |
| **Generate** | filesystem | write_file (Robot tests) |
| **Execute** | powershell | robot command |
| **Analyze** | filesystem, claude-mem | read screenshots, store learnings |

### TypeDB Integration

```typeql
define
  exploration-session sub entity,
    owns session-id,
    owns session-name,
    owns session-url,
    owns started-at,
    owns completed-at,
    plays session-step:session;

  exploration-step sub entity,
    owns step-id,
    owns action-type,
    owns target-selector,
    owns step-value,
    owns description,
    owns success,
    plays session-step:step;

  session-step sub relation,
    relates session,
    relates step;

  test-case sub entity,
    owns test-id,
    owns test-name,
    owns generated-from,
    owns robot-code,
    plays generates:test;

  generates sub relation,
    relates session,
    relates test;
```

### Validation

- [ ] Exploration sessions recorded in TypeDB
- [ ] Generated tests are deterministic (no LLM at runtime)
- [ ] Failure analysis only invoked on test failure
- [ ] Evidence captured: screenshots, traces, analysis
- [ ] Generated tests can run in CI without LLM

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Use LLM to decide test pass/fail | Use deterministic assertions |
| Re-explore on each test run | Generate once, run many times |
| Skip recording exploration steps | Log every action for reproducibility |
| Analyze every test result with LLM | Only analyze failures |

---

## RULE-021: MCP Healthcheck Protocol

**Category:** `stability` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Every MCP-dependent operation MUST verify MCP server health before execution. Failures must be logged and recovery attempted before failing the operation.

**CRITICAL (GAP-MCP-003):** At session start, agents MUST call `governance_health` tool to verify Docker services (TypeDB, ChromaDB) are running. If unhealthy, notify user with recovery command before proceeding.

### Healthcheck Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCP Healthcheck Protocol                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Level 1: PRE-OPERATION CHECK (per tool call)                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Before MCP tool call:                                          │    │
│  │     └── Verify MCP server responding (via mcp list)             │    │
│  │     └── Check allowed failures list                             │    │
│  │     └── Log health status                                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Level 2: SESSION START CHECK (MANDATORY - GAP-MCP-003)                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  At session initialization (BEFORE any task execution):         │    │
│  │     └── CALL governance_health tool                             │    │
│  │     └── Check action_required field in response                 │    │
│  │     └── IF unhealthy:                                           │    │
│  │         ├── NOTIFY user: "Docker services down"                 │    │
│  │         ├── PROVIDE recovery command from response              │    │
│  │         └── WAIT for user acknowledgment                        │    │
│  │     └── Log health status to session                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Level 3: RECOVERY PROTOCOL                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  On MCP failure:                                                │    │
│  │     └── Attempt resurrection (restart MCP)                      │    │
│  │     └── Use fallback MCP if available                           │    │
│  │     └── Log failure and continue degraded                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### MCP Server Tiers

| Tier | Servers | Failure Impact |
|------|---------|----------------|
| **CRITICAL** | filesystem, git, powershell | Session blocked |
| **HIGH** | claude-mem, desktop-commander | Degraded functionality |
| **MEDIUM** | playwright, octocode, llm-sandbox | Feature unavailable |
| **CONDITIONAL** | godot-mcp | Skip if not needed |

### Allowed Failures

Servers that may fail without blocking operations:
- `godot-mcp` - Requires Godot Editor running
- `llm-sandbox` - Requires Docker running
- `octocode` - Requires GitHub PAT configured
- `context7` - May be disabled for stability

### Health Check Implementation

```python
# Per-operation health check
def verify_mcp_health(server_name: str) -> bool:
    """Check if MCP server is responding."""
    health_output = run("npx -y @anthropic-ai/claude-code mcp list")

    if server_name in ALLOWED_FAILURES:
        return True  # Skip check for allowed failures

    for line in health_output.split("\n"):
        if server_name in line:
            if "Failed" in line:
                log_warning(f"MCP {server_name} failed health check")
                return False
            return True

    return False
```

### Recovery Protocol

```yaml
on_mcp_failure:
  attempt_1:
    action: "Wait 5 seconds, retry"
    timeout: 5s

  attempt_2:
    action: "Restart MCP server"
    command: "claude mcp restart <server>"
    timeout: 30s

  attempt_3:
    action: "Check Docker/dependencies"
    for: ["llm-sandbox", "playwright"]

  fallback:
    action: "Continue degraded, log failure"
    evidence: "Log to session file"
```

### Validation

- [ ] MCP health checked before critical operations
- [ ] Allowed failures list respected
- [ ] Recovery attempted before failure
- [ ] Health status logged to session evidence

---

## RULE-022: Integrity Verification (Frankel Hash)

**Category:** `security` | **Priority:** HIGH | **Status:** DRAFT

### Directive

Critical files and configurations MUST have integrity verification via content hashing. Use Frankel Hash methodology for efficient similarity detection and change tracking.

### Frankel Hash Concept

```
Traditional Hash: Full file → SHA-256 → 64 chars
                  ANY change = completely different hash

Frankel Hash:     File → Chunks → Per-chunk hashes → Merkle tree
                  Change localized to specific chunks
                  Similarity score computable
```

### Use Cases

| Use Case | Hash Type | Purpose |
|----------|-----------|---------|
| **Config files** | SHA-256 | Detect tampering |
| **Rule files** | Frankel | Track incremental changes |
| **Session logs** | SHA-256 | Audit trail integrity |
| **TypeDB schema** | Frankel | Schema evolution tracking |
| **MCP configs** | SHA-256 | Security verification |

### Implementation

```python
class FrankelHash:
    """Chunk-based similarity hashing."""

    CHUNK_SIZE = 512  # bytes

    def compute(self, content: str) -> dict:
        """Compute Frankel hash with chunk hashes."""
        chunks = self._split_chunks(content)
        chunk_hashes = [sha256(c) for c in chunks]

        return {
            "full_hash": sha256(content),
            "chunk_count": len(chunks),
            "chunk_hashes": chunk_hashes,
            "merkle_root": self._merkle_root(chunk_hashes)
        }

    def similarity(self, hash_a: dict, hash_b: dict) -> float:
        """Compute similarity between two Frankel hashes."""
        if hash_a["full_hash"] == hash_b["full_hash"]:
            return 1.0

        matching = sum(
            1 for a, b in zip(hash_a["chunk_hashes"], hash_b["chunk_hashes"])
            if a == b
        )
        return matching / max(len(hash_a["chunk_hashes"]), len(hash_b["chunk_hashes"]))
```

### Files to Track

| File Category | Files | Check Frequency |
|---------------|-------|-----------------|
| **Governance** | `schema.tql`, `data.tql` | On change |
| **Rules** | `docs/rules/*.md` | On change |
| **Config** | `docker-compose.yml`, `.env` | Session start |
| **Evidence** | `evidence/*.md` | On create |

### TypeDB Integration

```typeql
# Store file hashes in TypeDB
file-hash sub entity,
    owns file-path,
    owns hash-type,        # "sha256" or "frankel"
    owns full-hash,
    owns chunk-count,
    owns merkle-root,
    owns computed-at,
    plays integrity-check:verified-file;

integrity-check sub relation,
    relates verified-file,
    relates checking-session,
    owns check-result,     # "pass", "fail", "changed"
    owns similarity-score;
```

### Validation

- [ ] Critical files have hash records
- [ ] Hash verified on session start
- [ ] Changes detected and logged
- [ ] Similarity scores for rule evolution

---

## RULE-023: Test Before Ship

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All code, UIs, and components MUST be tested before claiming they are complete. No shipping untested code under any circumstances.

### Origin

This rule was created on 2024-12-25 after shipping Trame UI modules (P9.2-P9.4) without verifying:
1. Dependencies were installed
2. Imports worked
3. UIs actually started

**Lesson learned:** Writing code is not the same as shipping working code.

### Test Levels

| Level | What | When |
|-------|------|------|
| **L1: Import** | Module imports without errors | After writing |
| **L2: Init** | Class/function instantiates | After writing |
| **L3: Smoke** | Basic happy path works | Before claiming done |
| **L4: Edge** | Edge cases handled | Before merge/release |

### Protocol

```
1. WRITE code
2. TEST imports work
3. TEST initialization works
4. TEST basic functionality
5. THEN mark as complete
```

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Write code → claim done | Write → Test → Verify → claim done |
| Assume dependencies installed | Verify with `pip show` or import |
| Skip testing "simple" code | Simple code fails too |
| Trust previous session's tests | Re-run relevant tests |

### Validation

- [ ] All new modules import without errors
- [ ] All new classes instantiate
- [ ] Basic functionality verified
- [ ] Dependencies documented in requirements

---

## RULE-024: AMNESIA Protocol (Autonomous Context Recovery)

**Category:** `maintenance` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

When context is lost, truncated, or a session continues from a previous conversation, agents MUST autonomously recover context using the AMNESIA Protocol before proceeding with tasks.

**CRITICAL (GAP-WORKFLOW-002):** Before major transitions (restart, crash recovery, long pause, context limit approaching), agents MUST prompt user to save context using `/save` or `/remember` skill.

### AMNESIA = Autonomous Memory & Network Extraction for Session Intelligence and Awareness

### Save Prompts Before Transitions (GAP-WORKFLOW-002)

| Transition Type | Trigger | Action |
|-----------------|---------|--------|
| **User requests restart** | "restart", "reboot", "close" | Prompt: "Would you like to /save before restart?" |
| **Context limit approaching** | >80% context used | Prompt: "Context limit approaching. Run /save?" |
| **Long pause detected** | >30 min between messages | Prompt: "Save session context before continuing?" |
| **Major milestone** | Phase completion, feature done | Prompt: "Milestone complete. Save progress with /save?" |
| **Error/crash recovery** | Resume after crash | Auto-run recovery, prompt to save after |

### Recovery Triggers

| Trigger | Indicator | Action |
|---------|-----------|--------|
| **Session Continuation** | "continued from previous conversation" | Full AMNESIA |
| **Context Truncation** | Summarized context provided | Partial AMNESIA |
| **Unknown State** | Unclear task queue or priorities | Targeted AMNESIA |
| **Explicit Request** | User asks "what were we doing?" | Full AMNESIA |

### Recovery Hierarchy (Priority Order)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AMNESIA Protocol - Recovery Layers                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: TODO.md (CRITICAL - Read First)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  File: TODO.md                                                   │    │
│  │  Contents: Current priorities, in-progress tasks, next actions   │    │
│  │  Recovery: Read and parse task queue                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 2: R&D Backlog (Strategic Context)                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  File: docs/backlog/R&D-BACKLOG.md                              │    │
│  │  Contents: Sprint status, phase progress, strategic goals        │    │
│  │  Recovery: Understand current phase and objectives               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 3: Session Summary (Provided Context)                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Source: Conversation summary (if available)                     │    │
│  │  Contents: Key decisions, files modified, pending work           │    │
│  │  Recovery: Parse summary for actionable items                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 4: Claude-Mem Queries (Semantic Memory)                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  MCP: claude-mem                                                 │    │
│  │  Queries:                                                        │    │
│  │    - "sim-ai current sprint progress"                           │    │
│  │    - "sim-ai recent session decisions"                          │    │
│  │    - "sim-ai [topic] implementation status"                     │    │
│  │  Recovery: Semantic search for relevant context                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  Layer 5: Gap Index (Known Issues)                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  File: docs/gaps/GAP-INDEX.md                                   │    │
│  │  Contents: Open gaps, blockers, dependencies                     │    │
│  │  Recovery: Understand current blockers                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Recovery Protocol

```yaml
amnesia_protocol:
  step_1_read_todo:
    action: "Read TODO.md"
    extract:
      - current_sprint
      - in_progress_tasks
      - next_priorities
    fallback: "If TODO.md missing, proceed to step 2"

  step_2_read_backlog:
    action: "Read R&D-BACKLOG.md"
    extract:
      - phase_status
      - strategic_goals
      - completion_percentage
    fallback: "If backlog missing, proceed to step 3"

  step_3_parse_summary:
    action: "Parse conversation summary"
    extract:
      - key_decisions
      - files_modified
      - pending_work
      - errors_encountered
    fallback: "If no summary, proceed to step 4"

  step_4_query_memory:
    action: "Query claude-mem"
    queries:
      - "sim-ai [project] current sprint"
      - "sim-ai recent decisions"
      - "sim-ai [topic] status"
    extract:
      - recent_context
      - relevant_memories
    fallback: "If no memories, proceed to step 5"

  step_5_check_gaps:
    action: "Read GAP-INDEX.md"
    extract:
      - open_gaps
      - blockers
      - dependencies
    fallback: "If gaps missing, use available context"

  final:
    action: "Synthesize and continue"
    output:
      - reconstructed_context
      - task_queue
      - next_action
```

### Claude-Mem Query Patterns

```python
# Always prefix with project name for isolation
queries = [
    "sim-ai current phase progress",
    "sim-ai P9 UI dashboard status",
    "sim-ai recent session 2024-12-25",
    "sim-ai TypeDB governance schema",
]

# Include dates for temporal search
"sim-ai 2024-12-25 decisions"

# Topic-specific recovery
"sim-ai RuleMonitor implementation"
"sim-ai JourneyAnalyzer tests"
```

### Recovery Output Format

After AMNESIA Protocol completes, output:

```markdown
## Context Recovered (AMNESIA Protocol)

**Current Sprint:** P9.x - [Sprint Name]
**Phase Progress:** X/Y tasks complete

**In Progress:**
- [Task currently being worked on]

**Next Actions:**
1. [Priority 1 task]
2. [Priority 2 task]

**Recent Decisions:**
- [Key decision from recent sessions]

**Active Blockers:**
- [Any gaps or blockers identified]

---
Continuing with: [specific next task]
```

### Integration with Other Rules

| Rule | Integration |
|------|-------------|
| **RULE-001** | Session evidence logging supports recovery |
| **RULE-012** | DSP hygiene keeps documents recovery-friendly |
| **RULE-014** | Autonomous sequencing resumes after recovery |
| **RULE-021** | MCP healthcheck before claude-mem queries |

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Ask user "what were we doing?" | Run AMNESIA Protocol autonomously |
| Start fresh without context | Recover context before proceeding |
| Ignore provided summary | Parse summary for actionable items |
| Query claude-mem without project prefix | Always prefix with "sim-ai" |
| Skip TODO.md | Always read TODO.md first |

### Validation

- [ ] TODO.md read on context loss
- [ ] R&D backlog consulted for strategic context
- [ ] Summary parsed for key information
- [ ] Claude-mem queried with project prefix
- [ ] Recovery output clearly summarized
- [ ] Task sequencing resumed automatically

---

## RULE-028: Change Validation Protocol

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

When code changes are implemented, agents MUST re-run exploratory validation using domain-specific heuristics from RULE-004 before marking tasks complete. This ensures changes don't introduce regressions or unexpected behaviors.

**CRITICAL: Bug Fix vs Feature Validation**

Fixing a technical bug is NOT the same as validating a feature works. Always validate at the FEATURE level, not just the BUG level.

### Validation Hierarchy (MANDATORY)

```
Level 1: TECHNICAL FIX
   └── The specific error/crash is resolved
   └── Example: "AttributeError no longer raised"

Level 2: FEATURE WORKS
   └── The intended feature functionality works E2E
   └── Example: "File content loads and displays in dialog"

Level 3: USER FLOW COMPLETE
   └── Full user journey works without friction
   └── Example: "User can view session → click file → read content → close dialog"

VALIDATION IS NOT COMPLETE UNTIL LEVEL 3 IS VERIFIED
```

### Origin (2024-12-28)

Created after a bug fix was declared "complete" when only Level 1 was validated:
- **Bug fixed**: `'GovernanceDashboard' object has no attribute '_client'` (dialog opened without crash)
- **Feature broken**: File content showed "Not Found" (API endpoint not registered)
- **Root cause**: API server not restarted (RULE-027 violation), endpoint not serving data

**Lesson**: A crash fix is not a feature fix. Always validate the full user flow.

### Trigger Conditions

| Trigger | Scope | Validation Required |
|---------|-------|---------------------|
| **Code fix** | Modified files | Targeted heuristics for affected domain |
| **Feature addition** | New components | Full heuristic suite for feature area |
| **Refactoring** | Changed structure | Smoke + regression tests |
| **Bug fix** | Specific issue | **Level 1-3 validation** (not just Level 1) |
| **Test fix** | Test code only | Re-run affected test + exploratory |

### Validation Protocol

```
WHEN code changes are implemented:

1. IDENTIFY change scope
   └── What files were modified?
   └── What domain (UI, API, DB, etc)?

2. SELECT heuristics from RULE-004
   └── UI changes → BOUNDARY, NAVIGATION, STATE, ERROR
   └── API changes → CONTRACT, IDEMPOTENCY, PAYLOAD
   └── CLI changes → EXIT_CODE, STDERR, PATH_SAFETY
   └── Docker changes → HEALTHCHECK, RESTART, VOLUME

3. RUN validation suite
   └── Unit tests for modified code
   └── Integration tests for affected flows
   └── Exploratory heuristics for domain

4. DOCUMENT results
   └── Evidence captured per RULE-001
   └── Gaps identified per RULE-004
   └── Pass/fail logged

5. VERIFY before marking complete
   └── All heuristics passed
   └── No new gaps introduced
   └── Tests green
```

### Exploratory Heuristic Matrix (Quick Reference)

| Change Type | Minimum Heuristics | Evidence |
|-------------|-------------------|----------|
| **UI component** | BOUNDARY, STATE, ERROR | Screenshot |
| **API endpoint** | CONTRACT, PAYLOAD, TIMEOUT | Response JSON |
| **Database schema** | IDEMPOTENCY, VOLUME | Query results |
| **Configuration** | RESTART, HEALTHCHECK | Service logs |
| **MCP tool** | CONTRACT, EXIT_CODE | Tool output |

### Integration with TDD Workflow

```
TDD Cycle:
  RED (failing test)
    ↓
  GREEN (code passes)
    ↓
  REFACTOR (clean up)
    ↓
  ┌─────────────────────────────────┐
  │ RULE-028: Change Validation     │
  │   └── Re-run exploratory        │
  │   └── Check heuristics          │
  │   └── Capture evidence          │
  └─────────────────────────────────┘
    ↓
  COMPLETE (mark done)
```

### Anti-Patterns

| Pattern | Instead |
|---------|---------|
| Mark complete after unit tests only | Run exploratory validation too |
| Skip heuristics for "small" changes | Apply proportional validation |
| Trust green tests without exploration | Explore for unexpected behaviors |
| Fix test without fixing code | Investigate root cause first |
| **Declare "bug fixed" when crash stops** | **Validate full feature works E2E** |
| **Assume API changes are live** | **Restart server per RULE-027** |
| **Test only the technical fix** | **Test the user's intended workflow** |

### Validation Checklist

- [ ] Change scope identified
- [ ] Domain heuristics selected from RULE-004
- [ ] Validation suite executed
- [ ] Results documented (screenshots, logs)
- [ ] No new gaps introduced
- [ ] Task marked complete only after validation

---

*Per RULE-014: Autonomous Task Sequencing + RULE-012: DSP*

---

## RULE-027: API Server Restart Protocol

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

ALWAYS restart API servers after making code changes BEFORE running tests. This prevents false test failures from running against stale server code.

### Protocol

```
WHEN modifying API code (endpoints, models, handlers):

1. STOP existing server process
   └── Kill any uvicorn/flask/fastapi processes on target port
   └── Verify port is free

2. START fresh server instance
   └── python -m uvicorn <module>:app --port <port>
   └── Wait for "Uvicorn running" confirmation

3. VERIFY server is responsive
   └── Call /api/health or similar endpoint
   └── Confirm expected version/status

4. RUN tests
   └── Only after steps 1-3 complete
   └── Tests hit fresh server with latest code
```

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Run tests immediately after code changes | Restart server first, verify health |
| Assume hot-reload caught changes | Explicitly restart for reliability |
| Debug "404 Method Not Allowed" without checking server | Check if server has latest code |
| Keep background server running indefinitely | Restart after API modifications |

### Validation

- [ ] Server restarted after API code changes
- [ ] Health endpoint confirms server is up
- [ ] Tests pass with new endpoints

---

*Per TODO-6: Agent Task Backlog UI - discovered during E2E test development*

---

## RULE-030: Docker Dev Container Workflow

**Category:** `development` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

For UI/API development and validation, agents MUST use Docker dev containers with volume mounts instead of attempting to run local Python processes. This ensures consistent environments and enables fast prototyping with live code reloading.

### Origin

Created 2024-12-28 after attempting local Python validation instead of using the existing `governance-dashboard-dev` container. Local approach failed due to port conflicts (agents container on 7777) and missing dependencies.

### When to Use Docker Dev Containers

| Scenario | Use Docker Dev | Use Local Python |
|----------|----------------|------------------|
| **UI validation** | ✅ Yes | ❌ No |
| **API testing** | ✅ Yes | ❌ No |
| **Quick code fix validation** | ✅ Yes | ❌ No |
| **Unit tests only** | Optional | ✅ Yes |
| **Pure Python scripting** | Optional | ✅ Yes |

### Available Dev Containers

| Container | Port | Profile | Volume Mounts |
|-----------|------|---------|---------------|
| `governance-dashboard-dev` | 8081 | `dev` | `./agent`, `./governance`, `./docs`, `./evidence` |
| `governance-api` | 8082 | `cpu` | `./governance` |

### Protocol

```
WHEN validating UI/API changes:

1. CHECK if dev container is running
   └── docker ps | grep governance-dashboard-dev

2. IF not running, START with dev profile
   └── docker compose --profile dev up -d governance-dashboard-dev
   └── OR: .\deploy.ps1 -Action up -Profile dev (after GAP-DEPLOY-001 resolved)

3. IF running but stale, RESTART
   └── docker restart sim-ai-governance-dashboard-dev-1

4. WAIT for container readiness
   └── curl http://localhost:8081 (dashboard)
   └── curl http://localhost:8082/api/health (API)

5. RUN validation
   └── Use Playwright MCP for UI validation
   └── Use PowerShell for API tests

6. NEVER attempt local Python for UI/API
   └── Ports likely in use by Docker containers
   └── Dependencies may differ from container
```

### Volume Mount Benefits

```yaml
# docker-compose.yml dev service
volumes:
  - ./agent:/app/agent:ro       # UI code - live reload
  - ./governance:/app/governance:ro  # API code - live reload
  - ./docs:/app/docs:ro         # Documentation
  - ./evidence:/app/evidence:ro  # Session evidence
```

Changes to mounted directories reflect immediately in the container without rebuild.

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Run `python agent/governance_dashboard.py` locally | Use Docker dev container |
| Run `uvicorn governance.api:app` locally | Use existing API container on 8082 |
| Kill Docker containers to free ports | Use Docker for all validation |
| Rebuild image after code changes | Restart container (volumes are mounted) |

### Related

- **GAP-DEPLOY-001**: deploy.ps1 missing dev profile support
- **RULE-028**: Change Validation Protocol (use Docker for validation)
- **RULE-023**: Test Before Ship (validate in Docker environment)

### Validation

- [ ] Docker dev container used for UI/API validation
- [ ] No local Python processes for containerized services
- [ ] Container restarted after code changes (not rebuilt)
- [ ] Ports verified free before starting services

---

*Per RULE-028: Change Validation Protocol - Docker dev workflow discovered 2024-12-28*

---

## RULE-031: Autonomous Task Continuation

**Category:** `operational` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

When executing multi-step tasks, agents MUST continue working until ALL tasks are complete or an explicit halt command is received. Agents MUST NOT stop prematurely after completing intermediate steps.

### Origin

Created 2025-01-01 after observing premature termination during multi-task sessions. User feedback: "why you stopped implementing fixes for other known issues? is there a way to prevent this by tuning the rules established?"

### Continuation Requirements

| Trigger | Action |
|---------|--------|
| **Task list has pending items** | Continue to next task |
| **Error during task** | Log error, attempt recovery, continue |
| **Subtask completed** | Mark complete, start next immediately |
| **All tasks complete** | Generate summary, await further instructions |
| **Explicit halt command** | Stop immediately (see RULE-014) |

### Anti-Patterns (PROHIBITED)

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Stop after fixing one issue when more exist | Fix all issues in sequence |
| Summarize and wait after partial completion | Continue until todo list is empty |
| Ask "should I continue?" after each step | Continue autonomously per RULE-014 |
| Skip pending tasks without explicit instruction | Complete all pending tasks |

### Task Tracking Requirements

```
WHEN working on multi-step tasks:

1. BEFORE starting
   └── Create todo list with ALL known tasks
   └── Set first task to "in_progress"

2. DURING execution
   └── Mark task "completed" IMMEDIATELY after finishing
   └── Set next task to "in_progress" WITHOUT pausing
   └── Add new discovered tasks to list as needed

3. ONLY STOP when:
   └── All tasks marked "completed"
   └── Explicit halt command received (STOP, HALT, STAI, RED ALERT)
   └── Context limit approaching (then summarize and continue in new session)

4. NEVER stop when:
   └── Todo list has pending items
   └── Intermediate step completed successfully
   └── User hasn't responded (continue working)
```

### Integration with Other Rules

| Rule | Relationship |
|------|--------------|
| **RULE-014** | Halt commands override continuation |
| **RULE-012** | DSP cycles are atomic units of work |
| **RULE-030** | Autonomous execution requirement |
| **RULE-024** | Context recovery enables multi-session continuation |

### Enforcement

- [ ] Todo list maintained throughout session
- [ ] No premature stops with pending tasks
- [ ] Explicit "all tasks complete" message when done
- [ ] Halt only on explicit command or context limit

### Metrics

Track and report:
- Tasks completed per session
- Premature stop incidents (should be 0)
- Continuation chains across context limits

---

*Per user feedback 2025-01-01: Agents must not stop until all tasks complete*
