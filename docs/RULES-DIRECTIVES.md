# Sim.ai Rules Directives

## Overview

This document defines mandatory rules for the Sim.ai PoC agent platform.
Rules are indexed in ChromaDB (`sim_ai_rules` collection) and enforced by agents.

**Quick Reference:** 13 active rules (12 ACTIVE, 1 DRAFT), 9 categories, automated enforcement via pre-commit + CI/CD.

---

## Rules Summary

| Rule | Category | Priority | Status | Enforcement |
|------|----------|----------|--------|-------------|
| RULE-001 | governance | CRITICAL | ACTIVE | Session logs required |
| RULE-002 | architecture | HIGH | ACTIVE | Code review |
| RULE-003 | governance | HIGH | DRAFT | Sync agent |
| RULE-004 | testing | HIGH | ACTIVE | Playwright MCP |
| RULE-005 | stability | HIGH | ACTIVE | Memory thresholds |
| RULE-006 | governance | MEDIUM | ACTIVE | Decision logging |
| RULE-007 | productivity | HIGH | ACTIVE | MCP Usage Protocol |
| RULE-008 | strategic | CRITICAL | ACTIVE | Technology scorecard |
| RULE-009 | devops | CRITICAL | ACTIVE | Version compatibility |
| RULE-010 | strategic | CRITICAL | ACTIVE | Evidence-based wisdom |
| RULE-011 | governance | CRITICAL | ACTIVE | Multi-agent governance |
| RULE-012 | maintenance | HIGH | ACTIVE | Deep Sleep Protocol (DSP) |
| RULE-013 | governance | HIGH | ACTIVE | Rules Applicability Convention |

---

## Rule Categories

| Category | Priority | Enforcement |
|----------|----------|-------------|
| `governance` | CRITICAL | Mandatory |
| `architecture` | HIGH | Mandatory |
| `testing` | HIGH | Mandatory |
| `observability` | HIGH | Mandatory |
| `security` | HIGH | Mandatory |
| `performance` | MEDIUM | Advisory |

---

## RULE-001: Session Evidence Logging

**Category:** `governance`  
**Priority:** CRITICAL  
**Status:** ACTIVE  
**Effectiveness Score:** N/A (new)

### Directive

All agent sessions MUST produce evidence logs that include:

1. **Thought Chain Documentation**
   - Every decision point with rationale
   - Alternatives considered and why rejected
   - Assumptions made and their basis

2. **Artifact Tracking**
   - Files created/modified with timestamps
   - Dependencies introduced
   - Configuration changes

3. **Session Metadata**
   - Session ID, start/end times
   - Models invoked with token counts
   - Tools used with invocation counts

4. **Export Requirements**
   - Session logs exported to `./docs/SESSION-{date}-{topic}.md`
   - Machine-readable YAML metadata block
   - Human-readable narrative

### Implementation

```python
# Session logging structure
session_log = {
    "session_id": str,
    "timestamp": datetime,
    "thought_chain": [
        {
            "step": int,
            "decision": str,
            "rationale": str,
            "alternatives": list[str],
            "confidence": float  # 0-1
        }
    ],
    "artifacts": [
        {
            "path": str,
            "action": "create|modify|delete",
            "timestamp": datetime
        }
    ],
    "metadata": {
        "models": dict,
        "tools": dict,
        "tokens": int
    }
}
```

### Validation

- [ ] Session log exists in `./docs/`
- [ ] Contains thought chain with ≥3 decision points
- [ ] Metadata block is valid YAML
- [ ] All artifacts are tracked

---

## RULE-002: Architectural & Design Best Practices

**Category:** `architecture`  
**Priority:** HIGH  
**Status:** ACTIVE  
**Effectiveness Score:** N/A (new)

### Directive

All code and system design MUST follow:

1. **Separation of Concerns**
   - Each component has single responsibility
   - Clear boundaries between layers (Agent, Routing, Storage, Observability)
   - No circular dependencies

2. **Configuration Over Code**
   - Environment variables for secrets and endpoints
   - YAML/JSON for model configurations
   - No hardcoded values in source

3. **Observability by Default**
   - Health endpoints for every service
   - Structured logging (JSON format)
   - Session dumps via `scripts/session_dump.py`

4. **Graceful Degradation**
   - Fallback models configured in LiteLLM
   - Service health checks with retries
   - Timeout handling for all external calls

5. **Idempotency**
   - Agent operations should be safely retriable
   - Database operations use upsert patterns
   - No side effects on read operations

6. **Documentation**
   - README for every component
   - Inline comments for non-obvious logic
   - API contracts documented

### Implementation Checklist

