# Sim.ai Rules Directives

## Overview

This document defines mandatory rules for the Sim.ai PoC agent platform.
Rules are indexed in ChromaDB (`sim_ai_rules` collection) and enforced by agents.

**Quick Reference:** 4 active rules, 6 categories, automated enforcement via pre-commit + CI/CD.

---

## Rules Summary

| Rule | Category | Priority | Status | Enforcement |
|------|----------|----------|--------|-------------|
| RULE-001 | governance | CRITICAL | ACTIVE | Session logs required |
| RULE-002 | architecture | HIGH | ACTIVE | Code review |
| RULE-003 | governance | HIGH | DRAFT | Sync agent |
| RULE-004 | testing | HIGH | ACTIVE | Playwright MCP |
| RULE-005 | stability | HIGH | ACTIVE | Memory thresholds |

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
   - All agent calls traced via Opik
   - Health endpoints for every service
   - Structured logging (JSON format)

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
    - opik_tracing_enabled: true
    - health_endpoints_exist: true
    - structured_logging: true
  degradation:
    - fallback_models_configured: true
    - timeouts_configured: true
    - retries_implemented: true
```

### Validation

- [ ] No circular imports detected
- [ ] All secrets in `.env` (not in code)
- [ ] Health endpoint returns 200
- [ ] Opik traces visible in dashboard

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

### MCP Stability Tiers

| Tier | MCPs | Risk | Usage |
|------|------|------|-------|
| **STABLE** | sequential-thinking, memory | LOW | ✅ Always allowed |
| **MODERATE** | desktop-commander, playwright, desktop-automation | MEDIUM | ✅ Use with monitoring |
| **RISKY** | context7, docker, fetch | HIGH | ⚠️ Use cautiously |
| **CONDITIONAL** | godot | MEDIUM | ⚠️ Requires Godot editor |

### Approved MCPs (Verified Working)

```
✅ sequential-thinking - Chain-of-thought reasoning
✅ memory            - Knowledge graph persistence
✅ playwright         - Browser automation (v0.0.53)
✅ desktop-automation - Robot MCP Server
✅ desktop-commander  - File/process operations
⚠️ godot             - Requires Godot editor running
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

## Enforcement

Rules are enforced via:
1. **Pre-commit hooks** - Static validation
2. **CI/CD checks** - Test suite includes rule compliance
3. **Runtime guards** - Agent checks rules before execution
4. **Opik metrics** - Track rule violation rates

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 0.1.0 | 2024-12-24 | Initial rules: Session Evidence, Architecture |
| 0.2.0 | 2024-12-24 | Added RULE-004: Exploratory Test Automation with Playwright MCP |
| 0.3.0 | 2024-12-24 | Added RULE-005: Memory & MCP Stability (from AngelGAI/LocalGAI) |
