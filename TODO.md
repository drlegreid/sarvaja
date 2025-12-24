# TODO List - Sim.ai PoC

**Document ID:** `TODO-001`  
**Status:** Active  
**Last Updated:** 2024-12-24  
**Gap Index:** See `.windsurf/workflows.md` for full evidence

---

## Gap Index Summary

| ID | Gap | Priority | Category | Rule | Evidence |
|----|-----|----------|----------|------|----------|
| GAP-001 | ChromaDB Knowledge Integration | ✅ FIXED | integration | RULE-002 | HttpClient injection |
| GAP-002 | Opik Tracing Integration | ✅ FIXED | integration | RULE-002 | OPIK_URL_OVERRIDE |
| GAP-003 | Ollama Model Pull | ✅ FIXED | configuration | RULE-009 | gemma3:4b (4GB, memory-tight) |
| GAP-004 | Grok/xAI API Key | Medium | configuration | RULE-002 | test skip |
| GAP-005 | Agent Task Backlog UI | Medium | functionality | RULE-002 | user request |
| GAP-006 | Sync Agent Implementation | Medium | functionality | RULE-003 | skeleton only |
| GAP-007 | ChromaDB v2 Test Update | Low | testing | RULE-009 | UUID error |
| GAP-008 | Agent UI Image | Low | configuration | RULE-009 | image not found |
| GAP-009 | Pre-commit Hooks | Medium | tooling | RULE-001 | RULES-DIRECTIVES.md |
| GAP-010 | CI/CD Pipeline | Low | tooling | RULE-009 | DEPLOYMENT.md |
| GAP-011 | OctoCode MCP not in use | ✅ CONFIGURED | tooling | RULE-007 | GITHUB_PAT in .env |
| GAP-012 | TypeDB R&D (inference + type safety) | ✅ RESOLVED | R&D | RULE-010 | Phase 1+2 complete, MCP server created |
| GAP-013 | MCPs tested but not invoked | ✅ RESOLVED | workflow | RULE-007 | DECISION-001 simplified stack |
| GAP-014 | IntelliJ Windsurf MCP not loading | Medium | tooling | RULE-005 | ~/.codeium/mcp_config.json not read by IntelliJ |
| GAP-015 | Consolidated STRATEGY.md | Medium | docs | RULE-001 | docs/GAP-ANALYSIS-2024-12-24.md |
| GAP-016 | ChromaDB sync TDD stubs | ✅ DONE | testing | RULE-004 | tests/test_chromadb_sync.py (10 skipped) |
| GAP-017 | Pre-commit hooks for RULE-001/002 | Medium | tooling | RULE-001 | Duplicate of GAP-009 |
| GAP-018 | Session documentation workflow | ✅ DONE | governance | RULE-001 | docs/SESSION-TEMPLATE.md |
| GAP-019 | MCP usage documentation | Medium | docs | RULE-007 | When to use each MCP |
| GAP-020 | Cross-project knowledge queries | HIGH | workflow | RULE-007 | claude-mem needs localgai/angelgai prefixes |
| GAP-021 | OctoCode for external research | Medium | workflow | RULE-007 | Use OctoCode for GitHub patterns, not just web search |

---

## High Priority Tasks

### 1. 🔧 Fix ChromaDB Knowledge Integration

**Priority:** High  
**Effort:** Medium (2-3 hours)  
**Status:** ✅ FIXED (2024-12-24)

#### Objective
Fix Agno ChromaDb wrapper to work with remote ChromaDB server.

#### Root Cause (ACTUAL)
- Agno's ChromaDb uses ephemeral client by default, not HttpClient
- kwargs passed to wrong client type (ChromaDbClient vs HttpClient)
- **Solution:** Inject HttpClient directly into `_client` property

#### Tasks
- [x] Research Agno ChromaDb class API requirements
- [x] Discovered: kwargs go to ephemeral client, not HttpClient
- [x] Fix: Inject `chromadb.HttpClient()` into `vector_db._client`
- [x] Test connection with heartbeat()
- [ ] Update integration tests in `test_rules_governance.py`

#### Success Criteria
- [x] Knowledge base loads without errors
- [x] Agents can connect to ChromaDB
- [ ] All skipped tests pass

---

### 2. 🔍 Fix Opik Tracing Integration

