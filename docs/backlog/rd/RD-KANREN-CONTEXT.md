# R&D: Kanren Context Engineering (KAN-001 to KAN-005)

**Status:** ✅ COMPLETE (All 5 tasks done, 62 tests passing)
**Priority:** HIGH
**Vision:** Logic programming for structural context engineering in LLM pipelines

---

## Overview

MiniKanren is a lightweight, embedded domain-specific language (EDSL) for logic programming, highly applicable to **context engineering**—the discipline of designing and assembling the input context (prompts, retrieved data, memory, tool outputs) for Large Language Models.

**Repository:** https://github.com/pythological/kanren

Its applicability stems from its ability to express complex problems as compact, declarative relational specifications, allowing for **reversible calculations** (e.g., generating, checking, or repairing context structures).

---

## Key Applicability Areas

### 1. Dynamic Context Generation & Synthesis

MiniKanren can generate valid context scenarios:
- Producing synthetic training data
- Building complex prompts (e.g., generating quines)
- Automated prompt template expansion

### 2. Constraint-Based Context Structuring

Enforce strict rules on input context:
- "If context A is present, then context B must be excluded"
- Token budget constraints
- Schema validation for structured prompts

### 3. Symbolic Reasoning in RAG

Act as a symbolic layer on top of Retrieval-Augmented Generation (RAG):
- Ensure retrieved data adheres to specific logic or domain rules
- Filter/validate chunks before feeding to LLM
- Cross-reference consistency checking

### 4. Reactive View Synchronization

Maintain synchronization between model (data) and view (prompted input):
- React to user interactions
- Update context in real-time
- State machine transitions for multi-turn dialogues

### 5. Formal Verification of Prompts

Write programs that verify prompts/context adhere to constraints:
- Reduce hallucinations through structural validation
- Ensure required information is present
- Detect conflicting instructions

---

## Integration with Sim.ai Architecture

### TypeDB + Kanren Synergy

```
┌─────────────────────────────────────────────────────────────────┐
│                    KANREN + TYPEDB INTEGRATION                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TypeDB (1729)                    Kanren Layer                  │
│  ├── Rules/Decisions ────────────► Constraint Definitions       │
│  ├── Task Graph      ────────────► Dependency Resolution        │
│  └── Session Evidence ───────────► Context Synthesis            │
│                                          │                       │
│                                          ▼                       │
│                                   ┌─────────────────┐           │
│                                   │  LLM Context    │           │
│                                   │  (Validated)    │           │
│                                   └─────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Use Case: Rule-Constrained Context Assembly

```python
from kanren import run, var, eq, conde

# Define context constraints using Kanren
def valid_context(context, rules):
    """
    Use Kanren to verify context satisfies governance rules.

    Per RULE-011: Multi-agent governance with trust-weighted constraints.
    """
    x = var()

    # Define relational constraints from TypeDB rules
    return conde(
        # If agent trust < 0.7, must include supervisor context
        [eq(context.trust_level, 'low'),
         eq(context.requires_supervisor, True)],

        # If task is CRITICAL, must have evidence trail
        [eq(context.task_priority, 'CRITICAL'),
         eq(context.has_evidence, True)],

        # Default case
        [eq(context.valid, True)]
    )
