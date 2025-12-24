# R&D Backlog - Sim.ai PoC

**Last Updated:** 2024-12-24
**Status:** Active Development

---

## Strategic Vision: Private Cluster AI Platform

**Goal:** Self-hosted platform with MCPs & UIs on private cluster

### Platform Pillars

| Pillar | Components | Current | Target |
|--------|------------|---------|--------|
| **Agents** | Orchestration, routing, playground | ✅ Agno/LiteLLM | TypeDB-enhanced |
| **Tasks/Projects** | Backlog, tracking, dependencies | ✅ Split docs | TypeDB graph |
| **Evidence/Sessions** | Decisions, logs, dumps | ✅ Markdown/scripts | Structured DB |
| **Rules** | RULE-001 to RULE-014 | ✅ TypeDB + Markdown | TypeDB inference |

### Architecture Target

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
│       │   └── Documents (53)  │  └── Rules (14) + Decisions    │
│       │                       │                                 │
│       └── HYBRID QUERY LAYER ─┴─────────────────────────────   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase Status

### Phase 1: TypeDB Container ✅ COMPLETE

- TypeDB running on port 1729
- Schema + 6 inference rules
- Python client (2.29.x driver)
- 68 tests passing
- 14 rules, 4 decisions, 3 agents

### Phase 2: Governance MCP ✅ COMPLETE

- Governance MCP server (11 tools)
- Multi-agent governance (RULE-011)
- Document cross-referencing (RULE-013)
- Rule dependencies tracked

### Phase 3: Stabilization (IN PROGRESS)

| Task | Status | Description |
|------|--------|-------------|
| P3.1 | ✅ DONE | Hybrid query router (TypeDB + ChromaDB) |
| P3.2 | ✅ DONE | Integration tests for MCP-TypeDB |
| P3.3 | ✅ DONE | ChromaDB sync bridge (rules, decisions, agents) |
| P3.4 | 📋 TODO | Update agents to use hybrid layer |
| P3.5 | 📋 TODO | Performance benchmarks |
| P3.6 | 📋 TODO | v1.0 release |

---

## Deferred Items

| Item | Status | Notes |
|------|--------|-------|
| Mem0 / OpenMemory MCP | ⏸️ DEFERRED | Superseded by TypeDB |
| Replace Agno with Memory MCP | ⏸️ DEFERRED | Pending TypeDB outcome |
| Custom Session/Memory UI | ⏸️ DEFERRED | After TypeDB validation |
| MCP-Monitor | LOW | Nice-to-have |
| AnythingLLM | LOW | Evaluate later |

---

## Strategic R&D: Custom Inference Engine

**Context:** TypeDB 3.x is ALPHA. We use stable 2.29.1.

### DIRECTIVE: Learn Before Optimize

> **Principle:** Implement Haskell MCP service first to become domain experts
> before attempting creative optimizations. Test coverage validates dependencies.

```
Phase 1: Python (current) ──→ Validate logic, gather requirements
         │
Phase 2: Haskell MCP ──────→ Learn inference domain deeply
         │                   └── Lazy eval, pattern matching, type safety
         │
Phase 3: Optimize ─────────→ Rust rewrite ONLY if benchmarks demand
         │                   └── PyO3 bindings, sub-ms latency
         │
Phase 4: Robotics ─────────→ Compatible inference for embedded/ROS
```

### Language Decision Matrix

| Factor | Python | Haskell | Rust |
|--------|--------|---------|------|
| **Learning** | ✅ Done | 🎯 Next | ⏳ Later |
| **Inference elegance** | ⚠️ Imperative | ✅ Natural | ⚠️ Manual |
| **Python FFI** | Native | HTTP/gRPC | PyO3 |
| **Robotics/ROS** | rospy | ❌ Hard | ✅ ros2-rust |
| **MCP deploy** | ✅ Easy | ⚠️ Runtime | ✅ Small binary |

### R&D Tasks

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| RD-001 | Haskell inference MCP prototype | 📋 TODO | HIGH | Learn domain via Servant API |
| RD-002 | Benchmark Python vs Haskell | 📋 TODO | MEDIUM | After RD-001 |
| RD-003 | Rust rewrite decision | ⏸️ BLOCKED | LOW | Requires RD-002 benchmarks |
| RD-004 | Robotics inference compatibility | 📋 TODO | FUTURE | ROS2/embedded targets |
| RD-005 | TypeDB 3.x alpha evaluation | 📋 TODO | LOW | Monitor releases |

### Haskell MCP Interface (Target)

```haskell
-- Servant API for inference MCP
type InferenceAPI =
       "query" :> ReqBody '[JSON] Query :> Post '[JSON] QueryResult
  :<|> "deps"  :> Capture "ruleId" Text :> Get '[JSON] [RuleId]
  :<|> "conflicts" :> Get '[JSON] [Conflict]
  :<|> "health" :> Get '[JSON] HealthStatus
```

### Why This Order?

1. **Python**: Already working, validates business logic
2. **Haskell**: Forces deep understanding of inference patterns
3. **Rust**: Only if latency <1ms is required (measure first!)
4. **Robotics**: Long-term - inference on edge devices

**Trigger for Rust rewrite:**
- Haskell inference >10ms on 1K rules
- Need WASM/embedded deployment
- Team prefers Rust ecosystem

---

*R&D tracking per RULE-010: Evidence-Based Wisdom*
