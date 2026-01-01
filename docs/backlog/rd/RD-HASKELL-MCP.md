# R&D: Haskell Inference MCP (RD-001 to RD-005)

**Status:** ON HOLD
**Priority:** FUTURE
**Note:** Per user directive - begin after strategic agentic platform complete

---

## Strategic Vision

Learn inference domain deeply through Haskell implementation before considering optimizations. This follows the principle: "Implement first to become domain experts."

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| RD-001 | Haskell inference MCP prototype | 📋 TODO | **FUTURE** | After strategic agentic platform |
| RD-002 | Benchmark Python vs Haskell | 📋 TODO | FUTURE | After RD-001 |
| RD-003 | Rust rewrite decision | ⏸️ BLOCKED | LOW | Requires RD-002 benchmarks |
| RD-004 | Robotics inference compatibility | 📋 TODO | FUTURE | ROS2/embedded targets |
| RD-005 | TypeDB 3.x alpha evaluation | 📋 TODO | LOW | Monitor releases |

---

## Language Decision Matrix

| Factor | Python | Haskell | Rust |
|--------|--------|---------|------|
| **Learning** | ✅ Done | 🎯 Next | ⏳ Later |
| **Inference elegance** | ⚠️ Imperative | ✅ Natural | ⚠️ Manual |
| **Python FFI** | Native | HTTP/gRPC | PyO3 |
| **Robotics/ROS** | rospy | ❌ Hard | ✅ ros2-rust |
| **MCP deploy** | ✅ Easy | ⚠️ Runtime | ✅ Small binary |

---

## Phase Strategy

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

---

## Haskell MCP Interface (Target)

```haskell
-- Servant API for inference MCP
type InferenceAPI =
       "query" :> ReqBody '[JSON] Query :> Post '[JSON] QueryResult
  :<|> "deps"  :> Capture "ruleId" Text :> Get '[JSON] [RuleId]
  :<|> "conflicts" :> Get '[JSON] [Conflict]
  :<|> "health" :> Get '[JSON] HealthStatus
```

---

## Trigger Conditions

**Trigger for Haskell development:**
- Strategic agentic platform (Phase 9) complete
- All agent orchestration (ORCH-001-007) functional

**Trigger for Rust rewrite:**
- Haskell inference >10ms on 1K rules
- Need WASM/embedded deployment
- Team prefers Rust ecosystem

---

## Evidence

- TypeDB 3.x: Has native vector support
- Current Python: Working, validates business logic
- Decision: Learn before optimize

*Per RULE-012 DSP: Haskell R&D documented, ON HOLD*