```yaml
architectural_compliance:
  separation_of_concerns:
    - agent_layer_isolated: true
    - routing_layer_isolated: true
    - storage_layer_isolated: true
  configuration:
    - secrets_in_env: true
    - no_hardcoded_urls: true
    - yaml_configs_validated: true
  observability:
    - health_endpoints_exist: true
    - structured_logging: true
    - session_dumps_enabled: true
  degradation:
    - fallback_models_configured: true
    - timeouts_configured: true
    - retries_implemented: true
```

### Validation

- [ ] No circular imports detected
- [ ] All secrets in `.env` (not in code)
- [ ] Health endpoint returns 200
- [ ] Session dump created (`scripts/session_dump.py`)

---

## RULE-003: Sync Protocol for Skills & Sessions

**Category:** `governance`  
**Priority:** HIGH  
**Status:** DRAFT  
**Effectiveness Score:** N/A (new)

### Directive

Local skills and sessions MUST be syncable to:
- Remote storage (optional cloud backup)
- Team shared repositories
- Cross-device continuity

### Sync Agent Design

See `./docs/SYNC-AGENT-DESIGN.md` for implementation.

---

## RULE-004: Exploratory Test Automation with Playwright MCP

**Category:** `testing`  
**Priority:** HIGH  
**Status:** ACTIVE  
**Effectiveness Score:** N/A (new)

### Directive

All UI/web components MUST be testable via Playwright MCP with custom heuristics:

1. **Exploratory Testing Protocol**
   - Use Playwright MCP for browser automation
   - Apply heuristic-based exploration (not just scripted tests)
   - Document findings as evidence in session logs

2. **Test Automation Heuristics**
   | Heuristic | Description | Priority |
   |-----------|-------------|----------|
   | `BOUNDARY` | Test edge cases, limits, empty states | HIGH |
   | `NAVIGATION` | Verify all links, routes, redirects | HIGH |
   | `STATE` | Check state transitions, persistence | MEDIUM |
   | `ERROR` | Trigger and verify error handling | HIGH |
   | `ACCESSIBILITY` | Check a11y compliance | MEDIUM |
   | `PERFORMANCE` | Measure load times, responsiveness | LOW |

3. **MCP Integration**
   - Configure Playwright MCP in IDE (`mcp_config.json`)
   - Use headless mode for CI, headed for debugging
   - Capture screenshots on failures

4. **Evidence Requirements**
   - Screenshot of each tested state
   - Console logs for errors
   - Network requests for API calls
   - Accessibility audit results

### MCP Configuration (Windsurf)

```json
{
  "playwright": {
    "command": "npx",
    "args": [
      "-y",
      "@playwright/mcp@latest",
      "--headless",
      "--output-dir",
      "C:\\Users\\natik\\Documents\\Vibe\\mcp_trials\\.artifacts\\playwright",
      "--save-trace"
    ]
  }
}
```

**Evidence Output:** `C:\Users\natik\Documents\Vibe\mcp_trials\.artifacts\playwright`

### Playwright MCP Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URL |
| `browser_screenshot` | Capture current state |
| `browser_click` | Click element |
| `browser_fill` | Fill form field |
| `browser_evaluate` | Run JavaScript |
| `browser_console` | Get console logs |

### Implementation Workflow

```
1. Navigate to target URL
2. Apply BOUNDARY heuristic (test limits)
3. Apply NAVIGATION heuristic (check links)
4. Apply ERROR heuristic (trigger failures)
5. Capture screenshots as evidence
6. Document findings in session log
```

### Validation

- [ ] Playwright MCP configured in IDE
- [ ] At least 3 heuristics applied per test session
- [ ] Screenshots captured for each state
- [ ] Findings documented in session log

---

## RULE-005: Memory & MCP Stability

**Category:** `stability`  
**Priority:** HIGH  
**Status:** ACTIVE  
**Source:** AngelGAI + LocalGAI (production-proven)

### Directive

All MCP operations MUST respect memory thresholds and stability tiers.

### Memory Thresholds

| Memory | Status | Action |
|--------|--------|--------|
| < 500 MB | HEALTHY | Normal operation |
| 500-1000 MB | NORMAL | Active development |
| 1000-1500 MB | WARNING | Monitor closely |
| 1500-2000 MB | HIGH | Consider closing files |
| > 2000 MB | CRITICAL | Restart soon |
| > 3000 MB | EMERGENCY | Restart immediately |

### MCP Stability Tiers (Updated 2024-12-24)

| Tier | MCPs | Risk | Usage |
|------|------|------|-------|
| **STABLE** | claude-mem, sequential-thinking, filesystem, git | LOW | ✅ Always use |
| **PRODUCTIVE** | octocode, powershell, llm-sandbox | LOW | ✅ Use for research/automation |
| **MODERATE** | desktop-commander, playwright | MEDIUM | ✅ Use with monitoring |
| **CONDITIONAL** | godot-mcp | MEDIUM | ⚠️ Requires Godot editor |

