# Changelog

All notable changes to **Sarvaja** (formerly sim.ai) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0-GA] - 2026-03-20

### Milestone: Sarvaja v1 General Availability

The platform reaches v1 readiness with **Sessions Management for Claude Code** as the flagship feature — full lifecycle tracking, JSONL ingestion, transcript viewing, and entity linking for Claude Code development sessions.

See [Release Notes](docs/releases/V1.0-GA.md) for full details.

---

## [1.3.1] - 2026-02-08

### Added
- **Workspaces & Capabilities**: CRUD for agent workspaces with TypeDB persistence
- **JSONL Watcher Daemon**: Event-driven session file monitoring
- **Session auto-refresh**: CustomTitle extraction and automatic UI updates
- **Robot Framework E2E**: 49 tests green, EDS rule + spec coverage
- **Gamedev workspace**: GAP-GAMEDEV-WS unified patterns audit

### Changed
- **Security hardening**: Deep scan batches 426–477 — 400+ logger sanitization fixes across all layers (routes, services, MCP tools, stores, UI controllers)
- **MCP integration tests**: Full suite + 2 production bug fixes + E2E selector alignment
- **Test suite hardening**: 0 unit failures, 141 integration pass

### Fixed
- Session `end_time`/`duration` computation
- Non-blocking overlay scrim for loading states
- Scheduler discovery E2E + schema resilience

---

## [1.3.0] - 2026-01-20

### Added
- **Sessions Management** (flagship feature):
  - Claude Code JSONL auto-discovery from `~/.claude/projects/`
  - Mega-session ingestion pipeline (streaming, ~60MB peak for 612MB files)
  - 4-tier transcript fallback (JSONL → in-memory → evidence → empty)
  - Zoom-level lazy loading (0=summary, 1=+tools, 2=+inputs, 3=+thinking)
  - Session transcript UI with color-coded conversation cards
  - Entity linking: sessions ↔ rules, decisions, tasks, evidence
  - MCP auto-session tracker for non-chat tool calls
  - Session repair and content validation (CVP Tier 2)
  - Disk-backed session persistence surviving container restarts
- **Ingestion pipeline**: 5 MCP tools (`ingest_session_content`, `mine_session_links`, `ingest_session_full`, `ingestion_status`, `ingestion_estimate`)
- **Session detail endpoints**: `/sessions/{id}/detail`, `/sessions/{id}/tools`, `/sessions/{id}/thoughts`, `/sessions/{id}/transcript`
- **Session relations endpoints**: `/sessions/{id}/evidence`, `/sessions/{id}/tasks`, `/sessions/{id}/rules`, `/sessions/{id}/decisions`
- **Evidence rendering**: Markdown→HTML for evidence file previews
- **Session validation**: CVP heuristic checks (H-SESSION-002/005/006)

### Changed
- Dashboard navigation consolidated to single source of truth (`constants.py`, 16 items)
- Session UI: 12 view modules (list, detail, content, transcript, tool_calls, tasks, evidence, timeline, form, validation)
- TypeDB schema extended with session attributes (`cc_session_uuid`, `cc_project_slug`, `cc_git_branch`, etc.)

---

## [1.2.0] - 2026-01-14

### Added
- **Orchestrator workflow** (WORKFLOW-ORCH-01-v1): Continuous loop engine with phases GATE→BACKLOG→SPEC→IMPLEMENT→VALIDATE→CERTIFY→COMPLETE
- **Dynamic budget**: ROI-based gating with `compute_budget()`, token exhaustion at 80%
- **3-tier validation specs** (TEST-SPEC-01-v1): Gherkin-style Business→Technical→Low-level
- **MCP-first enforcement** (GOV-MCP-FIRST-01-v1): TypeDB via MCP as single source of truth
- **Heuristic checks**: 27 automated checks across 6 domains (TASK, SESSION, RULE, AGENT, CROSS-ENTITY, EXPLORATORY)
- **Audit trail**: Full CRUD audit with correlation IDs, actor attribution, 7-day retention
- **Communication rule** (COMM-PROGRESS-01-v1): Batch stats must include impact + next steps

### Changed
- Project renamed from sim.ai to **Sarvaja** (per DECISION-008)
- Container runtime migrated from Docker to **Podman** (xubuntu migration)
- Mock StateGraph replaces LangGraph (OOM prevention on 13.5GB systems)

---

## [1.1.0] - 2025-12-30

### Added
- **MCP server split** (ARCH-MCP-02-v1): gov-core, gov-agents, gov-sessions, gov-tasks
- **Trust scoring**: Agent trust leaderboard, governance proposals, voting
- **Session bridge**: Chat ↔ gov-sessions integration
- **Data integrity**: Session persistence with TypeDB-first, in-memory fallback
- **Dashboard views**: Expanded to 15 views (Executive, Impact, Trust, Workflow, Audit, Monitor, Infrastructure, Metrics, Tests)

### Changed
- Architecture refactored from monolithic MCP to 4 domain-specific servers
- TypeDB schema migrated to 3.x syntax (hyphens, `value integer`, datetime without quotes)

---

## [1.0.0] - 2024-12-25

### Added

#### Governance Framework
- **22 Rules** (RULE-001 to RULE-022) for multi-agent governance
- **TypeDB integration** with inference engine (6 inference rules)
- **Governance MCP Server** with 26 tools
- **Trust scoring** algorithm for agent voting (RULE-011)

#### Rules by Category
- **Governance** (7): Session logging, sync, decisions, multi-agent, applicability, reporting, UI/UX
- **Technical** (7): Architecture, MCP usage, in-house rewrite, version compat, wisdom, infrastructure, cross-workspace
- **Operational** (8): Testing, stability, DSP, autonomy, R&D gate, E2E testing, healthcheck, integrity

#### Phase Completions
- **Phase 1**: TypeDB container + schema + Python client
- **Phase 2**: Governance MCP Server (11 tools)
- **Phase 3**: Stabilization (hybrid router, sync bridge, benchmarks)
- **Phase 4**: Cross-workspace integration (Agno wrappers, session collector, DSM tracker)
- **Phase 5**: External MCP integration (21 tools: Playwright, PowerShell, Desktop Commander, OctoCode)
- **Phase 6**: Agent UI framework (Task UI, Trame frontend)
- **Phase 8**: E2E testing framework (Robot Framework + Playwright)

#### Infrastructure
- **5 containers**: Dashboard (8081), LiteLLM (4000), Ollama (11434), ChromaDB (8001), TypeDB (1729)
- **460+ tests** passing
- **Pre-commit hooks** for code quality

#### Tools & Integrations
- MCP to Agno @tool wrappers
- SessionCollector for evidence routing
- DSMTracker for Deep Sleep Protocol
- RuleQualityAnalyzer for orphan/conflict detection

### Changed
- Simplified architecture per DECISION-001 (removed Opik)
- TypeDB-First strategy per DECISION-003
- Document structure: modular rules, gaps, backlog

### Deprecated
- ChromaDB as primary storage (moved to TypeDB vectors in v1.1)

---

## [0.1.0] - 2024-12-24

### Added
- Initial project setup
- Docker compose stack
- Basic agent playground
- LiteLLM routing configuration
- ChromaDB knowledge base (53 docs from claude-mem)

---

*Per SESSION-EVID-01-v1: Session Evidence Logging*
