# Sim.ai Rules Directives

## Overview

This document defines mandatory rules for the Sim.ai PoC agent platform.
Rules are indexed in ChromaDB (`sim_ai_rules` collection) and enforced by agents.

**Quick Reference:** 8 active rules, 7 categories, automated enforcement via pre-commit + CI/CD.

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