### Approved MCPs (Verified Working - 2024-12-24)

```
✅ claude-mem         - Memory persistence (53 docs in ChromaDB)
✅ octocode           - GitHub code search (GITHUB_PAT configured)
✅ sequential-thinking - Chain-of-thought reasoning
✅ playwright         - Browser automation
✅ desktop-commander  - File/process operations
✅ filesystem         - File system operations
✅ git                - Version control
✅ powershell         - Windows automation
✅ llm-sandbox        - Code execution sandbox
⚠️ godot-mcp         - Requires Godot editor running
```

### Process Leak Detection

```powershell
# Check node process count
(Get-Process node -EA SilentlyContinue).Count

# Thresholds:
# 1-3: HEALTHY
# 4-7: NORMAL
# 8-10: WARNING
# >10: LEAK - Kill and restart
```

### Recovery Levels

1. **Soft**: Restart Cascade/Claude Code
2. **Medium**: Disable heavy MCPs
3. **Hard**: Kill node processes
4. **Nuclear**: Full system restart

### Validation

- [ ] Memory stays below 2GB during normal operation
- [ ] Node process count < 10
- [ ] No MCP timeouts > 30 seconds
- [ ] Recovery script available

---

## Rule Index (ChromaDB Schema)

```json
{
  "collection": "sim_ai_rules",
  "schema": {
    "id": "rule_{number}",
    "document": "Full rule text",
    "metadata": {
      "category": "string",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "status": "ACTIVE|DRAFT|DEPRECATED",
      "effectiveness_score": "float 0-1",
      "created_at": "ISO datetime",
      "updated_at": "ISO datetime",
      "version": "semver"
    }
  }
}
```

---

## RULE-006: Decision Logging

**Category:** `governance`  
**Priority:** MEDIUM  
**Status:** ACTIVE  
**Source:** Session audit 2024-12-24

### Directive

All strategic decisions MUST be logged in task system, not just chat.

### Problem Statement

Decisions made during sessions often get lost because:
- Logged only in chat history (not persistent)
- No structured format for retrieval
- Hard to track what was decided vs discussed
- LLM cannot find prior decisions

### Requirements

Every session MUST log decisions in:

1. **`evidence/SESSION-DECISIONS-{date}.md`** - Decision audit trail
2. **`TODO.md`** - Add DECISION-XXX entries for major decisions

### Decision Log Format

```markdown
## DECISION-XXX: [Title]

**Date:** YYYY-MM-DD  
**Context:** [Why this decision was needed]  
**Options Considered:**
1. Option A - [pros/cons]
2. Option B - [pros/cons]

**Decision:** [What was decided]  
**Rationale:** [Why this option]  
**Action:** [What was done / to be done]  
**Status:** IMPLEMENTED | PENDING | DEFERRED
```

### Validation

- [ ] Session ends with decision audit
- [ ] Major decisions have DECISION-XXX entry
- [ ] evidence/SESSION-DECISIONS-*.md exists
- [ ] Decisions are actionable (not just discussion)

---

## RULE-007: MCP Usage Protocol

**Category:** `productivity`
**Priority:** HIGH
**Status:** ACTIVE
**Source:** Session audit 2024-12-24 (Claude Code setup)

### Directive

All sessions MUST actively leverage available MCPs according to task type.
MCPs are tools - they provide value only when invoked.

### Problem Statement

Session audit revealed MCPs were available but underutilized:
- claude-mem: 53 docs existed but weren't queried for context
- octocode: GitHub research done manually instead of via MCP
- sequential-thinking: Complex decisions made without structured reasoning
- playwright: UI endpoints not visually tested

### MCP Usage Matrix

| Task Type | Required MCPs | Optional MCPs |
|-----------|---------------|---------------|
| **Session Start** | claude-mem (context), filesystem | sequential-thinking |
| **Code Research** | octocode, filesystem | claude-mem |
| **Implementation** | filesystem, powershell | llm-sandbox, git |
| **Testing** | playwright, powershell | desktop-commander |
| **Complex Analysis** | sequential-thinking | claude-mem |
| **Documentation** | filesystem, git | claude-mem |

### Session Start Protocol (Updated)

Before starting work, MUST execute:

```
1. Query claude-mem for project context:
   mcp__claude-mem__chroma_query_documents(
     collection_name="claude_memories",
     query_texts=["sim-ai project context recent decisions"]
   )

2. Check for relevant prior decisions:
   mcp__claude-mem__chroma_query_documents(
     collection_name="claude_memories",
     query_texts=["sim-ai DECISION architecture"]
   )

3. For code research, use octocode:
   mcp__octocode__githubSearchCode(queries=[...])
```

### MCP Invocation Checklist

At session start, verify these MCPs are considered:

| MCP | Check | When to Use |
|-----|-------|-------------|
| **claude-mem** | ☐ Queried for context? | Always - 53+ docs available |
| **octocode** | ☐ GitHub research needed? | Code patterns, library usage |
| **sequential-thinking** | ☐ Complex decision? | Architecture, multi-step analysis |
| **playwright** | ☐ UI to test? | Web endpoints, visual verification |
| **powershell** | ☐ System commands? | Windows automation, env loading |
| **llm-sandbox** | ☐ Code to isolate? | Untrusted code, experiments |

### Active MCPs Reference

| MCP | Purpose | Invocation Pattern |
|-----|---------|-------------------|
| **claude-mem** | Memory persistence | `chroma_query_documents`, `chroma_add_documents` |
| **octocode** | GitHub code search | `githubSearchCode`, `githubGetFileContent` |
| **playwright** | Browser automation | `browser_navigate`, `browser_snapshot` |
| **sequential-thinking** | Structured reasoning | `sequentialthinking` |
| **desktop-commander** | File/process ops | `read_file`, `write_file`, `start_process` |
| **filesystem** | File operations | `read_file`, `write_file`, `list_directory` |
| **git** | Version control | `git_status`, `git_commit`, `git_diff` |
| **powershell** | Windows automation | `run_powershell` |
| **llm-sandbox** | Code execution | `execute_code` |

### Usage Metrics (Track per Session)

```yaml
mcp_usage:
  claude_mem_queries: 0      # Target: ≥1 per session
  octocode_searches: 0       # Target: ≥1 for research tasks
  sequential_thinking: 0     # Target: ≥1 for complex decisions
  playwright_tests: 0        # Target: ≥1 for UI tasks
  total_mcp_invocations: 0   # Track overall usage
```

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Manual GitHub search | Use octocode MCP |
| Copy-paste context | Query claude-mem |
| Ad-hoc decisions | Use sequential-thinking |
| Bash for file ops | Use filesystem MCP |
| Skipping memory check | Always query claude-mem first |

### Validation

- [ ] Session starts with claude-mem context query
- [ ] Research tasks use octocode (not manual search)
- [ ] Complex decisions use sequential-thinking
- [ ] UI testing uses playwright
- [ ] MCP usage logged in session evidence

---

## RULE-008: In-House Rewrite Principle

**Category:** `strategic`
**Priority:** CRITICAL
**Status:** ACTIVE
**Source:** Session 2024-12-24 (TypeDB decision research)

### Directive

When selecting external technologies for strategic components, ALWAYS prefer solutions that:
1. Have comprehensive test suites (warranty for in-house rewrite)
2. Are open-source with permissive or copyleft licenses
3. Have active development and community
4. Can be ported/rewritten in-house if needed

### Rationale

External dependencies are risks. Tests are warranties:
- If a solution has tests, we can understand its behavior
- Tests serve as specifications for an in-house rewrite
- We're not locked into vendor decisions
- Enterprise clients may require in-house solutions

### Evaluation Criteria

| Criterion | Weight | What to Check |
|-----------|--------|---------------|
| **Test Coverage** | CRITICAL | Does it have comprehensive tests? |
| **License** | HIGH | Open source? Apache/MIT/AGPL? |
| **Activity** | HIGH | Recent commits? Active PRs? |
| **Documentation** | MEDIUM | API docs? Examples? |
| **Community** | MEDIUM | Issues addressed? Discussions? |
| **Rewrite Path** | HIGH | Clear architecture? Modular? |

### Technology Selection Scorecard

Before adopting any strategic technology, complete this scorecard:

```yaml
technology_evaluation:
  name: "<technology>"
  purpose: "<what it solves>"

  scores:  # 1-5 scale
    test_coverage: 0      # Does it have tests?
    license_freedom: 0    # Can we fork/rewrite?
    active_development: 0 # Recent activity?
    documentation: 0      # Can we understand it?
    rewrite_feasibility: 0 # Could we build it ourselves?

  total_score: 0  # Sum of above (max 25)
  recommendation: "ADOPT | EVALUATE | REJECT"

  notes: |
    <reasoning for scores>
```

### Example: TypeDB Evaluation

```yaml
technology_evaluation:
  name: "TypeDB"
  purpose: "Graph DB with inference engine for knowledge reasoning"

  scores:
    test_coverage: 5      # typedb-behaviour repo, extensive tests
    license_freedom: 4    # AGPL-3.0 (copyleft, but open)
    active_development: 5 # Pushed Dec 2024, active issues
    documentation: 4      # Good docs, TypeQL reference
    rewrite_feasibility: 3 # Complex but modular architecture

  total_score: 21  # Strong candidate
  recommendation: "ADOPT"

  notes: |
    - 4,153 stars, active community
    - Native inference (not external plugin)
    - TypeDB-behaviour repo = clear test specifications
    - Python/Java/Rust drivers available
    - AGPL requires open-source derivatives
```