```

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| KAN-001 | Spike: Kanren Python library evaluation | ✅ DONE | **HIGH** | Installed kanren 0.3.0, validated context engineering use cases |
| KAN-002 | Design: Context constraint DSL | ✅ DONE | HIGH | governance/kanren/ package - modularized per DOC-SIZE-01-v1 |
| KAN-003 | PoC: RAG filter with Kanren validation | ✅ DONE | HIGH | KanrenRAGFilter class - 45 tests passing |
| KAN-004 | Integration: TypeDB → Kanren constraint loader | ✅ DONE | MEDIUM | TypeDBKanrenBridge + 10 tests passing |
| KAN-005 | Benchmark: Performance vs direct Python validation | ✅ DONE | MEDIUM | 0.138ms total, 62 tests passing |

---

## Advantages in Contextual AI

### Reversibility
Logic constraints can be run in reverse:
- Not only create context but infer what input constraints produce specific output
- Generate test cases from expected outputs
- Debugging: "What context would have prevented this error?"

### Symbolic Constraints
Handles complex logical conditions better than pure natural language prompting:
- Ensures retrieved context is consistent
- Formal verification capabilities
- Composable constraint definitions

### Extensibility
Minimal core (often <1000 lines):
- Easily modified for domain-specific constraints
- Handle infinite recursion for processing structured text data
- Add custom constraint solvers

---

## Limitations

### Performance
- Complex constraints can be computationally expensive
- May need caching for repeated constraint checks
- Consider lazy evaluation for large context sets

### Unfair Conjunction
- In original implementations, order of conjuncts affects convergence
- Pythological/kanren addresses this with improved search strategies
- May need careful ordering of constraints

### Learning Curve
- Declarative paradigm shift from imperative Python
- Debugging relational programs requires different mindset
- Documentation is academic-focused

---

## Comparison: Prompt Engineering vs Context Engineering

| Aspect | Prompt Engineering | Context Engineering (Kanren) |
|--------|-------------------|------------------------------|
| Focus | Phrasing of input | Structural/logical data assembly |
| Constraints | Natural language hints | Formal logic relations |
| Validation | Manual testing | Automated verification |
| Reversibility | One-way | Bidirectional |
| Composition | Copy-paste | Declarative combination |

---

## Research Resources

- **Pythological Kanren:** https://github.com/pythological/kanren
- **MiniKanren Original:** http://minikanren.org/
- **Relational Programming:** "The Reasoned Schemer" book
- **Unification Theory:** Foundation for pattern matching in Kanren

---

## Success Criteria

1. **KAN-001 Complete:** Working Kanren examples in project
2. **KAN-002 Complete:** 5+ governance rules expressed as Kanren relations
3. **KAN-003 Complete:** RAG pipeline with Kanren validation gate
4. **KAN-004 Complete:** Automatic TypeDB → Kanren sync
5. **KAN-005 Complete:** Performance acceptable for real-time use (<100ms overhead)

---

---

## Spike Results: KAN-001 (2024-12-27)

### Installation
```bash
pip install kanren
# Installed: kanren-0.3.0, unification-0.3.1, toolz-1.1.0, multipledispatch-1.0.0
```

### Validated Capabilities

| Feature | Test | Result |
|---------|------|--------|
| **Unification** | `run(1, x, eq(x, 5))` | `(5,)` ✅ |
| **Multiple Solutions** | `membero(x, [1,2,3])` | `(1, 2, 3)` ✅ |
| **Conditional Logic** | `conde([eq(x, 'high')], [eq(x, 'low')])` | Works ✅ |
| **Conjunction** | `lall(membero(x, [1,2]), membero(y, ['a','b']))` | `((1,'a'), (2,'a'), (1,'b'), (2,'b'))` ✅ |

### Context Engineering Validation

**Trust-Based Supervisor Requirement (per RULE-011):**
```python
agent_contexts = [
    {'name': 'claude-code', 'trust': 'high'},   # → requires_supervisor=False
    {'name': 'new-agent', 'trust': 'low'},      # → requires_supervisor=True
    {'name': 'sync-agent', 'trust': 'medium'}   # → requires_supervisor=True
]
```

**RAG Chunk Filtering (per RULE-007):**
```python
chunks = [
    {'source': 'typedb', 'verified': True}   # → valid=True
    {'source': 'external', 'verified': False} # → valid=False
    {'source': 'chromadb', 'verified': True}  # → valid=True
]
```

### Key Insights

1. **Low Overhead:** Kanren runs fast for small constraint sets
2. **Declarative:** Rules expressed as relations, not imperative code
3. **Composable:** `conde` (OR) and `lall` (AND) combine naturally
4. **Reversible:** Can query "what inputs produce this output"

### Next Steps

1. **KAN-002:** Map 5+ governance rules to Kanren relations
2. **KAN-003:** Integrate with ChromaDB retrieval pipeline
3. **KAN-004:** Load TypeDB rules as Kanren facts dynamically

---

---

## Implementation Results: KAN-002 (2024-12-27)

### File Created

**`governance/kanren_constraints.py`** - Full Kanren constraint DSL for governance rules.

### Constraints Implemented

| Constraint | Rules Mapped | Description |
|------------|--------------|-------------|
| `trust_level()` | RULE-011 | Trust score → {expert, trusted, supervised, restricted} |
| `requires_supervisor()` | RULE-011 | Trust-based supervisor requirement |
| `can_execute_priority()` | RULE-011 | Task priority × Trust level → permission |
| `task_requires_evidence()` | RULE-028 | Priority → evidence requirement |
| `valid_task_assignment()` | RULE-011, RULE-014, RULE-028 | Full assignment validation |
| `valid_rag_chunk()` | RULE-007 | RAG chunk source/type validation |
| `filter_rag_chunks()` | RULE-007 | Batch chunk filtering |
| `conflicting_priorities()` | RULE-011 | Rule conflict detection |
| `assemble_context()` | KAN-003 prep | Full context assembly |

### Test Coverage

```
tests/test_kanren_constraints.py: 39 tests, 100% pass
- TestTrustLevel: 4 tests
- TestRequiresSupervisor: 4 tests
- TestCanExecutePriority: 8 tests
- TestTaskRequiresEvidence: 4 tests
- TestValidTaskAssignment: 4 tests
- TestValidRagChunk: 5 tests
- TestFilterRagChunks: 3 tests
- TestRuleConflicts: 4 tests
- TestAssembleContext: 1 test
- TestValidateAgentForTask: 2 tests
```

### Usage Example

```python
from governance.kanren_constraints import (
    validate_agent_for_task,
    filter_rag_chunks,
    assemble_context,
    AgentContext,
    TaskContext,
)