**Priority:** High  
**Effort:** Low (1 hour)  
**Status:** ✅ FIXED (2024-12-24)

#### Objective
Fix Opik SDK configuration to work with self-hosted instance.

#### Root Cause
- `opik.configure()` API changed - `host` parameter not accepted
- Need to use `OPIK_URL_OVERRIDE` environment variable

#### Tasks
- [x] Review Opik SDK documentation for self-hosted config
- [x] Update `init_opik()` in playground.py (use env vars, not configure())
- [x] Update docker-compose.yml with OPIK_URL_OVERRIDE
- [ ] Test with Opik dashboard running
- [ ] Verify traces appear in dashboard

#### Success Criteria
- [x] Opik initializes without errors
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

### 10. 🔐 Add Pre-commit Hooks for Rules Enforcement

**Priority:** Medium  
**Effort:** Low (1 hour)  
**Status:** 📋 Not Started

#### Objective
Enforce RULE-001 and RULE-002 via pre-commit hooks.

#### Tasks
- [ ] Install pre-commit framework
- [ ] Create `.pre-commit-config.yaml`
- [ ] Add check for `.env` not committed
- [ ] Add check for session log in ./docs/
- [ ] Test hooks work correctly

#### Success Criteria
- [ ] Credentials blocked from commit
- [ ] Session evidence validated

---

### 11. 📊 Add CI/CD Pipeline

**Priority:** Low  
**Effort:** Medium (2 hours)  
**Status:** 📋 Not Started

#### Objective
Automate testing and deployment via GitHub Actions.

#### Tasks
- [ ] Create `.github/workflows/ci.yml`
- [ ] Add test step using `deploy.ps1 -Action test`
- [ ] Add health check step
- [ ] Configure secrets for API keys

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

### DevOps Scripts
- ✅ Created deploy.ps1 with 9 actions (up, down, status, logs, health, test, pull-models, opik, rebuild)
- ✅ Fixed ChromaDB v2 API endpoint in health check
- ✅ Created docs/DEPLOYMENT.md with full deployment guide
- ✅ Updated CLAUDE.md to reference deploy.ps1
- ✅ Updated README.md with DevOps commands table

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

## R&D Backlog

### 🎯 STRATEGIC VISION: Private Cluster AI Platform

**Goal:** Self-hosted platform with MCPs & UIs on private cluster

#### Platform Pillars

| Pillar | Components | Current | Target |
|--------|------------|---------|--------|
| **Agents** | Orchestration, routing, playground | ✅ Agno/LiteLLM | TypeDB-enhanced |
| **Tasks/Projects** | Backlog, tracking, dependencies | 📋 TODO.md | TypeDB graph |
| **Evidence/Sessions** | Decisions, logs, dumps | ✅ Markdown/scripts | Structured DB |
| **Rules** | RULE-001 to RULE-008 | ✅ Markdown | TypeDB inference |

#### Governance Mechanisms

| Mechanism | Purpose | Status |
|-----------|---------|--------|
| **Workflows** | Session protocols, ceremonies | ✅ Documented |
| **Observability** | Metrics, logs, traces | 📋 MCP-Monitor |
| **Authoring** | Rule creation, validation | 📋 TypeDB schema |
| **Conflict Resolution** | Clustering, merging | 📋 TypeDB queries |
| **Orphan Detection** | Unused rules, dead links | 📋 TypeDB inference |
| **Ambiguity Detection** | Overlapping rules | 📋 TypeDB inference |

#### Memory Architecture

| Layer | Function | Technology |
|-------|----------|------------|
| **Short-term** | Session context | ChromaDB vectors |
| **Long-term** | Institutional knowledge | TypeDB + ChromaDB |
| **Compression** | Summarization, compacting | LLM + TypeDB |
| **Indexing** | Fast retrieval | ChromaDB similarity |
| **Structuring** | Relationships, types | TypeDB schema |
| **Inference** | Rule derivation | TypeDB engine |

#### Strategic Approach: Cloud → Local Transfer