### Comparison: Graph DBs with Inference

| Database | Stars | Inference | License | Tests | Rewrite Score |
|----------|-------|-----------|---------|-------|---------------|
| **TypeDB** | 4,153 | ✅ Native | AGPL-3.0 | ✅ Extensive | **21/25** |
| **Dgraph** | 21,423 | ❌ Limited | Apache-2.0 | ✅ Yes | 18/25 |
| **Apache Jena** | 1,261 | ✅ OWL/RDFS | Apache-2.0 | ✅ Yes | 17/25 |
| **Blazegraph** | 973 | ✅ External | GPL-2.0 | ⚠️ Older | 14/25 |
| **Neo4j** | 13K+ | ❌ None | Mixed | ✅ Yes | 15/25 |
| **Stardog** | - | ✅ Yes | Commercial | - | **REJECT** |
| **GraphDB** | - | ✅ OWL | Commercial | - | **REJECT** |

### Validation

- [ ] Technology scorecard completed before adoption
- [ ] Test suite reviewed and understood
- [ ] License verified compatible with enterprise use
- [ ] Rewrite path documented if critical component
- [ ] OctoCode research performed (not just web search)

---

## RULE-009: DevOps Version Compatibility Protocol

**Category:** `devops`
**Priority:** CRITICAL
**Status:** ACTIVE
**Source:** Session 2024-12-24 (TypeDB version mismatch incident)

### Directive

Before installing ANY package, container, or dependency:
1. **Check container/service version FIRST** (docker logs, --version)
2. **Use OctoCode to find compatible client versions**
3. **Use llm-sandbox or isolated env for testing** (never pollute global Python)
4. **Verify version matrix** (client vs server compatibility)

### The Mistake That Created This Rule

```
WRONG: pip install typedb-driver  # Blindly install latest
RIGHT:
  1. docker logs sim-ai-typedb-1 | grep version  # → 2.29.1
  2. OctoCode: find compatible Python client for TypeDB 2.29.x
  3. pip install typedb-client==2.18.2  # Matched version
```

### Version Check Protocol

| Step | Tool | Command |
|------|------|---------|
| 1. Container version | Bash/PowerShell | `docker logs <container> \| grep version` |
| 2. Client compatibility | OctoCode | Search repo for version matrix/requirements |
| 3. Isolated testing | llm-sandbox | Test import/connection before global install |
| 4. Dependency conflicts | pip | `pip check` after install |

### MCP Usage for DevOps

| Task | Use This MCP | NOT This |
|------|--------------|----------|
| Check versions | powershell, Bash | Manual typing |
| Find compatible packages | OctoCode | Web search guess |
| Test Python imports | llm-sandbox | Global Python |
| Container inspection | desktop-commander | Manual docker |

### Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|--------------|-------------|------------------|
| `pip install <pkg>` without version | Version mismatch | Check server version first |
| Installing to global Python | Dependency conflicts | Use venv or llm-sandbox |
| Guessing package names | Wrong package | OctoCode search |
| Skipping `pip check` | Silent breaks | Always verify after install |

### Validation

- [ ] Container version checked before client install
- [ ] OctoCode used to find version compatibility
- [ ] llm-sandbox used for isolated testing
- [ ] `pip check` run after any install
- [ ] No global Python pollution for experiments

---

## RULE-010: Evidence-Based Wisdom Accumulation

**Category:** `strategic`
**Priority:** CRITICAL
**Status:** ACTIVE
**Source:** Session 2024-12-24 (MCP usage philosophy)

### Directive

Every experiment, decision, and action MUST produce traceable evidence that contributes to accumulated wisdom:

1. **Use MCPs for detailed evidence** - MCPs provide structured, queryable output that feeds evidence pipelines
2. **Hypothesis-based approach** - Form hypothesis → test → collect evidence → validate/refute
3. **Logical decision making** - Decisions based on facts, not assumptions
4. **Multiplier effect** - Each experiment multiplies wisdom (or exposes stupidity via tests)
5. **Test-caught failures** - Failed hypotheses caught by tests are learning opportunities

### Evidence Pipeline

```
MCP Output → Evidence Collection → Logical Analysis → Decision → TypeDB Rule
     ↓              ↓                    ↓               ↓           ↓
Structured   ChromaDB Memory      Hypothesis Test    DECISION-xxx   Inference
  Data        (claude-mem)         (pytest)          Documented    Available
```

### The Wisdom Accumulation Principle

```
Wisdom = Σ(Evidence × Validation)
Stupidity = Σ(Assumptions × Untested)

As platform grows:
- Each validated experiment → multiplies wisdom
- Each untested assumption → accumulates technical debt
- Tests catch stupidity early → prevents debt multiplication
```

