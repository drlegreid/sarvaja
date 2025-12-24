# Sim.ai Windsurf Workflows

## Overview

This document defines Cascade/Windsurf workflows for the Sim.ai PoC project, ensuring consistent development patterns, gap tracking, and evidence documentation.

---

## Workflow 1: Session Start Protocol

**Trigger:** Every new Cascade session

### Steps
1. **Load Context**
   ```
   - Read CLAUDE.md for project rules
   - Read TODO.md for current gaps/tasks
   - Check docker ps for running services
   ```

2. **Verify Services**
   ```powershell
   .\deploy.ps1 -Action status
   .\deploy.ps1 -Action health
   ```

3. **Review Open Gaps**
   - Check TODO.md High Priority tasks
   - Note any blockers from previous session

---

## Workflow 2: Gap Discovery & Documentation

**Trigger:** When discovering any issue, inconsistency, or missing functionality

### Steps
1. **Capture Evidence**
   - Error message (exact text)
   - File path and line number
   - Command that triggered the issue
   - Expected vs actual behavior

2. **Classify Gap**
   | Category | Examples |
   |----------|----------|
   | `integration` | API mismatch, SDK changes |
   | `configuration` | Missing env vars, wrong endpoints |
   | `functionality` | Missing feature, broken behavior |
   | `documentation` | Missing docs, outdated info |
   | `testing` | Missing tests, failing tests |

3. **Add to TODO.md**
   ```markdown
   ### N. 🔧 [Gap Title]
   
   **Priority:** High/Medium/Low
   **Effort:** Low/Medium/High (estimated hours)
   **Status:** 📋 Not Started
   **Category:** [category]
   **Discovered:** [date]
   
   #### Evidence
   - **Error:** `[exact error message]`
   - **File:** `[file:line]`
   - **Command:** `[command that triggered]`
   
   #### Root Cause
   [Analysis of why this gap exists]
   
   #### Tasks
   - [ ] Task 1
   - [ ] Task 2
   
   #### Success Criteria
   - [ ] Criterion 1
   ```

4. **Create Memory** (if significant)
   - Use Cascade memory tool for cross-session persistence
   - Tag with project name and gap category

---

## Workflow 3: Session Evidence Export

**Trigger:** End of significant work session

### Steps
1. **Create Session Log**
   - File: `docs/SESSION-{YYYY-MM-DD}-{topic}.md`
   - Include thought chain, decisions, artifacts

2. **Update TODO.md**
   - Move completed tasks to "Completed" section
   - Add any new gaps discovered
   - Update task statuses

3. **Commit & Push**
   ```powershell
   git add -A
   git commit -m "Session: [brief description]"
   git push origin master
   ```

---

## Workflow 4: DevOps Operations

**Trigger:** Any deployment, rebuild, or service operation

### Commands Reference
```powershell
# Start/Stop
.\deploy.ps1 -Action up -Profile cpu
.\deploy.ps1 -Action down

# Monitoring
.\deploy.ps1 -Action status
.\deploy.ps1 -Action logs
.\deploy.ps1 -Action health

# Maintenance
.\deploy.ps1 -Action rebuild
.\deploy.ps1 -Action pull-models
.\deploy.ps1 -Action test

# Observability
.\deploy.ps1 -Action opik
```

### Health Check Sequence
```powershell
# Full health verification
.\deploy.ps1 -Action health
pytest tests/test_health.py -v
```

---

## Workflow 5: Integration Testing

**Trigger:** After any code change or configuration update

### Steps
1. **Run Health Tests**
   ```powershell
   pytest tests/test_health.py -v --tb=short
   ```

2. **Run Routing Tests**
   ```powershell
   pytest tests/test_litellm_routing.py -v --tb=short
   ```

3. **Run Full Suite**
   ```powershell
   .\deploy.ps1 -Action test
   ```

4. **Document Results**
   - Record pass/fail counts
   - Note any new failures
   - Add gaps for failing tests

---

## Workflow 6: Memory Interaction Protocol

**Trigger:** When needing cross-session context

### Creating Memories
- **Project context**: Tag with `sim-ai`, `platform-gai`
- **Gap discoveries**: Tag with `gap`, `[category]`
- **Decisions**: Tag with `decision`, `architecture`
- **Evidence**: Tag with `evidence`, `[date]`

### Querying Memories
- Before web search, check memories first
- Use specific tags for targeted retrieval
- Cross-reference with TODO.md gaps

---

## Gap Index

### Current Gaps (from TODO.md)