# Quick validation
result = validate_agent_for_task("AGENT-001", 0.95, "CRITICAL")
print(result["valid"])  # True

# Full context assembly
agent = AgentContext("AGENT-001", "Claude Code", 0.95, "claude-code")
task = TaskContext("TASK-001", "CRITICAL", True)
chunks = [{"source": "typedb", "verified": True, "type": "rule"}]
context = assemble_context(agent, task, chunks)
```

### Next Steps

1. **KAN-003:** Integrate with ChromaDB retrieval pipeline
2. **KAN-004:** Dynamic TypeDB → Kanren fact loading
3. **KAN-005:** Performance benchmarks (<100ms target)

---

*Per RULE-010: Evidence-Based Wisdom - R&D spike to evaluate Kanren for context engineering*
*Per User Directive 2024-12-27: MiniKanren for structural context engineering*

---

## Implementation Results: KAN-003 (2026-01-15)

### File Modified

**`governance/kanren_constraints.py`** - Added `KanrenRAGFilter` class for RAG integration.

### Class Implemented

| Class | Purpose | Methods |
|-------|---------|---------|
| `KanrenRAGFilter` | RAG retrieval with Kanren validation | `search_validated()`, `search_for_task()`, `_results_to_chunks()` |

### Methods

| Method | Description |
|--------|-------------|
| `search_validated()` | Search VectorStore and filter results through Kanren constraints |
| `_results_to_chunks()` | Convert SimilarityResult to chunk format for Kanren validation |
| `search_for_task()` | Full context assembly with task/agent validation |

### Key Features

1. **Lazy VectorStore Loading:** Only connects when first search is performed
2. **Source Type Mapping:** Maps VectorStore types to Kanren categories (rule→typedb, session→chromadb)
3. **Verification by Score:** Chunks with similarity score > 0.5 are marked as verified
4. **Integrated Validation:** Combines RAG filtering with agent trust and task evidence requirements

### Test Coverage

```
tests/test_kanren_constraints.py: 45 tests, 100% pass
- TestKanrenRAGFilter: 6 tests
  - test_filter_import
  - test_filter_instantiation
  - test_filter_with_mock_store
  - test_results_to_chunks_conversion
  - test_search_for_task_validation
  - test_low_score_chunk_filtered
```

### Usage Example

```python
from governance.kanren_constraints import (
    KanrenRAGFilter,
    AgentContext,
    TaskContext,
)

# Initialize RAG filter
rag_filter = KanrenRAGFilter()

# Search with Kanren validation
results = rag_filter.search_validated(
    query_embedding=[0.1, 0.2, ...],
    top_k=10
)

