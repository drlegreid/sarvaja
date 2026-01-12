# Architecture Rules - Sim.ai

Rules governing system architecture, infrastructure, and MCP server patterns.

> **Parent:** [RULES-TECHNICAL.md](../RULES-TECHNICAL.md)
> **Rules:** RULE-002, RULE-016, RULE-036

---

## RULE-002: Architectural & Design Best Practices

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

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

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Hardcode secrets in source | Use `.env` and environment variables |
| Create circular imports | Refactor to clear layer boundaries |
| Skip health endpoints | Add `/health` to every service |
| Ignore errors silently | Log and provide fallback behavior |
| Write non-idempotent operations | Use upsert patterns for retries |

---

## RULE-016: Infrastructure Identity & Hardware Metadata

**Category:** `devops` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

All infrastructure components MUST be identifiable via metadata for digital twin management.

### Infrastructure Registry

| Component | Role | Port |
|-----------|------|------|
| agents | Agno runtime | 7777 |
| chromadb | Vector storage | 8001 |
| typedb | Graph inference | 1729 |
| litellm | Model routing | 4000 |
| ollama | Local inference | 11434 |

### Hardware Resource Limits

| Container | Memory | CPU | Purpose |
|-----------|--------|-----|---------|
| agents | 1G | - | Agno agent runtime |
| litellm | 512M | - | Model routing proxy |
| chromadb | 1G | - | Vector storage |
| typedb | 2G | - | Graph database |
| ollama | 4G | 2 | Local inference |

### Deployment Identity

```yaml
deployment_identity:
  deployment_id: "{project}-{date}-{env}"
  host_fingerprint: "{cpu}-{ram}-{os}"
  cluster_signature: md5(containers)
  mcp_profile: [active_mcp_names]
```

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Run untracked containers | Register in infrastructure registry |
| Exceed memory limits without reason | Document resource requirements |
| Deploy without identity metadata | Include deployment_id in logs |
| Skip port documentation | Maintain port registry table |

---

## RULE-036: MCP Server Separation Pattern

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** REQUIRED

### Directive

Large MCP servers (>50 tools) MUST be split into domain-specific servers.

### Server Domains

| Domain | Server | Tools |
|--------|--------|-------|
| Core | `governance-core` | Rules, decisions, health |
| Agents | `governance-agents` | Agents, trust, proposals |
| Sessions | `governance-sessions` | Sessions, DSM, evidence |
| Tasks | `governance-tasks` | Tasks, workspace, gaps |

### Requirements

1. Each server has own entry point (`mcp_server_{domain}.py`)
2. Tool modules split per RULE-032 (<300 lines)
3. Keep unified server for backward compatibility
4. Add all servers to `.mcp.json`

### Validation
- [ ] Each server imports <300 lines
- [ ] Each server starts independently
- [ ] Unified server still works
- [ ] Tests validate all servers

### Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Keep monolith MCP with >50 tools | Split into domain-specific servers |
| Create files >300 lines | Split per RULE-032 |
| Remove unified server immediately | Keep for backward compatibility |
| Skip server independence tests | Verify each server starts alone |

---

*Per RULE-012: DSP Semantic Code Structure*
