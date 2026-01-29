# ARCH-YAGNI-01-v1: Service Proliferation Guard

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL

> **Tags:** `architecture`, `design`, `yagni`, `critical-analysis`, `service-boundary`

---

## Directive

Before introducing a new service, microservice, or standalone component, a **5-dimension critical analysis** MUST be performed and documented. New services MUST NOT be created when existing modules satisfy all current requirements.

---

## Problem Statement

Service proliferation is a common failure mode in growing platforms. Each new service adds:
- Deployment complexity (container, health checks, restart policies)
- Network failure modes (timeouts, retries, circuit breakers)
- Serialization overhead (HTTP hops, JSON encoding/decoding)
- Test surface expansion (integration tests, contract tests)
- Operational burden (monitoring, logging, alerting)

The cost is paid immediately and permanently. The benefit is speculative until proven by unmet requirements.

---

## 5-Dimension Critical Analysis

Before proposing a new service, analyze across ALL five dimensions:

### 1. Architecture: Service Boundary Justification

| Question | Pass Criteria |
|----------|--------------|
| Does a new capability exist that no current module provides? | YES required |
| Does the new service have its own data ownership? | YES required |
| Would the new service have >1 consumer? | YES required |
| Is there a deployment independence requirement? | Documented justification |

**Anti-pattern**: Wrapping existing pure functions in an HTTP service adds a network hop with no new capability.

### 2. Design: Coupling Analysis

| Question | Pass Criteria |
|----------|--------------|
| Does the service avoid becoming a God Service? | Must serve ONE bounded context |
| Does it avoid duplicating domain knowledge from other services? | Zero duplication |
| Does it respect existing domain ownership (per ARCH-MCP-02-v1)? | No cross-domain encroachment |

**Anti-pattern**: A "document service" that must understand rules, tasks, sessions, and evidence violates single responsibility.

### 3. Quality: Cost/Benefit Accounting

| Metric | Must Quantify |
|--------|--------------|
| Lines of code added | Service + client + tests + routes + config |
| New failure modes introduced | Network, serialization, availability |
| Test categories required | Unit + integration + contract + E2E |
| Features gained vs. current solution | Must be >0 |

**Anti-pattern**: Adding ~1500 lines to wrap 679 lines of working code doubles maintenance with zero feature gain.

### 4. Resiliency: Failure Mode Enumeration

| Question | Pass Criteria |
|----------|--------------|
| How many new failure modes does the service introduce? | Enumerate ALL |
| What degrades when this service is down? | Document blast radius |
| Is the current solution's resiliency preserved? | No regression |
| Does the platform already have enough containers? | Justified addition only |

**Anti-pattern**: Converting a filesystem read (1 dependency) into a service call (4+ dependencies: network, service process, serialization, filesystem) strictly reduces resiliency.

### 5. Performance: Latency & Resource Impact

| Question | Pass Criteria |
|----------|--------------|
| What is the latency delta? | Measured, not estimated |
| Does the operation benefit from caching? | OS page cache may suffice |
| Is the operation on the critical path? | Justify if YES |

**Anti-pattern**: Adding 15-50ms HTTP overhead to a 1ms filesystem read for the most common operation.

---

## Decision Framework

```
All 5 dimensions analyzed?
├── NO  → BLOCK: Complete analysis first
└── YES → Count dimensions where new service WINS
          ├── 0-1 wins → REJECT: Existing solution sufficient
          ├── 2-3 wins → DISCUSS: Requires team review + documented rationale
          └── 4-5 wins → APPROVE: Clear justification exists
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Create service because "it might be useful later" | Prove unmet requirement exists NOW |
| Wrap pure functions in HTTP services | Keep pure functions, expose via existing API if needed |
| Add containers for capabilities that work as libraries | Libraries > services for same-process consumers |
| Skip critical analysis because "microservices are best practice" | Analyze context; monolith modules often superior at small scale |
| Create God Services spanning multiple domains | Respect domain boundaries per ARCH-MCP-02-v1 |
| Estimate performance impact | MEASURE performance impact |

---

## Validation

- [ ] 5-dimension analysis documented before any new service proposal
- [ ] Unmet requirement clearly identified (not speculative)
- [ ] Failure mode enumeration complete
- [ ] Latency impact measured (not estimated)
- [ ] Team review for borderline cases (2-3 dimension wins)

---

## Evidence: Document Service Analysis (2026-01-29)

Applied this framework to evaluate a "Document Management Service" proposal:

| Dimension | Result | Reasoning |
|-----------|--------|-----------|
| Architecture | REJECT | No new capability; MCP tools already CRUD-complete |
| Design | REJECT | Would become God Service spanning all domains |
| Quality | REJECT | +800 lines, zero features gained |
| Resiliency | REJECT | Adds container + network deps to 1ms filesystem reads |
| Performance | REJECT | 15-50x latency increase for most common operation |

**Verdict**: 0/5 dimensions favor new service. Existing MCP tools (679 lines, 6 tools) satisfy all requirements.

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per ARCH-BEST-01-v1: Separation of concerns, config over code*