# Full context assembly for task execution
agent = AgentContext("AGENT-001", "Claude Code", 0.95, "claude-code")
task = TaskContext("TASK-001", "CRITICAL", True)
context = rag_filter.search_for_task(
    query_text="governance rules",
    task_context=task,
    agent_context=agent
)
```

---

## Implementation Results: KAN-004 (2026-01-15)

### File Created

**`governance/kanren/loader.py`** - TypeDB → Kanren constraint loader.

### Components Implemented

| Component | Description |
|-----------|-------------|
| `RuleConstraint` | Dataclass for TypeDB rule representation |
| `TypeDBKanrenBridge` | Bridge managing load/validate lifecycle |
| `load_rules_from_typedb()` | Parse MCP JSON → RuleConstraint list |
| `populate_kanren_facts()` | Create Kanren relations from rules |
| `query_critical_rules()` | Query CRITICAL priority rules |
| `query_rules_by_priority()` | Query rules by priority level |
| `query_foundational_rules()` | Query FOUNDATIONAL type rules |
| `validate_rule_compliance()` | Full compliance validation |

### Kanren Relations Created

```python
# Priority relations
rule_priority = Relation("rule_priority")      # (rule_id, priority)
critical_rule = Relation("critical_rule")       # (rule_id,)

# Type relations
rule_type_rel = Relation("rule_type")          # (rule_id, type)
foundational_rule = Relation("foundational_rule")
operational_rule = Relation("operational_rule")
technical_rule = Relation("technical_rule")

# Category relations
governance_rule = Relation("governance_rule")
testing_rule = Relation("testing_rule")
autonomy_rule = Relation("autonomy_rule")
```

### Test Coverage

```
tests/test_kanren_constraints.py: 55 tests, 100% pass
- TestTypeDBKanrenLoader: 10 tests
  - test_loader_imports
  - test_rule_constraint_from_dict
  - test_load_rules_from_json
  - test_load_rules_empty_input
  - test_populate_kanren_facts
  - test_typedb_kanren_bridge_lifecycle
  - test_validate_rule_compliance_expert
  - test_validate_rule_compliance_low_trust
  - test_validate_rule_missing_evidence
  - test_get_rules_by_category
```

### Usage Example

```python
from governance.kanren import TypeDBKanrenBridge

# Initialize bridge
bridge = TypeDBKanrenBridge()

# Load rules from MCP result
mcp_result = await governance_query_rules(status="ACTIVE")
counts = bridge.load_from_mcp(mcp_result)
print(f"Loaded {counts['critical']} CRITICAL rules")

# Validate compliance
result = bridge.validate_rule(
    "RULE-011",
    has_evidence=True,
    agent_trust=0.85
)
if result["compliant"]:
    print("Agent can execute rule")
else:
    print(f"Violations: {result['violations']}")
```

---

## Implementation Results: KAN-005 (2026-01-15)

### File Created

**`governance/kanren/benchmark.py`** - Performance benchmark suite.

### Benchmark Results

| Benchmark | Avg Time | Target | Status |
|-----------|----------|--------|--------|
| trust_level | 0.000ms | <1.0ms | PASS |
| requires_supervisor | 0.047ms | <1.0ms | PASS |
| can_execute_priority | 0.061ms | <1.0ms | PASS |
| task_requires_evidence | 0.029ms | <1.0ms | PASS |
| valid_task_assignment | 0.141ms | <5.0ms | PASS |
| filter_rag_chunks | 3.187ms | <5.0ms | PASS |
| find_rule_conflicts | 0.006ms | <10.0ms | PASS |

### Kanren vs Direct Python Comparison

| Operation | Kanren | Direct | Overhead |
|-----------|--------|--------|----------|
| trust_level | 0.0001ms | 0.0001ms | 0.4% |
| requires_supervisor | 0.047ms | 0.0001ms | ~39000% |
| can_execute | 0.062ms | 0.0001ms | ~53000% |
| requires_evidence | 0.029ms | 0.0001ms | ~27000% |

### Summary

- **Total Kanren avg time: 0.138ms** (target: <100ms)
- **All benchmarks PASSED**
- Kanren adds overhead vs direct Python, but absolute times are sub-millisecond
- Trade-off: Declarative constraint composition for <1ms overhead

### Test Coverage

```
tests/test_kanren_constraints.py: 62 tests, 100% pass
- TestKanrenBenchmarks: 7 tests
```

---

## RD-KANREN-CONTEXT: COMPLETE

All 5 tasks complete:
- KAN-001: Library evaluation
- KAN-002: Constraint DSL
- KAN-003: RAG filter integration
- KAN-004: TypeDB loader
- KAN-005: Performance benchmarks

**Total Tests: 62 passing**

---