```
┌─────────────────────────────────────────────────────────────────┐
│                  KNOWLEDGE TRANSFER PIPELINE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLOUD LLM (Expensive)          LOCAL INFERENCE (Cheap)        │
│  ┌─────────────────┐            ┌─────────────────┐            │
│  │ Claude/GPT-4    │            │ Ollama/Gemma    │            │
│  │ - R&D           │   RULES    │ - Production    │            │
│  │ - Rule creation │ ────────►  │ - Apply rules   │            │
│  │ - Complex tasks │   TypeDB   │ - Fast queries  │            │
│  └─────────────────┘            └─────────────────┘            │
│                                                                 │
│  HYPOTHESIS: Rules created by expensive Cloud LLM can be       │
│  applied by cheap local models via TypeDB inference engine.    │
│                                                                 │
│  TypeDB stores the "wisdom" - local models execute it.         │
└─────────────────────────────────────────────────────────────────┘
```

> **R&D Question**: Can TypeDB rules transfer Cloud LLM reasoning to local inference?

---

### 🎯 EVOLUTION ROADMAP (DECISION-003: 2024-12-24)

**Target:** sim-ai v0.x → sim-ai v1.0 (TypeDB-Enhanced Hybrid Platform)

```
┌─────────────────────────────────────────────────────────────────┐
│                    sim-ai v1.0 Target Architecture              │
├─────────────────────────────────────────────────────────────────┤
│  Agents (7777) ─────────────────────────────────────────────    │
│       │                                                         │
│       ├── LiteLLM (4000) ── Ollama (11434)                     │
│       │                                                         │
│       ├── ChromaDB (8001)     │  TypeDB (1729)                 │
│       │   └── Semantic search │  └── Inference + Types         │
│       │   └── Documents (53)  │  └── Rules (8) + Decisions     │
│       │                       │                                 │
│       └── HYBRID QUERY LAYER ─┴─────────────────────────────   │
└─────────────────────────────────────────────────────────────────┘
```

---

### PHASE 1: TypeDB Container (Current Sprint) ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| P1.1 | ✅ DONE | Add TypeDB to docker-compose.yml (port 1729) |
| P1.2 | ✅ DONE | Create TypeDB schema for 8 rules |
| P1.3 | ✅ DONE | Create Python TypeDB client wrapper |
| P1.4 | ✅ DONE | Write inference rule: "blocked-by-dependency" |
| P1.5 | ✅ DONE | Test inference query returns results |

**Success Criteria:** TypeDB running, 1 inference rule working ✅

> **Progress (2024-12-24):** Phase 1 COMPLETE!
> - Schema + data + loader created (6 inference rules)
> - Python client wrapper with 2.29.x driver API
> - 68 tests passing (unit + BDD + integration)
> - Inference verified: transitive deps, cascade supersede, priority conflicts, escalation, proposal cascade
> - RULE-011 Multi-Agent Governance implemented with agents, proposals, votes, disputes
> - 11 rules, 4 decisions, 3 agents loaded
> - Files: `governance/schema.tql`, `governance/data.tql`, `governance/loader.py`, `governance/client.py`
> - Design: `docs/DESIGN-Governance-MCP.md` (GaaS architecture)

---

### PHASE 2: Hybrid Architecture & Governance MCP

| Task | Status | Description |
|------|--------|-------------|
| P2.1 | ✅ DONE | Migrate RULE-001 to RULE-011 to TypeDB (11 rules, 4 decisions) |
| P2.2 | ✅ DONE | Add relationships: rule-dependency, decision-affects, decision-supersedes |
| P2.3 | ✅ DONE | Test: "find all rules affected by DECISION-003" (verified) |
| P2.4 | ✅ DONE | Create Governance MCP server (11 tools) |
| P2.5 | ✅ DONE | Implement MCP tools: propose_rule, vote, dispute, get_trust_score |
| P2.6 | 📋 TODO | Create hybrid query router (TypeDB + ChromaDB) |
| P2.7 | 📋 TODO | Integration tests for MCP-TypeDB workflow |

**Success Criteria:** Governance MCP server running, basic tools working

---

### PHASE 3: Stabilization & v1.0

| Task | Status | Description |
|------|--------|-------------|
| P3.1 | 📋 TODO | Update agents to use hybrid layer |
| P3.2 | 📋 TODO | Create TypeDB MCP server (optional) |
| P3.3 | 📋 TODO | Document hybrid architecture |
| P3.4 | 📋 TODO | Performance benchmarks |
| P3.5 | 📋 TODO | v1.0 release |
| P3.6 | ⏸️ BLOCKED | Rename sim-ai → platform-gai (after v1.0 milestone) |

