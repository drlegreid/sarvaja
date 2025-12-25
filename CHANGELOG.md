# Changelog

All notable changes to sim-ai are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **5 Docker containers**: Agents (7777), LiteLLM (4000), Ollama (11434), ChromaDB (8001), TypeDB (1729)
- **460+ tests** passing
- **Pre-commit hooks** for code quality

#### Tools & Integrations
- MCP to Agno @tool wrappers
- SessionCollector for evidence routing
- DSMTracker for Deep Sleep Protocol
- RuleQualityAnalyzer for orphan/conflict detection
- LangGraph workflow state machines
- Pydantic AI type-safe tools

### Changed
- Simplified architecture per DECISION-001 (removed Opik)
- TypeDB-First strategy per DECISION-003
- Document structure: modular rules, gaps, backlog

### Deprecated
- ChromaDB as primary storage (moving to TypeDB vectors in v1.1)

---

## [0.1.0] - 2024-12-24

### Added
- Initial project setup
- Docker compose stack
- Basic agent playground
- LiteLLM routing configuration
- ChromaDB knowledge base (53 docs from claude-mem)

---

*Per RULE-001: Session Evidence Logging*
