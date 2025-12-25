# Operational Rules - Sim.ai

Rules governing testing, stability, maintenance, and task execution.

---

## RULE-004: Exploratory Test Automation & Executable Specification

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All components MUST be testable via domain-specific heuristics. Exploratory testing complements TDD cycle to ensure proper coverage and evidence capture for audit.

### Test Strategy Integration

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

## RULE-020: LLM-Driven E2E Test Generation

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

E2E tests MUST be generated via LLM-driven exploratory sessions using Playwright MCP. LLM is used ONLY for:
1. **Exploration phase** - Discover UI paths via heuristics
2. **Test generation** - Convert exploration to deterministic Robot Framework tests
3. **Failure analysis** - Analyze why deterministic tests failed

LLM is NOT used during test execution.

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
│  Level 2: SESSION START CHECK                                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  At session initialization:                                     │    │
│  │     └── Run full MCP health audit                               │    │
│  │     └── Count active vs expected servers                        │    │
│  │     └── Log to session evidence                                 │    │
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

*Per RULE-014: Autonomous Task Sequencing + RULE-012: DSP*