**Success Criteria:** Production-ready, documented, benchmarked

> **P3.6 Trigger:** Only rename after TypeDB inference is working + 1 real use case validated.
> Repo is already `platform-gai` on GitHub - codebase should match.

---

### COMPLETED / DEFERRED

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Inherit Experience Data Lakes | ✅ DONE | 53 docs in ChromaDB |
| 2 | Session Data Dump Workflow | ✅ DONE | scripts/session_dump.py |
| 3 | OctoCode MCP | ✅ CONFIGURED | GITHUB_PAT in .env |
| 4 | Mem0 / OpenMemory MCP | ⏸️ DEFERRED | Superseded by TypeDB |
| 5 | Replace Agno with Memory MCP | ⏸️ DEFERRED | Pending TypeDB outcome |
| 6 | Custom Session/Memory UI | ⏸️ DEFERRED | After TypeDB validation |
| 7 | MCP-Monitor | LOW | Nice-to-have |
| 8 | AnythingLLM | LOW | Evaluate later |
| 9 | Godot MCP sleep mode | LOW | Lazy IDE start on first call, not always-on |
| 10 | **TypeDB 3.x Frontrun R&D** | 🎯 STRATEGIC | In-house inference engine |

#### R&D-010: TypeDB 3.x Frontrun (STRATEGIC)

**Context:** TypeDB 3.x is still ALPHA (3.0.0-alpha-10). We use stable 2.29.1.

**Opportunity:** Build in-house inference engine that frontrunns TypeDB 3.x features:
- Study TypeDB 3.x alpha changelog and new features
- Identify inference patterns we need (transitive, cascade, conflict)
- Build lightweight Rust/Python inference engine
- Maintain compatibility with TypeDB 2.x data format

**Why:** Strategic independence from vendor roadmap + performance optimization.

**References:**
- TypeDB 3.x Alpha: https://github.com/vaticle/typedb/releases
- TypeDB 2.29.1 (stable): Current production version
- RULE-008: In-House Rewrite Principle (score technologies before adoption)

> **DECISION-003**: TypeDB elevated to Phase 1. Reasoning/inference > vector storage.
> **RULE-008**: Technology scorecard applied - TypeDB scored 21/25 (ADOPT).
> **Principle**: Gradual migration - don't break what works, add alongside.

---

### 18. 💾 Session Data Dump Workflow

**Priority:** HIGH  
**Effort:** Medium (1 day)  
**Status:** 📋 Not Started  
**Business Value:** Preserve learnings, enable session continuity

#### Objective
Create automated workflow to dump session data for future use.

#### What to Dump
| Data | Source | Format |
|------|--------|--------|
| Session decisions | `evidence/SESSION-DECISIONS-*.md` | Markdown |
| Gaps discovered | `TODO.md#gap-index` | JSON export |
| Rules created | `docs/RULES-DIRECTIVES.md` | Markdown |
| Memories | Cascade memory system | JSON export |
| ChromaDB docs | `sim-ai ChromaDB` | JSON + embeddings |

#### Workflow Integration
```
Session End → Trigger dump → Export to:
  1. evidence/SESSION-DUMP-{date}.json
  2. GitHub commit
  3. Optional: claude-mem sync
```

#### Script Design
```python
# scripts/session_dump.py
def dump_session():
    export_decisions()      # evidence/*.md
    export_gaps()           # TODO.md gaps as JSON
    export_chromadb()       # Vector store snapshot
    export_memories()       # Cascade memories
    commit_to_git()         # Auto-commit
```

#### Success Criteria
- [ ] One-command session dump
- [ ] JSON export for programmatic access
- [ ] Git commit with dump
- [ ] Can restore session context from dump

---

### 17. 🧠 Inherit Experience Data Lakes

**Priority:** HIGH  
**Effort:** Medium (1-2 days)  
**Status:** 📋 Not Started  
**Business Value:** Institutional knowledge, proven patterns, avoid re-learning

#### Data Sources to Inherit

| Source | Location | Docs | Content |
|--------|----------|------|--------|
| **claude-mem** | `~/.claude-mem/chroma` | 114 | Governance, sessions, workflows |
| **angelgai** | `../angelgai/` | ~10 | Crash recovery, MCP stability |
| **localgai** | `../localgai/` | ~20 | EBMSF, DSM, scripts |

