# DECISION-003: TypeDB-First Storage Strategy

**Date**: 2024-12-24
**Status**: PROPOSED
**Author**: AI Assistant + User
**Context**: Phase 6 Strategic Architecture Review

## Summary

Adopt TypeDB as the primary storage layer for all new data, leveraging TypeDB 3.x vector search capabilities. ChromaDB remains read-only for legacy claude-mem data until migration.

## Problem Statement

Current architecture uses two separate databases:
- **ChromaDB**: Vector store for semantic search (inherited from claude-mem)
- **TypeDB**: Logical inference for rule dependencies

This creates:
1. Data fragmentation across systems
2. Query routing complexity
3. Two systems to maintain and monitor
4. Inability to combine semantic + logical queries in single transaction

## Decision

**TypeDB-First for all new data.**

### Architecture Evolution

```
PHASE 1: NOW (Hybrid)                    PHASE 2: MIGRATION
┌────────────────────────────────┐       ┌────────────────────────────────┐
│         Query Router           │       │         Query Router           │
├────────────────────────────────┤       ├────────────────────────────────┤
│  TypeDB    │    ChromaDB       │  ───► │         TypeDB 3.x             │
│  (logic)   │    (vectors)      │       │  (logic + vectors unified)     │
└────────────────────────────────┘       └────────────────────────────────┘
```

### TypeDB 3.x Capabilities

| Feature | TypeDB 2.x | TypeDB 3.x | ChromaDB |
|---------|------------|------------|----------|
| Logical inference | ✓ | ✓ | ✗ |
| Schema enforcement | ✓ | ✓ | ✗ |
| Vector embeddings | ✗ | ✓ | ✓ |
| Similarity search | ✗ | ✓ (near) | ✓ |
| ACID transactions | ✓ | ✓ | Limited |
| Rule reasoning | ✓ | ✓ | ✗ |

### TypeDB 3.x Vector Example

```typeql
define
  document sub entity,
    owns content,
    owns embedding,
    owns created-at;

  embedding sub attribute, value double[];
  content sub attribute, value string;

insert
  $doc isa document,
    has content "Authentication module handles OAuth2",
    has embedding [0.12, 0.45, 0.78, ...];

match
  $doc isa document, has embedding $emb, has content $c;
  ($doc) near ($emb, $query_vector) with distance < 0.3;
fetch $doc: content;
```

## Implementation Plan

### Phase 2a: TypeDB Vector Schema (Week 1)

1. Add vector embedding schema to TypeDB
2. Create embedding generation pipeline
3. Test vector similarity queries

### Phase 2b: New Data to TypeDB (Week 2)

1. All new agent memories → TypeDB
2. All governance proposals → TypeDB
3. Task execution logs → TypeDB

### Phase 2c: Migration Tool (Week 3+)

1. Export ChromaDB collections
2. Generate embeddings (same model)
3. Import to TypeDB with schema mapping
4. Verify query parity

### Phase 2d: ChromaDB Sunset

1. Make ChromaDB read-only
2. Update query router to TypeDB-only
3. Decommission ChromaDB container

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| TypeDB 3.x vector stability | Gradual rollout, keep ChromaDB fallback |
| Embedding model mismatch | Document model version, re-embed if needed |
| Performance regression | Benchmark before migration |
| Query syntax changes | Abstract behind query service layer |

## Alternatives Considered

### A: Keep Hybrid Forever
- **Pros**: No migration effort
- **Cons**: Perpetual complexity, two systems to maintain

### B: Migrate to ChromaDB Only
- **Pros**: Simple vector store
- **Cons**: Lose logical inference capabilities

### C: Use PostgreSQL with pgvector
- **Pros**: Mature, widely supported
- **Cons**: No native reasoning/inference

## Success Metrics

| Metric | Target |
|--------|--------|
| Query latency (p95) | < 200ms |
| Storage containers | 1 (down from 2) |
| Query routing logic | Eliminated |
| Combined semantic+logical queries | Possible |

## Decision Rationale

TypeDB 3.x unifies our needs:
1. **Semantic search**: Native vector embeddings
2. **Logical inference**: Rule dependencies, conflict detection
3. **Schema**: Enforced data quality
4. **Single source of truth**: No data fragmentation

The "TypeDB beast" becomes the brain for:
- Agent memories
- Governance rules
- Task history
- Knowledge base

---

**Approved by**: Pending
**Implementation start**: Post-Phase 6
**Target completion**: Phase 7
