# Technical Rules - Sim.ai

Rules governing architecture, technology selection, and tooling.

---

## RULE-002: Architectural & Design Best Practices

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All code and system design MUST follow:

1. **Separation of Concerns** - Single responsibility, clear layer boundaries
2. **Configuration Over Code** - Environment variables, YAML configs
3. **Observability by Default** - Health endpoints, structured logging
4. **Graceful Degradation** - Fallback models, retries, timeouts
5. **Idempotency** - Retriable operations, upsert patterns
6. **Documentation** - README per component, API contracts

### Validation
- [ ] No circular imports detected
- [ ] All secrets in `.env` (not in code)
- [ ] Health endpoint returns 200
- [ ] Session dump created

---

## RULE-007: MCP Usage Protocol

**Category:** `productivity` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

All sessions MUST actively leverage available MCPs according to task type.

### MCP Usage Matrix

| Task Type | Required MCPs | Optional MCPs |
|-----------|---------------|---------------|
| **Session Start** | claude-mem, filesystem | sequential-thinking |
| **Code Research** | octocode, filesystem | claude-mem |
| **Implementation** | filesystem, powershell | llm-sandbox, git |
| **Testing** | playwright, powershell | desktop-commander |
| **Complex Analysis** | sequential-thinking | claude-mem |

### Active MCPs Reference

| MCP | Purpose |
|-----|---------|
| **claude-mem** | Memory persistence (ChromaDB) |
| **octocode** | GitHub code search |
| **playwright** | Browser automation |
| **sequential-thinking** | Structured reasoning |
| **desktop-commander** | File/process ops |
| **filesystem** | File operations |
| **git** | Version control |
| **powershell** | Windows automation |
| **llm-sandbox** | Code execution |

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| Manual GitHub search | Use octocode MCP |
| Copy-paste context | Query claude-mem |
| Ad-hoc decisions | Use sequential-thinking |
| Bash for file ops | Use filesystem MCP |

### Validation
- [ ] Session starts with claude-mem context query
- [ ] Research tasks use octocode
- [ ] Complex decisions use sequential-thinking

---

## RULE-008: In-House Rewrite Principle

**Category:** `strategic` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

When selecting technologies, prefer solutions with:
1. Comprehensive test suites (rewrite warranty)
2. Open-source with permissive licenses
3. Active development and community
4. Can be ported/rewritten in-house

### Technology Selection Scorecard

```yaml
technology_evaluation:
  name: "<technology>"
  scores:  # 1-5 scale
    test_coverage: 0
    license_freedom: 0
    active_development: 0
    documentation: 0
    rewrite_feasibility: 0
  total_score: 0  # max 25
  recommendation: "ADOPT | EVALUATE | REJECT"
```

### Validation
- [ ] Technology scorecard completed before adoption
- [ ] Test suite reviewed and understood
- [ ] License verified compatible
- [ ] OctoCode research performed

---

## RULE-009: DevOps Version Compatibility Protocol

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Before installing ANY package:
1. Check container/service version FIRST
2. Use OctoCode to find compatible versions
3. Use llm-sandbox for isolated testing
4. Verify version matrix

### Version Check Protocol

| Step | Tool | Command |
|------|------|---------|
| Container version | Bash | `docker logs <container> \| grep version` |
| Client compatibility | OctoCode | Search repo for version matrix |
| Isolated testing | llm-sandbox | Test import before global install |
| Dependency conflicts | pip | `pip check` after install |

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| `pip install <pkg>` without version | Check server version first |
| Install to global Python | Use venv or llm-sandbox |
| Guess package names | OctoCode search |

### Validation
- [ ] Container version checked before client install
- [ ] OctoCode used for version compatibility
- [ ] No global Python pollution

---

## RULE-010: Evidence-Based Wisdom Accumulation

**Category:** `strategic` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

Every experiment MUST produce traceable evidence:
1. Use MCPs for detailed evidence
2. Hypothesis-based approach
3. Logical decision making
4. Test-caught failures = learning opportunities

### Evidence Pipeline

```
MCP Output → Evidence Collection → Logical Analysis → Decision → TypeDB Rule
```

### Wisdom Accumulation Principle

```
Wisdom = Σ(Evidence × Validation)
Stupidity = Σ(Assumptions × Untested)
```

### MCP Usage for Evidence

| Evidence Type | MCP Tool |
|---------------|----------|
| API exploration | llm-sandbox |
| Version checks | powershell |
| Code patterns | OctoCode |
| Memory storage | claude-mem |

### Validation
- [ ] MCPs used instead of manual operations
- [ ] Hypothesis documented before testing
- [ ] Evidence collected in structured format
- [ ] Successful patterns encoded as rules

---

## RULE-016: Infrastructure Identity & Hardware Metadata

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE

### Directive

All infrastructure components MUST be identifiable via metadata for digital twin management. Hardware specifications enable reproducible environments and capacity planning.

### Infrastructure Registry