### MCP Usage for Evidence

| Evidence Type | MCP Tool | Output |
|---------------|----------|--------|
| API exploration | llm-sandbox | Structured Python output |
| Version checks | powershell | Package/container versions |
| Code patterns | OctoCode | GitHub search results |
| File operations | desktop-commander | Detailed file metadata |
| Memory storage | claude-mem | ChromaDB documents |

### Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|--------------|-------------|------------------|
| Manual typing instead of MCP | No evidence trail | Use MCPs for all operations |
| Skip hypothesis validation | Untested assumptions | Write tests for hypotheses |
| Ad-hoc decisions | No rationale | Document in DECISION-xxx |
| Ignoring test failures | Stupidity multiplies | Fix tests immediately |

### Integration Points

- **Memory (claude-mem)**: Store evidence documents with metadata
- **Governance (TypeDB)**: Encode validated rules for inference
- **Documentation (./docs)**: Human-readable decision logs
- **GitHub Issues**: Track gaps and R&D progress

### Validation

- [ ] MCPs used instead of manual operations
- [ ] Hypothesis documented before testing
- [ ] Evidence collected in structured format
- [ ] Failed tests investigated (not ignored)
- [ ] Successful patterns encoded as rules

---

## RULE-011: Multi-Agent Governance Protocol

**Category:** `governance`
**Priority:** CRITICAL
**Status:** ACTIVE
**Source:** Session 2024-12-24 (AI governance best practices research)

### Directive

Multi-agent systems MUST implement structured governance with human oversight, consensus mechanisms, and evidence-based conflict resolution.

### Governance Layers (Bicameral Model)

```
┌─────────────────────────────────────────────────────────────────────┐
│ UPPER CHAMBER (Human Oversight)                                      │
│ - Veto authority on rule changes                                    │
│ - Strategic steering and prioritization                             │
│ - Ambiguity resolution when AI cannot decide                        │
│ - Budget and resource allocation                                    │
├─────────────────────────────────────────────────────────────────────┤
│ LOWER CHAMBER (AI Execution)                                         │
│ - Task execution from TypeDB queue                                  │
│ - Evidence collection and hypothesis testing                        │
│ - Peer review and consensus voting                                  │
│ - Trust scoring and compliance tracking                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Governance MCP Responsibilities

The Governance MCP manages DB state and provides:

| Tool | Responsibility |
|------|----------------|
| `governance_propose_rule` | Submit rule changes with evidence |
| `governance_vote` | Peer review voting on proposals |
| `governance_dispute` | Raise conflicts for resolution |
| `governance_resolve_conflict` | Evidence-based conflict resolution |
| `governance_get_trust_score` | Agent reliability scoring |
| `governance_sync_state` | Bidirectional sync protocol |
| `governance_escalate_to_human` | Trigger human oversight |

### Conflict Resolution Protocol

```
1. DETECT: TypeDB inference identifies conflict
   └─> Priority, semantic, or dependency conflict

2. ANALYZE: Hypothesis-based assessment (RULE-010)
   ├─> Evidence weight scoring
   ├─> Semantic clarity analysis
   └─> Trust score weighting

3. PEER REVIEW: Agents vote on resolution
   ├─> Weighted by trust score
   ├─> Quorum: 2+ agents
   └─> Threshold: 80% weighted approval

4. HUMAN ESCALATION (if needed):
   ├─> Deadlock (50/50 split)
   ├─> Strategic impact (affects CRITICAL rules)
   ├─> Trust deficit (all agents < 0.70)
   └─> Explicit ambiguity detected

5. RESOLVE: Update TypeDB, propagate to all agents
   └─> Log evidence trail, update trust scores
