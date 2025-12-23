# TODO List - Sim.ai PoC

**Document ID:** `TODO-001`  
**Status:** Active  
**Last Updated:** 2024-12-24

---

## High Priority Tasks

### 1. 🔧 Fix ChromaDB Knowledge Integration

**Priority:** High  
**Effort:** Medium (2-3 hours)  
**Status:** 📋 Not Started

#### Objective
Fix Agno ChromaDb wrapper to work with ChromaDB v2 API. Currently disabled in `agent/playground.py`.

#### Root Cause
- ChromaDB v2 API requires collection UUIDs, not names
- Agno wrapper expects different parameters than v2 provides

#### Tasks
- [ ] Research Agno ChromaDb class API requirements
- [ ] Create ChromaDB client wrapper that handles UUID lookup
- [ ] Update `create_chromadb_knowledge()` in playground.py
- [ ] Test with rules/memories/sessions collections
- [ ] Update integration tests in `test_rules_governance.py`

#### Success Criteria
- [ ] Knowledge base loads without errors
- [ ] Agents can query ChromaDB for rules
- [ ] All skipped tests pass

---

### 2. 🔍 Fix Opik Tracing Integration

**Priority:** High  
**Effort:** Low (1 hour)  
**Status:** 📋 Not Started

#### Objective
Fix Opik SDK configuration to work with self-hosted instance.

#### Root Cause
- `opik.configure()` API changed - `host` parameter not accepted
- Need to use correct configuration method for self-hosted Opik

#### Tasks
- [ ] Review Opik SDK documentation for self-hosted config
- [ ] Update `init_opik()` in playground.py
- [ ] Test with Opik dashboard running
- [ ] Verify traces appear in dashboard

#### Success Criteria
- [ ] Opik initializes without errors
- [ ] Agent calls traced in Opik dashboard

---

### 3. 🚀 Start Opik Dashboard

**Priority:** High  
**Effort:** Low (30 minutes)  
**Status:** 📋 Not Started

#### Objective
Start Opik dashboard for agent monitoring.

#### Tasks
- [ ] Run `cd opik; .\opik.ps1`
- [ ] Verify dashboard at http://localhost:5173
- [ ] Document any startup issues
- [ ] Update health test to pass

#### Success Criteria
- [ ] Dashboard accessible
- [ ] `test_opik_health` passes

---

### 4. 📦 Pull Ollama Model

**Priority:** High  
**Effort:** Low (15 minutes + download time)  
**Status:** 📋 Not Started

#### Objective
Pull gemma3:4b model for local inference.

#### Tasks
- [ ] Run `docker exec sim-ai-ollama-1 ollama pull gemma3:4b`
- [ ] Verify model available with `ollama list`
- [ ] Test local completion via LiteLLM
- [ ] Update test to pass

#### Success Criteria
- [ ] `test_local_ollama_completion` passes

---

## Medium Priority Tasks

### 5. 🔑 Configure Grok/xAI Integration

**Priority:** Medium  
**Effort:** Low (15 minutes)  
**Status:** ⏳ Pending (needs API key)

#### Objective
Enable Grok model routing through LiteLLM.

#### Tasks
- [ ] Obtain xAI API key
- [ ] Add to `.env` as `XAI_API_KEY`
- [ ] Test Grok completion
- [ ] Update test to pass

#### Success Criteria
- [ ] `test_grok_completion` passes

---

### 6. 📊 Implement Agent Task Backlog UI

**Priority:** Medium  
**Effort:** Medium (3-4 hours)  
**Status:** 📋 Not Started

#### Objective
Create visibility into agent tasks and execution history.

#### Options
1. **Opik Dashboard** - Primary (already cloned)
2. **Agent UI** - `docker compose --profile full up -d agent-ui`
3. **Custom ChromaDB viewer** - Query sessions collection

#### Tasks
- [ ] Start Opik dashboard (see Task #3)
- [ ] Configure agents to send traces
- [ ] Create dashboard views for:
  - [ ] Task execution history
  - [ ] Token usage per agent
  - [ ] Success/failure rates
- [ ] Document how to access backlog

#### Success Criteria
- [ ] Can view agent task history
- [ ] Can see execution metrics

---

### 7. 🔄 Implement Sync Agent

**Priority:** Medium  
**Effort:** Medium (4-5 hours)  
**Status:** 📋 Not Started (skeleton created)

#### Objective
Enable synchronization of skills, sessions, and rules across environments.

#### Tasks
- [ ] Implement Git transport for skillbooks
- [ ] Test sync_agent.py --test mode
- [ ] Create skillbooks/ directory structure
- [ ] Document sync workflow

#### Success Criteria
- [ ] Can sync skillbooks to Git
- [ ] Can pull rules from remote

---

## Low Priority Tasks

### 8. 📝 Update Tests for ChromaDB v2 API

**Priority:** Low  
**Effort:** Medium (2 hours)  
**Status:** ⏸️ On Hold (blocked by Task #1)

#### Objective
Refactor ChromaDB tests to use proper v2 API with UUIDs.

#### Tasks
- [ ] Get collection UUID after creation
- [ ] Use UUID in subsequent API calls
- [ ] Remove `@pytest.mark.skip` decorators
- [ ] Verify all tests pass

---

### 9. 🎨 Add Agent UI Dashboard

**Priority:** Low  
**Effort:** Low (30 minutes)  
**Status:** 📋 Not Started

#### Objective
Enable visual chat interface with agents.

#### Tasks
- [ ] Run `docker compose --profile full up -d agent-ui`
- [ ] Access http://localhost:3000
- [ ] Test agent interactions
- [ ] Document usage

---

## Completed Tasks ✅

### Docker Stack Deployment
- ✅ Created docker-compose.yml with CPU profile
- ✅ Configured LiteLLM with Claude + Grok + Ollama models
- ✅ Set up ChromaDB for vector storage
- ✅ Created 5 agents (Orchestrator, Rules Curator, Researcher, Coder, Local)
- ✅ All containers running and healthy

### Documentation
- ✅ Created README.md with architecture overview
- ✅ Created SESSION-2024-12-24-POC-DEPLOYMENT.md
- ✅ Created RULES-DIRECTIVES.md (RULE-001, RULE-002)
- ✅ Created SYNC-AGENT-DESIGN.md

### Testing
- ✅ Created pytest test suite
- ✅ Health tests passing (6/7 - Opik pending)
- ✅ LiteLLM routing tests passing (Claude works)

### GitHub Integration
- ✅ Pushed to drlegreid/platform-gai
- ✅ Credentials excluded via .gitignore

---

## Task Status Legend

| Symbol | Status | Meaning |
|--------|--------|---------|
| ✅ | Completed | Task finished and verified |
| 🚧 | In Progress | Currently working on this |
| ⏳ | Pending | Waiting on dependency or action |
| 📋 | Not Started | Ready to begin |
| ❌ | Blocked | Cannot proceed due to blocker |
| ⏸️ | On Hold | Paused for later consideration |

---

## Session Notes

### 2024-12-24 (Initial Deployment)
- Deployed full stack (LiteLLM, ChromaDB, Ollama, Agents)
- Claude completion working through LiteLLM proxy
- Discovered ChromaDB v2 API breaking changes
- Discovered Opik SDK API changes
- Created sync agent skeleton
- Pushed to GitHub

### Next Session Focus
1. Start Opik dashboard (Task #3)
2. Pull Ollama model (Task #4)
3. Fix Opik tracing (Task #2)
4. Fix ChromaDB knowledge (Task #1)

---

**Document Maintenance**
- Update TODO.md when discovering gaps
- Move completed tasks to "Completed" section
- Review priorities weekly