```yaml
infrastructure:
  host:
    id: "natik-laptop-i7"
    hardware:
      cpu: "Intel Core i7"
      ram: "16GB"
      storage: "SSD"
      gpu: "None (CPU-only)"
    os: "Windows 11"
    roles: ["development", "docker-host", "mcp-host"]

  clusters:
    sim-ai:
      type: "docker-compose"
      containers:
        - name: agents-1
          image: sim-ai-agents
          port: 7777
          role: "agno-agent-runtime"
        - name: chromadb-1
          image: chromadb/chroma
          port: 8001
          role: "vector-storage"
        - name: typedb-1
          image: vaticle/typedb
          port: 1729
          role: "graph-inference"
        - name: litellm-1
          image: ghcr.io/berriai/litellm
          port: 4000
          role: "model-routing"
        - name: ollama-1
          image: ollama/ollama
          port: 11434
          role: "local-inference"

    agno-agi:
      type: "docker-compose"
      source: "C:\Users\natik\Documents\Vibe\agno-agi"
      containers:
        - name: agents
          port: 7777
        - name: agent-ui
          port: 3000
        - name: chromadb
          port: 8001

  mcp_servers:
    runtime: "claude-code-native"
    servers:
      - name: claude-mem
        type: stable
        backend: chromadb
      - name: playwright
        type: moderate
        backend: browser
      - name: godot-mcp
        type: conditional
        backend: godot-editor
      - name: desktop-commander
        type: moderate
        backend: native
      - name: sequential-thinking
        type: stable
        backend: memory
```

### Hardware Resource Limits

| Container | Memory | CPU | Purpose |
|-----------|--------|-----|---------|
| agents | 1G | - | Agno agent runtime |
| litellm | 512M | - | Model routing proxy |
| chromadb | 1G | - | Vector storage |
| typedb | 2G | - | Graph database |
| ollama | 4G | 2 | Local inference |

### Digital Twin Identity Protocol

Every deployment MUST include:

```yaml
deployment_identity:
  deployment_id: "{project}-{date}-{env}"  # sim-ai-2024-12-24-dev
  host_fingerprint: "{cpu}-{ram}-{os}"      # i7-16gb-win11
  cluster_signature: md5(containers)         # Unique per config
  mcp_profile: [active_mcp_names]            # Current MCP set
```

### Cross-Workspace Coordination

| Workspace | Cluster | Host |
|-----------|---------|------|
| sim-ai | sim-ai-* | natik-laptop-i7 |
| agno-agi | agno-agi-* | natik-laptop-i7 |
| local-gai | MCP-only | natik-laptop-i7 |
| angelgai | Watchdog | natik-laptop-i7 |

### Validation
- [ ] Infrastructure registry up-to-date
- [ ] All containers have defined resource limits
- [ ] Deployment identity logged in session
- [ ] Hardware fingerprint matches deployment

---

## RULE-017: Cross-Workspace Pattern Reuse

**Category:** `strategic` | **Priority:** HIGH | **Status:** ACTIVE

### Directive

Before implementing new functionality, check cross-workspace wisdom index for existing patterns.

### Pattern Sources

| Source | Path | Patterns |
|--------|------|----------|
| **local-gai** | `C:\Users\natik\Documents\Vibe\localgai` | EBMSF, DSM, MCP wrappers |
| **agno-agi** | `C:\Users\natik\Documents\Vibe\agno-agi` | Base Agno cluster |
| **sim-ai** | Current | TypeDB hybrid, Governance MCP |

### Reuse Checklist

Before implementing:
- [ ] Checked CROSS-WORKSPACE-WISDOM.md
- [ ] Searched claude-mem for similar patterns
- [ ] Reviewed related workspace evidence

### Pattern Categories

| Category | Documents | Tools |
|----------|-----------|-------|
| MCP Wrappers | docker_wrapper.py, godot_wrapper.py | Dependency auto-start |
| Type-Safe Tools | pydantic_tools.py | Pydantic AI + FastMCP |
| State Machines | langgraph_workflow.py | LangGraph |
| Evidence Tracking | dsm_tracker.py | DSM phases |
| Health Monitoring | watchdog_rules | Memory thresholds |

### Validation
- [ ] Cross-workspace search performed
- [ ] Existing patterns leveraged
- [ ] New patterns documented for reuse

---

## RULE-025: Test Data Integrity Requirements

**Category:** `testing` | **Priority:** HIGH | **Status:** DRAFT

### Directive

All tests that verify UI functionality MUST include API data validation assertions. A test that passes with empty data is not a valid test.

### Requirements

1. **API Data Validation**: Before UI validation, verify API returns non-empty data
2. **Fail on Empty**: If data is empty, test MUST FAIL with diagnostic message
3. **No Skipped Data Assertions**: E2E tests must not skip data-dependent assertions
4. **Realistic Mocks**: Mocks must return realistic data, not empty collections

### Anti-Patterns

| ❌ Don't | ✅ Do Instead |
|----------|---------------|
| `assert isinstance(result, list)` | `assert len(result) > 0, "Expected data from API"` |
| `@skipif(True, reason="Requires DB")` | Only skip after checking availability |
| `mock.return_value = []` | `mock.return_value = [realistic_test_data]` |
| Test imports only | Test actual data display |
| Test type returns | Test content correctness |

### Exploratory Test Heuristics

Per user feedback: "Exploratory tests should have exposed gaps long ago"

| Heuristic | Implementation |
|-----------|----------------|
| **API Data Available** | Query API, verify >0 items before UI test |
| **Data Visible** | If API returns data, UI MUST display it |
| **Empty State Handled** | If API empty, UI shows "No data" message |
| **Linked Data Present** | Related entities should show relationships |
| **CRUD Complete** | Create → Read → Update → Delete works end-to-end |

### Validation

- [ ] No tests with empty assertions pass
- [ ] All E2E tests verify data availability first
- [ ] Exploratory tests log findings to GAP-INDEX.md
- [ ] Failed heuristics create new gaps

### Evidence

- GAP-UI-028: "Tests pass but UI broken (lenient tests)"
- User feedback: "for me UI is still a toy"
- Exploratory test session EXP-P10-001

---

*Per RULE-008: In-House Rewrite Principle*
