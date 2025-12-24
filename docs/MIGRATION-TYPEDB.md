# TypeDB Migration Strategy

**Created:** 2024-12-24
**Status:** Active
**Principle:** Zero-downtime migration - never break what works

---

## Core Principle

```
┌─────────────────────────────────────────────────────────────┐
│          ADDITIVE INTEGRATION, NOT REPLACEMENT              │
├─────────────────────────────────────────────────────────────┤
│  • TypeDB runs ALONGSIDE existing services                  │
│  • ChromaDB continues serving document search               │
│  • Rollback = remove TypeDB container, nothing else changes │
│  • Each phase has explicit success criteria before next     │
└─────────────────────────────────────────────────────────────┘
```

---

## Current State (Phase 0)

| Service | Port | Status | Data |
|---------|------|--------|------|
| Agents | 7777 | ✅ Running | Agent definitions |
| LiteLLM | 4000 | ✅ Running | Model routing |
| ChromaDB | 8001 | ✅ Running | 53 documents |
| Ollama | 11434 | ✅ Running | gemma models |

**What MUST keep working:**
- [ ] `pytest tests/test_health.py` passes
- [ ] Agent playground responds at :7777
- [ ] LiteLLM routes to Ollama
- [ ] ChromaDB queries return documents

---

## Phase 1: TypeDB Container (Current)

### Tasks

| ID | Task | Risk | Rollback |
|----|------|------|----------|
| P1.1 | Add TypeDB to docker-compose.yml | LOW | Remove service block |
| P1.2 | Create schema for 8 rules | LOW | N/A (additive) |
| P1.3 | Create Python TypeDB wrapper | LOW | Remove file |
| P1.4 | Test inference rule | LOW | N/A (additive) |
| P1.5 | Add TypeDB health check | LOW | Remove test |

### Docker Compose Addition

```yaml
services:
  # ... existing services unchanged ...

  typedb:
    image: vaticle/typedb:latest
    container_name: sim_typedb
    ports:
      - "1729:1729"
    volumes:
      - typedb_data:/opt/typedb-all-linux-x86_64/server/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:1729/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  typedb_data:
```

### Success Criteria (Must Pass Before Phase 2)

- [ ] TypeDB container starts successfully
- [ ] TypeDB health check passes
- [ ] Schema loaded with 8 rules
- [ ] At least 1 inference query returns results
- [ ] Existing tests still pass (no regression)

### Rollback Procedure

```powershell
# If TypeDB causes issues:
docker stop sim_typedb
docker rm sim_typedb

# Remove from docker-compose.yml (revert git changes)
git checkout docker-compose.yml

# Verify existing services still work
.\deploy.ps1 -Action health
```

---

## Phase 2: Hybrid Query Layer

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Request                            │
│                         │                                   │
│                    ┌────▼────┐                              │
│                    │  Router │                              │
│                    └────┬────┘                              │
│              ┌──────────┴──────────┐                        │
│              │                     │                        │
│         Semantic Query        Inference Query               │
│              │                     │                        │
│         ┌────▼────┐           ┌────▼────┐                   │
│         │ChromaDB │           │ TypeDB  │                   │
│         └─────────┘           └─────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Tasks

| ID | Task | Risk | Rollback |
|----|------|------|----------|
| P2.1 | Create hybrid query router | MEDIUM | Route all to ChromaDB |
| P2.2 | Migrate RULE-001 to RULE-008 | LOW | Keep in markdown |
| P2.3 | Migrate DECISION-001 to DECISION-004 | LOW | Keep in markdown |
| P2.4 | Add graph relationships | LOW | Delete from TypeDB |
| P2.5 | Test cross-query (search + inference) | LOW | N/A |

### Router Logic

```python
class HybridQueryRouter:
    def route(self, query: str, query_type: str):
        if query_type == "semantic":
            return self.chromadb.query(query)
        elif query_type == "inference":
            return self.typedb.query(query)
        elif query_type == "hybrid":
            # Semantic search first, then inference on results
            docs = self.chromadb.query(query)
            return self.typedb.infer(docs)
```

### Success Criteria

- [ ] Router correctly dispatches queries
- [ ] Rules queryable from TypeDB
- [ ] Inference: "find conflicting rules" works
- [ ] No regression in existing functionality

---

## Phase 3: Full Integration

### Tasks

| ID | Task | Risk | Rollback |
|----|------|------|----------|
| P3.1 | Agents use hybrid layer | HIGH | Revert agent code |
| P3.2 | TypeDB MCP server (optional) | LOW | Don't deploy |
| P3.3 | Performance benchmarks | LOW | N/A |
| P3.4 | Documentation update | LOW | N/A |
| P3.5 | v1.0 release | LOW | Tag only |

### Success Criteria

- [ ] Agents query TypeDB for rule inference
- [ ] Performance within acceptable bounds
- [ ] All tests pass
- [ ] Documentation complete

---

## Data Migration Plan

### What Stays in ChromaDB
- 53 existing documents (session dumps, memory)
- Future semantic search documents
- Agent context/memory

### What Goes to TypeDB
- 8 governance rules (RULE-001 to RULE-008)
- 4 strategic decisions (DECISION-001 to DECISION-004)
- Rule relationships (blocks, requires, supersedes)
- Task dependencies

### Migration Order

1. **Rules first** - Most structured, clear schema
2. **Decisions second** - Reference rules
3. **Tasks third** - Reference both
4. **Relationships last** - Connect entities

---

## Rollback Scenarios

| Scenario | Action | Impact |
|----------|--------|--------|
| TypeDB won't start | Remove from compose | None |
| TypeDB crashes prod | Stop container | ChromaDB continues |
| Inference returns wrong results | Disable inference queries | ChromaDB fallback |
| Performance too slow | Cache or disable TypeDB | ChromaDB fallback |

---

## Health Check Matrix

| Phase | ChromaDB | TypeDB | Hybrid | Required |
|-------|----------|--------|--------|----------|
| 0 | ✅ | - | - | ChromaDB only |
| 1 | ✅ | ✅ | - | Both independent |
| 2 | ✅ | ✅ | ✅ | All three |
| 3 | ✅ | ✅ | ✅ | All three |

---

## Verification Commands

```powershell
# Phase 0 - Current
.\deploy.ps1 -Action health

# Phase 1 - With TypeDB
docker ps | findstr typedb
Invoke-WebRequest -Uri "http://localhost:1729/health"

# Phase 2 - Hybrid
python -c "from agent.hybrid_router import HybridRouter; print(HybridRouter().health())"

# All Phases - Regression
pytest tests/test_health.py -v
```

---

*Reference: [SESSION-DECISIONS-2024-12-24.md](../evidence/SESSION-DECISIONS-2024-12-24.md)*
