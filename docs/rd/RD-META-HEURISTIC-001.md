# RD-META-HEURISTIC-001: Session Pattern Analysis Agent

**Phase:** R&D | **Priority:** MEDIUM | **Status:** DESIGN
**Created:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT

---

## Overview

A "sleep mode" agent that analyzes Claude Code session transcripts to identify:
1. **Recurring command failures** - Commands that frequently fail on first attempt
2. **Discovery patterns** - Knowledge discovered repeatedly across sessions
3. **Fixture opportunities** - Static information that could be pre-loaded

## Problem Statement

During sessions, Claude Code often:
- Tries commands that fail (wrong container name, missing CLI tools)
- Rediscovers the same information (TypeDB version, Python version in containers)
- Wastes tokens on trial-and-error that could be avoided

### Examples from Today's Session

| Failed Attempt | Working Solution | Fixture Opportunity |
|----------------|------------------|---------------------|
| `podman exec typedb typedb --version` | `podman logs platform_typedb_1 \| grep version` | Container naming pattern |
| `pip download --python-version 3.13` | `pip list --outdated` in container | Python compatibility matrix |
| `podman exec platform_typedb_1 typedb` | Use dashboard container for Python | Service capability map |

---

## Proposed Solution

### Agent Architecture

```
┌─────────────────────────────────────────────────────┐
│              Sleep Mode Agent                        │
│  (Runs during idle time or scheduled)               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Session Scanner                                 │
│     - Read ~/.claude/projects/*/transcripts        │
│     - Extract command→result pairs                 │
│     - Identify failure patterns                    │
│                                                     │
│  2. Pattern Analyzer                                │
│     - Group similar failures                       │
│     - Calculate frequency/severity                 │
│     - Identify solutions that worked               │
│                                                     │
│  3. Fixture Generator                               │
│     - Create reusable snippets                     │
│     - Update CLAUDE.md sections                    │
│     - Generate rules if pattern is strong          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Output Artifacts

1. **Fixtures File**: `.claude/fixtures/container-patterns.md`
   ```markdown
   ## Container Name Patterns
   - TypeDB: platform_typedb_1
   - ChromaDB: platform_chromadb_1
   - Dashboard: platform_governance-dashboard-dev_1

   ## Service Capabilities
   - TypeDB container: No CLI, use logs for version
   - Dashboard container: Python 3.12 + typedb-driver
   ```

2. **Anti-Pattern Catalog**: `docs/gaps/evidence/ANTI-PATTERNS.md`
   ```markdown
   ## Known Anti-Patterns
   | Pattern | Frequency | Solution |
   |---------|-----------|----------|
   | `typedb --version` in container | 5x | Use container logs |
   | Wrong container name | 8x | Use `platform_{service}_1` |
   ```

3. **Rule Proposals**: Auto-generate draft rules for strong patterns

---

## Implementation Phases

### Phase 1: Manual Analysis (CURRENT)
- Document patterns manually as they occur
- Create CONTAINER-TYPEDB-01-v1 rule (DONE)
- Build fixture library incrementally

### Phase 2: Session Scanner
- Script to parse session transcripts
- Extract Bash tool calls and results
- Identify error patterns

### Phase 3: Pattern Analyzer
- Group similar errors
- Calculate pattern strength
- Prioritize fixture opportunities

### Phase 4: Auto-Generation
- Generate fixture files
- Propose rule updates
- Update CLAUDE.md automatically

---

## Success Metrics

| Metric | Target |
|--------|--------|
| First-attempt command success rate | >80% (vs ~60% now) |
| Tokens wasted on rediscovery | <10% reduction |
| New fixtures generated per quarter | 5-10 |
| Rules created from patterns | 2-3 per quarter |

---

## Dependencies

- Session transcript access (`.jsonl` files)
- Pattern matching library (regex or NLP)
- Rule creation API (gov-core MCP)

---

## Related

- CONTAINER-TYPEDB-01-v1: First rule from manual pattern analysis
- RULE-PKG-LATEST-01-v1: Another pattern-derived rule
- GAP-MCP-PAGING-001: Example of recurring issue to fixture

---

*Per WORKFLOW-RD-01-v1: R&D requires explicit human approval before implementation*