#### Knowledge Categories

```
governance     - Bicameral model, RACI, sync protocol
session_*      - Session histories, decisions
workflow       - DSM, AITV, ceremonies
mcp_*          - Selection methodology, stability rules
scripts        - Python utilities (dsm_tracker, memory_audit)
```

#### Migration Strategy

1. **Phase 1:** Export claude-mem to sim-ai ChromaDB
2. **Phase 2:** Import governance docs as agent knowledge
3. **Phase 3:** Migrate scripts to sim-ai/scripts/
4. **Phase 4:** Update agent instructions with inherited patterns

#### Why This Matters
- 114 docs = months of learnings
- EBMSF methodology = proven MCP selection
- DSM workflow = structured maintenance
- Governance model = human/AI collaboration

---

### 15. 🏆 TypeDB In-House Solution (UPSELL)

**Priority:** HIGH  
**Effort:** High (weeks)  
**Status:** 📋 R&D Planning  
**Business Value:** Differentiation, upsell to enterprise clients

#### Strategic Vision
Build in-house TypeDB-based rules engine with:
- **Inference engine** - Auto-derive facts from rules
- **Type safety** - Compile-time validation (Haskell magic)
- **Symbolic reasoning** - Logic-based querying
- **Enterprise features** - Audit trail, compliance

#### Why TypeDB > ChromaDB for Rules?
| Feature | ChromaDB | TypeDB |
|---------|----------|--------|
| Storage | Vector similarity | Graph + Types |
| Queries | Semantic search | Logic inference |
| Rules | Manual evaluation | Auto-derivation |
| Types | None | Strong polymorphic |
| Reasoning | None | Symbolic |

#### Upsell Potential
- Enterprise compliance (audit trails)
- Complex rule chains (auto-inference)
- Type-safe integrations (Haskell client)
- On-premise deployment (no cloud dependency)

#### Phase Plan (USER DECISION 2024-12-24)

**Phase 1: Vanilla TypeDB**
1. Deploy vanilla TypeDB locally
2. Prototype rules schema
3. Build inference rules for governance
4. Test with sim-ai knowledge base
5. Validate inference + type safety benefits

**Phase 2: Performance Rewrite**
1. Evaluate rewrite in: **Haskell**, **Go**, or **Rust**
2. Keep TypeDB schema/query language
3. Optimize for:
   - Local-first deployment
   - Memory efficiency
   - Enterprise performance
4. Migration path from vanilla TypeDB

---

### 16. 🔄 Replace Agno ChromaDb with Memory MCP

**Priority:** HIGH  
**Effort:** Medium (1-2 days)  
**Status:** 📋 Not Started

#### Why Replace Agno?
| Aspect | Agno ChromaDb | Memory MCP (Existing) |
|--------|---------------|----------------------|
| Maturity | New, undocumented | Proven in localgai (114 docs) |
| Integration | Hacky (_client injection) | Clean MCP protocol |
| Features | Basic vector search | Knowledge graph, relations |
| Governance | None | Bicameral model built-in |
| Stability | Unknown | Production-tested |

#### Agno's Actual Value
- **AgentOS** - FastAPI serving (keep this)
- **Agent orchestration** - Multi-agent patterns (keep this)
- **ChromaDb wrapper** - REMOVE (use memory MCP instead)

#### Migration Plan
1. Keep Agno for agent orchestration only
2. Replace `create_chromadb_knowledge()` with memory MCP calls
3. Use existing claude-mem patterns from localgai
4. Preserve bicameral governance model

---

### 12. 🔬 TypeDB Technical Research (GAP-012)

**Priority:** Medium  
**Effort:** High (research + implementation)  
**Status:** 📋 Not Started

#### Objective
Evaluate TypeDB for local premise deployment with:
- Strong type system (polymorphic queries)
- Rule inference engine
- Symbolic reasoning
- Haskell client integration (type-safe queries)

#### Research Questions
1. Can TypeDB replace/complement ChromaDB for rules storage?
2. How does inference compare to manual rule evaluation?
3. Is Haskell client mature enough for production?
4. Resource requirements for local deployment?

#### Resources
- TypeDB: https://github.com/typedb/typedb
- Haskell Client: https://github.com/typedb-osi/typedb-client-haskell (INCUBATING)
- Learning Center: https://typedb.com/learn