| ID | Gap | Priority | Category | Status |
|----|-----|----------|----------|--------|
| GAP-001 | ChromaDB Knowledge Integration | High | integration | Not Started |
| GAP-002 | Opik Tracing Integration | High | integration | Not Started |
| GAP-003 | Ollama Model Pull | High | configuration | Not Started |
| GAP-004 | Grok/xAI API Key | Medium | configuration | Pending |
| GAP-005 | Agent Task Backlog UI | Medium | functionality | Not Started |
| GAP-006 | Sync Agent Implementation | Medium | functionality | Not Started |
| GAP-007 | ChromaDB v2 Test Update | Low | testing | On Hold |
| GAP-008 | Agent UI Image | Low | configuration | Blocked |
| GAP-009 | Pre-commit Hooks | Medium | tooling | Not Started |
| GAP-010 | CI/CD Pipeline | Low | tooling | Not Started |

---

## Evidence Archive

### 2024-12-24: Initial Deployment

**Session Artifacts:**
- `docker-compose.yml` - Stack configuration
- `config/litellm_config.yaml` - Model routing
- `agents.yaml` - 5 agent definitions
- `agent/playground.py` - Agent server
- `tests/` - Integration test suite

**Discoveries:**
1. ChromaDB v2 API breaking change (collections require UUID)
2. Opik SDK `configure()` API changed (host parameter removed)
3. Agno `OpenAILike` model class doesn't exist (use `Claude` directly)
4. `agnohq/agent-ui` Docker image not available

**Resolutions:**
- ✅ Switched to `agno.models.anthropic.Claude`
- ✅ Disabled ChromaDB knowledge temporarily
- ✅ Deferred Opik integration
- ⏳ Agent UI blocked on image availability

---

## Workflow 7: EBMSF - Evidence-Based MCP Selection

**Trigger:** Adding new MCP server or reviewing existing MCPs
**Source:** LocalGAI methodology (proven in production)

### Phase 1: Discovery
Sources to check:
- https://github.com/modelcontextprotocol/servers (Official)
- https://mcpmarket.com/ (10,000+ tools, leaderboard)
- https://mcp.so/ (Registry - 17,000+ servers)

### Phase 2: Hypothesis Formation
```
Template: IF [project_need] THEN [mcp_candidate] BECAUSE [evidence]

Example: IF project requires browser testing 
         THEN playwright-mcp 
         BECAUSE it captures traces and screenshots automatically
```

### Phase 3: Risk Assessment
| Dimension | LOW | MEDIUM | HIGH |
|-----------|-----|--------|------|
| Security | Read-only, no network | Sandboxed writes | System access, network |
| Stability | Official, >1yr | Community, 6-12mo | New, <6mo |
| Data | Local files only | External with auth | Transmits sensitive |

**Threshold:** Total risk ≤ 6 (max 3 per dimension)

### Phase 4: Impact Scoring
| Metric | Weight | HIGH | MEDIUM | LOW |
|--------|--------|------|--------|-----|
| Token Preservation | 35% | >50% | 25-50% | <25% |
| Task Acceleration | 30% | >40% | 20-40% | <20% |
| Error Reduction | 20% | >30% | 15-30% | <15% |
| Learning Curve | 15% | <1hr | 1-4hr | >4hr |

### Phase 5: Decision Matrix
```
MUST_HAVE:    Impact ≥ 2.5 AND Risk ≤ 4
RECOMMENDED:  Impact ≥ 2.0 AND Risk ≤ 6
OPTIONAL:     Impact ≥ 1.5 AND Risk ≤ 6
EXCLUDE:      Impact < 1.5 OR Risk > 6
```

### Phase 6: Continuous Validation
- Monthly review of all MCPs
- Check GitHub for maintenance status
- Re-evaluate on project scope change

---

## Workflow 8: Exploratory Testing with Playwright MCP

**Trigger:** Testing UI/web components

### Prerequisites
- Playwright MCP configured in `mcp_config.json`
- Target URL accessible

### Heuristics to Apply

| Heuristic | Actions |
|-----------|--------|
| `BOUNDARY` | Empty inputs, max length, special chars |
| `NAVIGATION` | All links, back button, deep links |
| `STATE` | Login/logout, form persistence, refresh |
| `ERROR` | Invalid inputs, network failures, 404s |
| `ACCESSIBILITY` | Tab order, screen reader, contrast |

### Workflow Steps

```
1. browser_navigate → target URL
2. browser_screenshot → initial state
3. Apply BOUNDARY heuristic:
   - browser_fill → empty, max, special
   - browser_screenshot → each state
4. Apply NAVIGATION heuristic:
   - browser_click → all links
   - browser_screenshot → each page
5. Apply ERROR heuristic:
   - browser_fill → invalid data
   - browser_console → capture errors
6. Document findings in session log
```

### Evidence Collection
```powershell
# Screenshots saved to:
./evidence/screenshots/{date}_{test}_{state}.png

# Console logs:
./evidence/logs/{date}_{test}_console.json
```

---

## Related Documents

- [CLAUDE.md](../CLAUDE.md) - Project rules
- [TODO.md](../TODO.md) - Task tracking
- [RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) - Governance rules (RULE-004)
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide

---

**Last Updated:** 2024-12-24
