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

*Per RULE-008: In-House Rewrite Principle*