#### TypeDB Features
| Feature | Benefit |
|---------|---------|
| Type System | Polymorphic queries, compile-time safety |
| Rule Inference | Auto-derive facts from rules |
| Symbolic Reasoning | Logic-based querying |
| TypeQL | Declarative query language |

#### Haskell Client Layers
1. **Type-Safe-Client** - Schema compiled with Haskell (strongest)
2. **High-Level-Client** - Nice API for TypeDB Protocol
3. **Low-Level-Client** - gRPC wrapper

---

### 13. 🔍 OctoCode MCP Integration (GAP-011)

**Priority:** High  
**Effort:** Low (30 min)  
**Status:** 📋 Not Started

#### Objective
Enable semantic GitHub code search via OctoCode MCP.

#### Why Not Using It?
- Was classified as RISKY in angelgai (rate limits, memory)
- But user correctly notes: it's valuable for code research

#### OctoCode Tools
| Tool | Purpose |
|------|---------|
| `githubSearchCode` | Find code patterns across repos |
| `githubSearchRepositories` | Discover repos by topic |
| `githubViewRepoStructure` | Explore repo structure |
| `githubGetFileContent` | Read files with smart extraction |
| `githubSearchPullRequests` | Find PRs |

#### Commands
- `/research` - Expert code & product research
- `/plan` - Research, plan & implement
- `/review_pull_request` - PR review
- `/review_security` - Security audit

#### Installation
```json
{
  "octocode": {
    "command": "npx",
    "args": ["-y", "octocode-mcp@latest"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "<token>"
    }
  }
}
```

#### Tasks
- [ ] Add OctoCode to mcp_config.json
- [ ] Configure GitHub PAT
- [ ] Test with `/research` command
- [ ] Document in workflows.md

---

### 14. 🛠️ MCP Workflow Integration (GAP-013)

**Priority:** High  
**Effort:** Medium  
**Status:** 📋 Not Started

#### Problem
MCPs are tested/verified but NOT actively used in workflow.

#### Root Cause
- Cascade doesn't auto-invoke MCP tools
- Need explicit tool calls or prompts
- Some MCPs require specific invocation patterns

#### Available MCPs (Verified Working)
| MCP | How to Use |
|-----|------------|
| `sequential-thinking` | Complex reasoning chains |
| `memory` | Knowledge graph persistence |
| `playwright` | Browser automation |
| `desktop-automation` | Robot automation |
| `desktop-commander` | File/process ops |

#### Actions
- [ ] Document when to use each MCP
- [ ] Create workflow triggers for MCP usage
- [ ] Add MCP usage to RULE-004/005
- [ ] Practice using MCPs in actual work

---

### 19. 🧠 Mem0 / OpenMemory MCP

**Priority:** 🔥 TOP (DECISION-002)  
**Effort:** Medium (1-2 days)  
**Status:** 🔄 IN PROGRESS  
**Source:** https://mem0.ai/blog/how-to-make-your-clients-more-context-aware-with-openmemory-mcp

#### What It Is
Private, local memory layer for MCP clients with vector-backed storage. Works with Cursor, Claude Desktop, and other MCP-compatible tools.

#### Key Features
- Local-first (data stays on your machine)
- Vector storage for semantic search
- MCP protocol native
- Dashboard UI included
- Cross-session memory persistence

#### Requirements (discovered 2024-12-24)
- `pip install mem0ai` ✅ Installed
- ~~OPENAI_API_KEY required~~ **CAN USE OLLAMA INSTEAD!**
- Config: `"ollama_base_url": "http://localhost:11434"`

#### Ollama Config (no OpenAI needed)
```python
config = {
    'llm': {'provider': 'ollama', 'config': {'model': 'gemma3:4b', 'ollama_base_url': 'http://localhost:11434'}},
    'embedder': {'provider': 'ollama', 'config': {'model': 'nomic-embed-text', 'ollama_base_url': 'http://localhost:11434'}}
}
```

#### Next Steps
- [x] Pull Ollama embedding model: `ollama pull nomic-embed-text` ✅ Done
- [x] Test Mem0 with Ollama embeddings ✅ Validated 2024-12-24
- [x] Created `config/mem0_config.py` with reusable config
- [ ] Deploy OpenMemory MCP server
- [ ] Integrate with Windsurf/Cascade
- [ ] Migrate 53 ChromaDB docs if successful