```

### Human Escalation Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| **VETO** | Human explicitly blocks | Proposal rejected, logged |
| **STEER** | Strategic direction needed | Human chooses from options |
| **AMBIGUITY** | Multiple valid interpretations | Human selects interpretation |
| **DEADLOCK** | Agents cannot reach consensus | Human breaks tie |
| **CRITICAL** | Affects CRITICAL priority rule | Human approval required |

### Trust Score Algorithm

```python
Trust = (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

Where:
- Compliance: % of rules followed
- Accuracy: % of predictions validated
- Consistency: 1 - variance(behavior)
- Tenure: min(1.0, days_active / 365)
```

### Sync Protocol

```
LOCAL (Claude Code)          GOVERNANCE MCP          SERVER (Docker)
      │                            │                       │
      │──propose_rule──────────────>│                       │
      │                            │──validate_conflict────>│
      │                            │<─────vote─────────────│
      │<────vote_request───────────│                       │
      │─────vote───────────────────>│                       │
      │                            │──calculate_consensus──│
      │                            │                       │
      │                     [IF CONSENSUS]                 │
      │                            │──update_typedb───────>│
      │<────sync_state─────────────│<──sync_state─────────│
      │                            │                       │
      │                     [IF ESCALATE]                  │
      │                            │──notify_human────────>│
      │                            │<─────decision────────│
      │<────resolution─────────────│──────resolution─────>│
```

### Best Practices Applied

Based on research (arxiv.org/html/2508.18765v2, arxiv.org/html/2501.06322v1):

1. **Governance-as-a-Service**: Modular policy enforcement without modifying agent logic
2. **Trust Factor Mechanism**: Longitudinal compliance and severity-aware history
3. **Rule-Based Consensus**: Efficiency and predictability over ad-hoc negotiation
4. **Debate Protocols**: Argumentative exchanges for complex conflicts
5. **Communication Standards**: MCP as protocol with embedded governance guarantees

### Validation

- [ ] Governance MCP server implemented
- [ ] TypeDB schema extended (agent, proposal, vote, dispute)
- [ ] Conflict detection inference rules active
- [ ] Trust scoring algorithm operational
- [ ] Human escalation workflow tested
- [ ] Sync protocol verified bidirectional

### References

- [Governance-as-a-Service Framework](https://arxiv.org/html/2508.18765v2)
- [Multi-Agent Collaboration Mechanisms](https://arxiv.org/html/2501.06322v1)
- [Multi-Agent Risks from Advanced AI](https://arxiv.org/abs/2502.14143)
- [Anthropic MCP Protocol](https://modelcontextprotocol.io/)
- RULE-010: Evidence-Based Wisdom Accumulation
- Bicameral Governance Model (claude-mem: gov_bicameral_model)

---

## RULE-012: Deep Sleep Protocol (DSP)

**Category:** `maintenance`
**Priority:** HIGH
**Status:** ACTIVE
**Source:** Session 2024-12-24 (localgai DSM protocol adaptation)

### Directive

Periodically invoke **Deep Sleep Protocol (DSP)** for deliberate technical backlog hygiene, separate from aggressive business navigation.

### What DSP Is

DSP is a methodical, deliberate process for maintaining technical quality:
- **Not** rushing toward business goals
- **Not** reactive firefighting
- **Is** systematic cleanup and hygiene
- **Is** entropy prevention

### DSP Phases

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE
```

| Phase | Purpose | Actions |
|-------|---------|---------|
| **AUDIT** | Inventory gaps, debt, orphans | Scan TODO.md, TypeDB for stale items |
| **HYPOTHESIZE** | Form improvement theories | Propose rule/decision changes |
| **MEASURE** | Quantify current state | Run tests, check metrics, count orphans |
| **OPTIMIZE** | Apply improvements | Update TypeDB, clean backlog, archive completed |
| **VALIDATE** | Verify improvements | Run full test suite, verify no regressions |

### When to Invoke DSP

| Trigger | Scope | Cadence |
|---------|-------|---------|
| **Session End** | Quick audit of new gaps | Every session (5 min) |
| **Milestone** | Full backlog hygiene | Weekly or per milestone (30 min) |
| **Pre-Release** | Deep technical review | Before major releases (2+ hours) |
| **Entropy Alert** | Orphan detection | When TypeDB inference detects issues |

### Quick DSP Checklist (Session End)

```markdown
## DSP Quick Audit

- [ ] New gaps added to TODO.md?
- [ ] Decisions logged in evidence/?
- [ ] Tests still passing?
- [ ] No orphan rules created?
- [ ] Session log completed?
```

### Full DSP Checklist (Milestone)

```markdown
## DSP Full Audit

### AUDIT
- [ ] Count open gaps in TODO.md
- [ ] Check for stale items (>30 days)
- [ ] Identify orphan rules (no references)
- [ ] Scan for TODO(RULE-XXX) compliance

### HYPOTHESIZE
- [ ] Propose cleanup actions
- [ ] Identify consolidation opportunities
- [ ] Draft deprecation list

### MEASURE
- [ ] Run pytest tests/
- [ ] Check TypeDB entity counts
- [ ] Verify ChromaDB doc counts

### OPTIMIZE
- [ ] Archive completed tasks
- [ ] Close resolved gaps
- [ ] Update deprecated rules
- [ ] Clean TODO.md

### VALIDATE
- [ ] All tests pass
- [ ] No regression introduced
- [ ] Documentation updated
```

### DSP vs Business Navigation

| Aspect | DSP (Deep Sleep) | Business Navigation |
|--------|------------------|---------------------|
| **Pace** | Deliberate, methodical | Aggressive, fast |
| **Focus** | Technical debt, backlog | Feature delivery |
| **Scope** | Cleanup, hygiene | New functionality |
| **Evidence** | Audit trails | User stories |
| **Outcome** | Reduced entropy | Customer value |

### Validation

- [ ] DSP quick audit at each session end
- [ ] DSP full audit at each milestone
- [ ] Entropy metrics tracked (gap count, orphan count)
- [ ] No stale items > 30 days without review

---

## RULE-013: Rules Applicability Convention

**Category:** `governance`
**Priority:** HIGH
**Status:** ACTIVE
**Source:** Session 2024-12-24 (strategic vision analysis)

### Directive

All code comments, gaps, and TODOs MUST reference applicable governance rules using a consistent meta-reference format.

### Problem Statement

Code gaps and TODOs lack traceability:
- `# TODO: Fix this later` - No rule reference
- Gaps in TODO.md don't link to enforcing rules
- Hard to audit rule compliance across codebase
- Orphan gaps with no governance context

### Meta-Reference Format

```
{TYPE}({RULE-ID}): {Description}

Where:
- TYPE: TODO | FIXME | GAP-XXX | HACK | NOTE
- RULE-ID: RULE-001 through RULE-0XX (or DECISION-XXX)
- Description: Actionable statement
```

### Examples

```python
# Good - with rule reference
# TODO(RULE-002): Extract to separate module for separation of concerns
# FIXME(RULE-009): Version mismatch - check container version first
# GAP-020(RULE-005): Memory threshold exceeded, add monitoring
# HACK(RULE-002): Temporary workaround until refactor

# Bad - no rule reference
# TODO: Fix this later
# FIXME: This is broken
# HACK: Don't ask why
```

### Gap Format in TODO.md

```markdown
| ID | Gap | Priority | Category | Rule |
|----|-----|----------|----------|------|
| GAP-020 | Memory monitoring | HIGH | stability | RULE-005 |
| GAP-021 | Session template | MEDIUM | governance | RULE-001 |
```

### TypeDB Integration

Gaps and rules are cross-referenced:

```typeql
# Gap entity with rule reference
gap sub entity,
    owns gap-id,
    owns description,
    owns location,      # file:line or doc:section
    owns status,
    plays gap-rule-reference:referenced-gap;

gap-rule-reference sub relation,
    relates referenced-gap,
    relates governing-rule;

rule-entity plays gap-rule-reference:governing-rule;
```

### Inference Benefits

With proper meta-referencing, TypeDB can infer:
- **Orphan gaps**: Gaps with no rule reference
- **Rule coverage**: Which rules have active gaps
- **Compliance debt**: Gaps blocking rule enforcement
- **Priority cascade**: High-priority rule → high-priority gap

### Validation

- [ ] All TODO comments have RULE-XXX reference
- [ ] Gaps in TODO.md have Rule column populated
- [ ] No orphan gaps in codebase (grep for `TODO:` without RULE)
- [ ] TypeDB gap-rule-reference populated

### Enforcement

```bash
# Find orphan TODOs (no rule reference)
grep -rn "TODO:" --include="*.py" | grep -v "RULE-"

# Count compliant vs non-compliant
grep -c "TODO(RULE-" *.py  # Compliant
grep -c "TODO:" *.py        # Total
```

---

## Enforcement

Rules are enforced via:
1. **Pre-commit hooks** - Static validation
2. **CI/CD checks** - Test suite includes rule compliance
3. **Runtime guards** - Agent checks rules before execution
4. **Session dumps** - Track decisions and gaps

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2024-12-24 | Initial rules: Session Evidence, Architecture |
| 0.2.0 | 2024-12-24 | Added RULE-004: Exploratory Test Automation with Playwright MCP |
| 0.3.0 | 2024-12-24 | Added RULE-005: Memory & MCP Stability (from AngelGAI/LocalGAI) |
| 0.4.0 | 2024-12-24 | Added RULE-006: Decision Logging (from session audit) |
| 0.5.0 | 2024-12-24 | Added RULE-007: MCP Usage Protocol (from Claude Code session audit) |
| 0.5.1 | 2024-12-24 | Updated RULE-005: MCP tiers to reflect 10 active MCPs |
| 0.6.0 | 2024-12-24 | Added RULE-008: In-House Rewrite Principle (strategic tech selection) |
| 0.7.0 | 2024-12-24 | Added RULE-009: Version Compatibility Protocol (TypeDB/dependency management) |
| 0.8.0 | 2024-12-24 | Added RULE-010: Evidence-Based Wisdom (hypothesis-driven approach) |
| 0.9.0 | 2024-12-24 | Added RULE-011: Multi-Agent Governance Protocol (bicameral model, MCP-based DB state) |
| 0.9.1 | 2024-12-24 | Created DESIGN-Governance-MCP.md architecture document |
| 0.10.0 | 2024-12-24 | Added RULE-012: Deep Sleep Protocol (DSP) for backlog hygiene |
| 0.11.0 | 2024-12-24 | Added RULE-013: Rules Applicability Convention (meta-referencing) |