#### Validation Evidence (2024-12-24)
```
Add result: {'id': '751fdaf2-...', 'memory': 'sim-ai project uses...', 'event': 'ADD'}
Search results: 1 found
```
**Note:** Use `embedding_model_dims: 768` for nomic-embed-text (not 1536 like OpenAI).

---

### 20. 🤖 AnythingLLM

**Priority:** MEDIUM  
**Effort:** Low (exploration)  
**Status:** 📋 RESEARCH  
**Source:** https://anythingllm.com | https://github.com/Mintplex-Labs/anything-llm

#### What It Is
All-in-one AI application for document chat, local LLM hosting, and RAG.

#### Key Features
- Desktop app (free)
- Use any LLM (local or API)
- Document RAG built-in
- Privacy-focused
- No technical setup required

#### Evaluation Criteria
- [ ] Compare with our LiteLLM + Agents stack
- [ ] Test document ingestion workflow
- [ ] Assess if it replaces or complements our stack

---

### 21. 📚 Awesome MCP Memory Servers

**Priority:** RESEARCH  
**Effort:** Low (survey)  
**Status:** 📋 RESEARCH  
**Source:** https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md

#### Notable Projects
| Project | Description |
|---------|-------------|
| **Arc Memory** | Temporal knowledge graph for AI dev |
| **CogniGraph** | Mind maps + knowledge graphs |
| **mcp-obsidian** | Obsidian vault integration |
| **mcp-memory-bank** | Structured docs for context preservation |
| **mem0 integration** | Long-term memory via Mem0 |

#### Actions
- [ ] Survey top 5 projects
- [ ] Identify best fit for sim-ai use case
- [ ] Consider Arc Memory for TypeDB alternative

---

### 22. 🖥️ MCP-Monitor (Crash Prevention)

**Priority:** HIGH  
**Effort:** Low (1 hour)  
**Status:** 📋 RESEARCH  
**Source:** https://github.com/seekrays/mcp-monitor

#### What It Is
System monitoring tool that exposes metrics via MCP protocol. LLMs can query real-time system info.

#### Available Tools
| Tool | Purpose |
|------|---------|
| `get_cpu_info` | CPU usage, core count |
| `get_memory_info` | Virtual/swap memory usage |
| `get_disk_info` | Disk usage, partitions |
| `get_network_info` | Network interfaces, traffic |
| `get_host_info` | System details, uptime |
| `get_process_info` | Process listing, sorting by CPU/memory |

#### Use Case for sim-ai
- **Prevent crashes** by monitoring memory before heavy operations
- **Auto-scale** model selection based on available resources
- **Debug** memory leaks in long sessions

#### Next Steps
- [ ] Install mcp-monitor: `npx @anthropic-ai/create-mcp-server`
- [ ] Add to Windsurf MCP config
- [ ] Create workflow: check memory before model calls
- [ ] Alert if memory < threshold

---

## Session Notes

### 2024-12-24 (Initial Deployment)
- Deployed full stack (LiteLLM, ChromaDB, Ollama, Agents)
- Claude completion working through LiteLLM proxy
- Discovered ChromaDB v2 API breaking changes
- Discovered Opik SDK API changes
- Created sync agent skeleton
- Pushed to GitHub

### 2024-12-24 (Claude Code Setup)
- Configured new ANTHROPIC_API_KEY in .env
- Validated all 10 MCPs active and working
- Tested Mem0 with Ollama embeddings ✅ (DECISION-002 validated)
- Tested LiteLLM routing: gemma-local + claude-sonnet ✅
- Created `config/mem0_config.py` for reusable Mem0 config
- Created session evidence: `evidence/SESSION-2024-12-24-CLAUDE-CODE-SETUP.md`
- Ollama models: gemma3:4b (3.3GB), nomic-embed-text (274MB)

### Next Session Focus
1. Deploy OpenMemory MCP server
2. Integrate Mem0 with Windsurf/Cascade
3. Evaluate MCP-Monitor for crash prevention
4. Fix deploy.ps1 health check script (curl issue)

---

**Document Maintenance**
- Update TODO.md when discovering gaps
- Move completed tasks to "Completed" section
- Review priorities weekly
